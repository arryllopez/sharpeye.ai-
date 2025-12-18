import pandas as pd
from pathlib import Path

PLAYER_PATH = Path("data/processed/player_points_features.csv")
DEF_PATH = Path("data/processed/team_defense_rolling.csv")
OUT_PATH = Path("data/processed/model_dataset.csv")

players = pd.read_csv(PLAYER_PATH, parse_dates=["GAME_DATE"])
teams = pd.read_csv(DEF_PATH, parse_dates=["GAME_DATE"])

# --------------------------------------------------
# Local team mapping (minimal, expandable)
# --------------------------------------------------
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

# -------------------------
# Extract opponent abbrev
# -------------------------
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

# Normalize defense team names
teams["TEAM_NAME"] = teams["TEAM_NAME"].str.strip()

DEF_COLS = [
    "DEF_PTS_ALLOWED_L5",
    "DEF_3PT_ALLOWED_L5",
    "DEF_3PT_PCT_L5",
]

# -------------------------
# SAFE per-team asof merge
# -------------------------
merged_chunks = []

for team in players["OPP_TEAM_NAME"].unique():
    p = players[players["OPP_TEAM_NAME"] == team].copy()
    t = teams[teams["TEAM_NAME"] == team].copy()

    if t.empty:
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

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
final_df.to_csv(OUT_PATH, index=False)

print("[OK] Model dataset created:", OUT_PATH)
print("Rows:", len(final_df))
