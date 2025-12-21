import pandas as pd
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
RAW_PATH = Path("data/raw/player_game_logs.csv")
OUTPUT_PATH = Path("data/processed/player_points_features.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv(RAW_PATH)

# -----------------------------
# Basic cleanup
# -----------------------------
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

df = df.sort_values(["PLAYER_ID", "GAME_DATE"])

# -----------------------------
# Rolling features (SHIFTED)
# -----------------------------
group = df.groupby("PLAYER_ID", group_keys=False)

df["PTS_L5"] = group["PTS"].shift(1).rolling(5).mean()
df["PTS_L10"] = group["PTS"].shift(1).rolling(10).mean()
df["MIN_L5"] = group["MIN"].shift(1).rolling(5).mean()
#addding these features for potential future use
df["REB_L5"] = group["REB"].shift(1).rolling(5).mean()
df["AST_L5"] = group["AST"].shift(1).rolling(5).mean()
df["FG3M_L5"] = group["FG3M"].shift(1).rolling(5).mean()

# Optional expansion later:
# df["FG3A_L5"] = group["FG3A"].shift(1).rolling(5).mean()

# -----------------------------
# Drop rows without enough history
# -----------------------------
df = df.dropna(subset=["PTS_L5", "PTS_L10", "MIN_L5", "REB_L5", "AST_L5", "FG3M_L5"])

# -----------------------------
# Save
# -----------------------------
df.to_csv(OUTPUT_PATH, index=False)

print(f"Saved player features to {OUTPUT_PATH}")
