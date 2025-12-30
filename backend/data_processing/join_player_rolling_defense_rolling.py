# backend/data_processing/join_player_rolling_defense_rolling.py
import pandas as pd
from pathlib import Path

PLAYER_PATH = Path("data/processed/player_points_features.csv")
DEF_PATH = Path("data/processed/team_defense_rolling.csv")
RAW_PLAYER_PATH = Path("data/raw/player_game_logs.csv")
OUT_PATH = Path("data/processed/model_dataset.csv")

players = pd.read_csv(PLAYER_PATH, parse_dates=["GAME_DATE"])
teams = pd.read_csv(DEF_PATH, parse_dates=["GAME_DATE"])
raw_players = pd.read_csv(RAW_PLAYER_PATH, parse_dates=["GAME_DATE"])

# Team mapping
TEAM_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "LA Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}

# Extract opponent
def extract_opponent(matchup: str) -> str:
    if "vs." in matchup:
        return matchup.split("vs.")[-1].strip()
    if "@" in matchup:
        return matchup.split("@")[-1].strip()
    return None

players["OPP_ABBR"] = players["MATCHUP"].apply(extract_opponent)
players["OPP_TEAM_NAME"] = players["OPP_ABBR"].map(TEAM_ABBR_TO_NAME)

# Drop unmapped games
players = players.dropna(subset=["OPP_TEAM_NAME"])

# Check if POSITION column already exists (it should from build_player_features.py)
if 'POSITION' in players.columns:
    print(f"\nPOSITION column already in dataset: {players['POSITION'].notna().sum():,} players have positions")
else:
    print("\nWarning: POSITION column missing from player_points_features.csv")

# ===============================
# BUILD POSITIONAL DEFENSE FEATURES
# ===============================
print("\nBuilding positional defense features...")

# Get opponent team and position from raw player logs
raw_players["OPP_ABBR"] = raw_players["MATCHUP"].apply(extract_opponent)
raw_players["OPP_TEAM_NAME"] = raw_players["OPP_ABBR"].map(TEAM_ABBR_TO_NAME)
raw_players = raw_players.dropna(subset=["OPP_TEAM_NAME", "POSITION"])

# Aggregate points by opponent team, game date, and position
pos_defense = raw_players.groupby(['OPP_TEAM_NAME', 'GAME_DATE', 'POSITION']).agg({
    'PTS': 'sum'  # Total points allowed to this position
}).reset_index()

pos_defense.rename(columns={'PTS': 'PTS_ALLOWED_TO_POS'}, inplace=True)

# Sort for rolling calculations
pos_defense = pos_defense.sort_values(['OPP_TEAM_NAME', 'POSITION', 'GAME_DATE'])

# Calculate rolling averages by team and position
grouped_pos = pos_defense.groupby(['OPP_TEAM_NAME', 'POSITION'], group_keys=False)

pos_defense['DEF_PTS_VS_POS_L5'] = (
    grouped_pos['PTS_ALLOWED_TO_POS']
    .shift(1)
    .rolling(5, min_periods=1)
    .mean()
)

pos_defense['DEF_PTS_VS_POS_L10'] = (
    grouped_pos['PTS_ALLOWED_TO_POS']
    .shift(1)
    .rolling(10, min_periods=1)
    .mean()
)

# Pivot to wide format for easier joining
pos_defense_wide = pos_defense.pivot_table(
    index=['OPP_TEAM_NAME', 'GAME_DATE'],
    columns='POSITION',
    values=['DEF_PTS_VS_POS_L5', 'DEF_PTS_VS_POS_L10']
).reset_index()

# Flatten column names
pos_defense_wide.columns = [
    f"{col[0]}_{col[1]}" if col[1] else col[0]
    for col in pos_defense_wide.columns
]

