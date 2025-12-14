import os
import pandas as pd

# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

PLAYER_PATH = os.path.join(RAW_DIR, "player_game_logs.csv")
TEAM_DEF_PATH = os.path.join(RAW_DIR, "team_defensive_game_logs.csv")
OUTPUT_PATH = os.path.join(
    PROCESSED_DIR,
    "player_points_with_opponent_defense.csv"
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
players = pd.read_csv(PLAYER_PATH)
teams = pd.read_csv(TEAM_DEF_PATH)

players["GAME_DATE"] = pd.to_datetime(players["GAME_DATE"])
teams["GAME_DATE"] = pd.to_datetime(teams["GAME_DATE"])

# -------------------------------------------------
# EXTRACT OPPONENT ABBREVIATION FROM MATCHUP
# Examples:
# "LAL vs SAS" → SAS
# "LAL @ SAS"  → SAS
# -------------------------------------------------
players["OPP_ABBR"] = players["MATCHUP"].apply(
    lambda x: x.split(" ")[-1]
)

# -------------------------------------------------
# MAP TEAM NAME → TEAM ABBREVIATION
# -------------------------------------------------
TEAM_ABBR_MAP = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

teams["TEAM_ABBR"] = teams["TEAM_NAME"].map(TEAM_ABBR_MAP)





# -------------------------------------------------
# SORT TEAM DEFENSE FOR ROLLING FEATURES
# -------------------------------------------------
teams = teams.sort_values(["TEAM_ABBR", "GAME_DATE"])

# -------------------------------------------------
# ROLLING DEFENSIVE METRICS (PRE-GAME)
# -------------------------------------------------
teams["DEF_PTS_ALLOWED_L5"] = (
    teams.groupby("TEAM_ABBR")["PTS_ALLOWED"]
    .shift(1)
    .rolling(5)
    .mean()
)

teams["DEF_3PT_ALLOWED_L5"] = (
    teams.groupby("TEAM_ABBR")["FG3_ALLOWED"]
    .shift(1)
    .rolling(5)
    .mean()
)

teams["DEF_3PT_PCT_L5"] = (
    teams.groupby("TEAM_ABBR")["OPP_FG3_PCT"]
    .shift(1)
    .rolling(5)
    .mean()
)

# -------------------------------------------------
# JOIN PLAYER → OPPONENT DEFENSE
# -------------------------------------------------
merged = players.merge(
    teams[
        [
            "GAME_DATE",
            "TEAM_ABBR",
            "DEF_PTS_ALLOWED_L5",
            "DEF_3PT_ALLOWED_L5",
            "DEF_3PT_PCT_L5",
        ]
    ],
    left_on=["GAME_DATE", "OPP_ABBR"],
    right_on=["GAME_DATE", "TEAM_ABBR"],
    how="left",
)

merged.drop(columns=["TEAM_ABBR"], inplace=True)

# -------------------------------------------------
# SAVE OUTPUT
# -------------------------------------------------
merged.to_csv(OUTPUT_PATH, index=False)

print("✅ Join complete")
print(f"Rows written: {len(merged)}")
print(f"Saved to: {OUTPUT_PATH}")
