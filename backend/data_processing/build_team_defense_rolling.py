from pathlib import Path
import pandas as pd

# ===============================
# PATHS
# ===============================
RAW_PATH = Path("data/raw/team_defensive_game_logs.csv")
OUT_PATH = Path("data/processed/team_defense_rolling.csv")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ===============================
# LOAD DATA
# ===============================
df = pd.read_csv(RAW_PATH, parse_dates=["GAME_DATE"])

# ===============================
# SORT (CRITICAL)
# ===============================
df = df.sort_values(["TEAM_NAME", "GAME_DATE"]).reset_index(drop=True)

# ===============================
# GROUP BY TEAM
# ===============================
grouped = df.groupby("TEAM_NAME", group_keys=False)

# ===============================
# ROLLING DEFENSIVE FEATURES
# ===============================
df["DEF_PTS_ALLOWED_L5"] = (
    grouped["PTS_ALLOWED"]
    .shift(1)
    .rolling(5)
    .mean()
)


df["DEF_3PT_ALLOWED_L5"] = (
    grouped["FG3_ALLOWED"]
    .shift(1)
    .rolling(5)
    .mean()
)

df["DEF_3PT_PCT_L5"] = (
    grouped["OPP_FG3_PCT"]
    .shift(1)
    .rolling(5)
    .mean()
)

df["DEF_PTS_ALLOWED_STD_L10"] = (
    grouped["PTS_ALLOWED"]
    .shift(1)
    .rolling(10)
    .std()
)

# ===============================
# PACE FEATURES
# ===============================
# Game pace = average possessions per game (average of both teams)
# Rolling average gives us each team's typical pace

df["TEAM_PACE_L5"] = (
    grouped["GAME_PACE"]
    .shift(1)
    .rolling(5)
    .mean()
)

df["TEAM_PACE_L10"] = (
    grouped["GAME_PACE"]
    .shift(1)
    .rolling(10)
    .mean()
)


# ===============================
# SAVE OUTPUT
# ===============================
out_cols = [
    "GAME_ID",
    "GAME_DATE",
    "SEASON",
    "TEAM_NAME",
    "OPPONENT",
    "DEF_PTS_ALLOWED_L5",
    "DEF_3PT_ALLOWED_L5",
    "DEF_3PT_PCT_L5",
    "DEF_PTS_ALLOWED_STD_L10",
    "TEAM_PACE_L5",
    "TEAM_PACE_L10",
]

df[out_cols].to_csv(OUT_PATH, index=False)

print(f"[OK] Team defense rolling features written to {OUT_PATH}")