# Rename for clarity
pos_defense_wide.rename(columns={
    'DEF_PTS_VS_POS_L5_Guard': 'DEF_PTS_VS_GUARD_L5',
    'DEF_PTS_VS_POS_L5_Forward': 'DEF_PTS_VS_FORWARD_L5',
    'DEF_PTS_VS_POS_L5_Center': 'DEF_PTS_VS_CENTER_L5',
    'DEF_PTS_VS_POS_L10_Guard': 'DEF_PTS_VS_GUARD_L10',
    'DEF_PTS_VS_POS_L10_Forward': 'DEF_PTS_VS_FORWARD_L10',
    'DEF_PTS_VS_POS_L10_Center': 'DEF_PTS_VS_CENTER_L10',
}, inplace=True)

print(f"  Positional defense rows: {len(pos_defense_wide):,}")

# Normalize team names
teams["TEAM_NAME"] = teams["TEAM_NAME"].str.strip()

DEF_COLS = [
    "DEF_PTS_ALLOWED_L5",
    "DEF_3PT_ALLOWED_L5",
    "DEF_3PT_PCT_L5",
    "TEAM_PACE_L5",
    "TEAM_PACE_L10",
]

POS_DEF_COLS = [
    'DEF_PTS_VS_GUARD_L5',
    'DEF_PTS_VS_FORWARD_L5',
    'DEF_PTS_VS_CENTER_L5',
    'DEF_PTS_VS_GUARD_L10',
    'DEF_PTS_VS_FORWARD_L10',
    'DEF_PTS_VS_CENTER_L10',
]

# Per-team asof merge (CORRECT APPROACH)
merged_chunks = []

for team in players["OPP_TEAM_NAME"].unique():
    p = players[players["OPP_TEAM_NAME"] == team].copy()
    t = teams[teams["TEAM_NAME"] == team].copy()
    pd_def = pos_defense_wide[pos_defense_wide["OPP_TEAM_NAME"] == team].copy()

    if t.empty:
        print(f"⚠️  No defense data for {team}")
        continue

    p = p.sort_values("GAME_DATE")
    t = t.sort_values("GAME_DATE")
    pd_def = pd_def.sort_values("GAME_DATE")

    # Merge team defense
    merged = pd.merge_asof(
        p,
        t[["GAME_DATE"] + DEF_COLS],
        on="GAME_DATE",
        direction="backward",
    )

    # Merge positional defense
    if not pd_def.empty:
        merged = pd.merge_asof(
            merged,
            pd_def[["GAME_DATE"] + POS_DEF_COLS],
            on="GAME_DATE",
            direction="backward",
        )

    merged_chunks.append(merged)

final_df = pd.concat(merged_chunks, ignore_index=True)

# ===============================
# CREATE POSITION-SPECIFIC DEFENSE FEATURE
# ===============================
print("\nCreating position-specific defense features...")

# Map each player to their correct positional defense stat
def get_positional_defense_l5(row):
    """Get the L5 defense stat for the player's position"""
    if pd.isna(row['POSITION']):
        return None

    if row['POSITION'] == 'Guard':
        return row.get('DEF_PTS_VS_GUARD_L5')
    elif row['POSITION'] == 'Forward':
        return row.get('DEF_PTS_VS_FORWARD_L5')
    elif row['POSITION'] == 'Center':
        return row.get('DEF_PTS_VS_CENTER_L5')
    else:
        return None

def get_positional_defense_l10(row):
    """Get the L10 defense stat for the player's position"""
    if pd.isna(row['POSITION']):
        return None

    if row['POSITION'] == 'Guard':
        return row.get('DEF_PTS_VS_GUARD_L10')
    elif row['POSITION'] == 'Forward':
        return row.get('DEF_PTS_VS_FORWARD_L10')
    elif row['POSITION'] == 'Center':
        return row.get('DEF_PTS_VS_CENTER_L10')
    else:
        return None

# Apply the mapping
final_df['DEF_PTS_VS_POSITION_L5'] = final_df.apply(get_positional_defense_l5, axis=1)
final_df['DEF_PTS_VS_POSITION_L10'] = final_df.apply(get_positional_defense_l10, axis=1)

