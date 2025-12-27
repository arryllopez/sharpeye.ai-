# backend/data_processing/join_player_rolling_defense_rolling.py
import pandas as pd
from pathlib import Path

PLAYER_PATH = Path("data/processed/player_points_features.csv")
DEF_PATH = Path("data/processed/team_defense_rolling.csv")
OUT_PATH = Path("data/processed/model_dataset.csv")

players = pd.read_csv(PLAYER_PATH, parse_dates=["GAME_DATE"])
teams = pd.read_csv(DEF_PATH, parse_dates=["GAME_DATE"])

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

# Normalize team names
teams["TEAM_NAME"] = teams["TEAM_NAME"].str.strip()

DEF_COLS = [
    "DEF_PTS_ALLOWED_L5",
    "DEF_3PT_ALLOWED_L5",
    "DEF_3PT_PCT_L5",
]

# Per-team asof merge (CORRECT APPROACH)
merged_chunks = []

for team in players["OPP_TEAM_NAME"].unique():
    p = players[players["OPP_TEAM_NAME"] == team].copy()
    t = teams[teams["TEAM_NAME"] == team].copy()

    if t.empty:
        print(f"⚠️  No defense data for {team}")
        continue

    p = p.sort_values("GAME_DATE")
    t = t.sort_values("GAME_DATE")

    merged = pd.merge_asof(
        p,
        t[["GAME_DATE"] + DEF_COLS],
        on="GAME_DATE",
        direction="backward",
    )

    merged_chunks.append(merged)

final_df = pd.concat(merged_chunks, ignore_index=True)

# Sort final dataset
final_df = final_df.sort_values("GAME_DATE").reset_index(drop=True)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
final_df.to_csv(OUT_PATH, index=False)

print("\n Model dataset created!")
print(f" Saved to: {OUT_PATH}")
print(f" Rows: {len(final_df):,}")
print(f" Date range: {final_df['GAME_DATE'].min()} to {final_df['GAME_DATE'].max()}")
print(f" Players: {final_df['PLAYER_NAME'].nunique():,}")