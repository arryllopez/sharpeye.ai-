import pandas as pd
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
BACKEND_DIR = Path(__file__).parent.parent
RAW_PATH = Path("data/raw/player_game_logs.csv")
OUTPUT_PATH = Path("data/processed/player_points_features.csv")
ADVANCED_PATH = BACKEND_DIR / "data/raw/player_advanced_stats.csv"
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

#scoring features
df["PTS_L5"] = group["PTS"].shift(1).rolling(5).mean()
df["PTS_L10"] = group["PTS"].shift(1).rolling(10).mean()
#minutes played feature
df["MIN_L5"] = group["MIN"].shift(1).rolling(5).mean()
#addding these features for potential future use
df["REB_L5"] = group["REB"].shift(1).rolling(5).mean()
df["AST_L5"] = group["AST"].shift(1).rolling(5).mean()
df["FG3M_L5"] = group["FG3M"].shift(1).rolling(5).mean()
#usage 
df["USAGE_VOLUME"] = df["FGA"] + 0.44 * df["FTA"] + df["TOV"]

if ADVANCED_PATH.exists():
    print("[INFO] Using real usage rate from advanced stats")
    advanced_df = pd.read_csv(ADVANCED_PATH)
    
    # Merge season-level stats
    df = df.merge(
        advanced_df[["PLAYER_ID", "SEASON", "USG_PCT", "PACE", "TS_PCT"]],
        on=["PLAYER_ID", "SEASON"],
        how="left"
    )
    #after this, it attaches a season usage percentage a season ts % to each game row for that player in that season
    
    # Still calculate game-level usage for rolling average

    df["USAGE_VOLUME_L5"] = group["USAGE_VOLUME"].shift(1).rolling(5).mean()

    print(f"  - Real USG_PCT available for {df['USG_PCT'].notna().sum():,} rows")
else:
    print("[WARN] No advanced stats found, using approximation")

# calculate game-level True Shooting %
denom = 2 * (df["FGA"] + 0.44 * df["FTA"])
df["TS_GAME"] = df["PTS"] / denom.replace(0, pd.NA)

# \rolling True Shooting %
df["TS_PCT_L5"] = group["TS_GAME"].shift(1).rolling(5).mean()
df["TS_PCT_L10"] = group["TS_GAME"].shift(1).rolling(10).mean()

#shooting volume
df["FGA_L5"] = group["FGA"].shift(1).rolling(5).mean()
df["FG3A_L5"] = group["FG3A"].shift(1).rolling(5).mean()
#points per minute
df["PTS_PER_MIN_L5"] = (
    group["PTS"].shift(1).rolling(5).mean() /
    group["MIN"].shift(1).rolling(5).mean().replace(0, pd.NA) #addressing division by 0
)
#volatlity
df["PTS_STD_L10"] = (
    group["PTS"]
    .shift(1)
    .rolling(10)
    .std()
)
#rest context
df = df.sort_values(["PLAYER_ID", "GAME_DATE"]) # ensure sorted by date
df["DAYS_REST"] = df.groupby("PLAYER_ID")["GAME_DATE"].diff().dt.days # days since last game
df["IS_BACK_TO_BACK"] = (df["DAYS_REST"] == 1).astype(int) #back to back games register as 1 day rest jan 23-jan22 = 1 day rest

#adding optional recent form since many redditors suggested it. 
df["PTS_L3"] = group["PTS"].shift(1).rolling(3).mean()
 



# expand using same format for more features
# modify ingestion -- > then processsing --> then training to reflect changes
# df["FG3A_L5"] = group["FG3A"].shift(1).rolling(5).mean()

# -----------------------------
# Drop rows without enough history
# -----------------------------
df = df.dropna(subset=[
    "PTS_L5",
    "PTS_L10",
    "MIN_L5",
    "REB_L5",
    "AST_L5",
    "FG3M_L5", #also recent form
    "USAGE_VOLUME_L5",
    "FGA_L5",
    "FG3A_L5",
    "PTS_PER_MIN_L5",
    "PTS_STD_L10",
    #newly added features
    #recent form
    "PTS_L3",
    #rest context
    "DAYS_REST",
    "IS_BACK_TO_BACK",
    #advanced stats
    "TS_PCT_L5",
    "TS_PCT_L10",
])


# -----------------------------
# Save
# -----------------------------
df.to_csv(OUTPUT_PATH, index=False)

print(f"Saved player features to {OUTPUT_PATH}")