print(f"  Rows with position-specific defense: {final_df['DEF_PTS_VS_POSITION_L5'].notna().sum():,}")

# ===============================
# ADD OPPONENT PACE
# ===============================
print("\nAdding opponent pace features...")

# The TEAM_PACE columns we just added are for the OPPONENT team
# (because we merged opponent defensive stats)
# Rename them to make it clear these are opponent pace stats
final_df.rename(columns={
    'TEAM_PACE_L5': 'OPP_PACE_L5',
    'TEAM_PACE_L10': 'OPP_PACE_L10',
}, inplace=True)

# ===============================
# ADD PLAYER'S OWN TEAM PACE
# ===============================
print("\nAdding player's team pace...")

# Map player's team abbreviation to full name
final_df['PLAYER_TEAM_NAME'] = final_df['TEAM_ABBREVIATION'].map(TEAM_ABBR_TO_NAME)

# Merge player's own team pace
player_team_pace_chunks = []
for team in final_df['PLAYER_TEAM_NAME'].unique():
    if pd.isna(team):
        continue

    p = final_df[final_df['PLAYER_TEAM_NAME'] == team].copy()
    t = teams[teams['TEAM_NAME'] == team].copy()

    if t.empty:
        print(f"  ⚠️  No pace data for {team}")
        player_team_pace_chunks.append(p)
        continue

    p = p.sort_values("GAME_DATE")
    t = t.sort_values("GAME_DATE")

    # Merge player's team pace
    merged = pd.merge_asof(
        p,
        t[["GAME_DATE", "TEAM_PACE_L5", "TEAM_PACE_L10"]],
        on="GAME_DATE",
        direction="backward",
        suffixes=('', '_PLAYER_TEAM')
    )

    player_team_pace_chunks.append(merged)

final_df = pd.concat(player_team_pace_chunks, ignore_index=True)

# Rename to make it clear these are the player's team pace
final_df.rename(columns={
    'TEAM_PACE_L5': 'PLAYER_TEAM_PACE_L5',
    'TEAM_PACE_L10': 'PLAYER_TEAM_PACE_L10',
}, inplace=True)

print(f"  Rows with player team pace: {final_df['PLAYER_TEAM_PACE_L5'].notna().sum():,}")

# ===============================
# CALCULATE EXPECTED POSSESSIONS
# ===============================
print("Calculating expected possessions...")

# Expected game pace = average of player's team pace and opponent's pace
# This accounts for both teams' playing styles
final_df['EXPECTED_GAME_PACE_L5'] = (final_df['PLAYER_TEAM_PACE_L5'] + final_df['OPP_PACE_L5']) / 2.0
final_df['EXPECTED_GAME_PACE_L10'] = (final_df['PLAYER_TEAM_PACE_L10'] + final_df['OPP_PACE_L10']) / 2.0

# Expected possessions = (player's minutes / 48) * expected game pace
final_df['EXPECTED_POSSESSIONS_L5'] = (final_df['MIN_L5'] / 48.0) * final_df['EXPECTED_GAME_PACE_L5']
final_df['EXPECTED_POSSESSIONS_L10'] = (final_df['MIN_L10'] / 48.0) * final_df['EXPECTED_GAME_PACE_L10']

print(f"  Rows with expected possessions: {final_df['EXPECTED_POSSESSIONS_L5'].notna().sum():,}")

# Sort final dataset
final_df = final_df.sort_values("GAME_DATE").reset_index(drop=True)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
final_df.to_csv(OUT_PATH, index=False)

print("\n Model dataset created!")
print(f" Saved to: {OUT_PATH}")
print(f" Rows: {len(final_df):,}")
print(f" Date range: {final_df['GAME_DATE'].min()} to {final_df['GAME_DATE'].max()}")
print(f" Players: {final_df['PLAYER_NAME'].nunique():,}")