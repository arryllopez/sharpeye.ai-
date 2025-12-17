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
    .rolling(window=5, min_periods=5, closed="left")
    .mean()
    .reset_index(level=0, drop=True)
)

df["DEF_3PT_ALLOWED_L5"] = (
    grouped["FG3_ALLOWED"]
    .rolling(window=5, min_periods=5, closed="left")
    .mean()
    .reset_index(level=0, drop=True)
)

df["DEF_3PT_PCT_L5"] = (
    grouped["OPP_FG3_PCT"]
    .rolling(window=5, min_periods=5, closed="left")
    .mean()
    .reset_index(level=0, drop=True)
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
]

df[out_cols].to_csv(OUT_PATH, index=False)

print(f"[OK] Team defense rolling features written → {OUT_PATH}")
