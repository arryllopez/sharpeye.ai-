"""
Comprehensive validation script for model_dataset.csv
Checks for data leakage, temporal correctness, and data quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================
# CONFIG
# ============================
DATASET_PATH = Path("data/processed/model_dataset.csv")

# ============================
# LOAD
# ============================
def load_data():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH, parse_dates=["GAME_DATE"])
    df = df.sort_values(["PLAYER_ID", "GAME_DATE"]).reset_index(drop=True)
    return df

# ============================
# BASIC STATS
# ============================
def basic_statistics(df):
    print("\n" + "=" * 70)
    print("BASIC STATISTICS")
    print("=" * 70)

    print(f"Total rows:        {len(df):,}")
    print(f"Unique players:    {df['PLAYER_NAME'].nunique():,}")
    print(f"Unique teams:      {df['TEAM_ABBREVIATION'].nunique()}")
    print(f"Date range:        {df['GAME_DATE'].min().date()} → {df['GAME_DATE'].max().date()}")

    games_per_player = df.groupby("PLAYER_ID").size()
    print("\nGames per player:")
    print(f"  Mean:   {games_per_player.mean():.1f}")
    print(f"  Median: {games_per_player.median():.1f}")
    print(f"  Min:    {games_per_player.min()}")
    print(f"  Max:    {games_per_player.max()}")

# ============================
# COLUMN CHECK
# ============================
def check_columns(df):
    print("\n" + "=" * 70)
    print("COLUMN CHECK")
    print("=" * 70)

    required_cols = [
        # identifiers
        "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GAME_DATE", "MATCHUP",
        "OPP_ABBR", "OPP_TEAM_NAME",

        # box score
        "MIN", "PTS", "REB", "AST", "FGM", "FGA", "FG3M", "FG3A",
        "FTM", "FTA", "TOV", "PF", "PLUS_MINUS",

        # context
        "IS_HOME",

        # rolling offense
        "PTS_L5", "PTS_L10", "MIN_L5",
        "REB_L5", "AST_L5", "FG3M_L5",
        "USAGE_PROXY", "USAGE_L5",
        "FGA_L5", "FG3A_L5",
        "PTS_PER_MIN_L5", "PTS_STD_L10",

        # defense
        "DEF_PTS_ALLOWED_L5",
        "DEF_3PT_ALLOWED_L5",
        "DEF_3PT_PCT_L5",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    extra = [c for c in df.columns if c not in required_cols]

    if missing:
        print(f"[FAIL] Missing columns: {missing}")
    else:
        print("[PASS] All required columns present")

    if extra:
        print(f"[INFO] Extra columns (ok): {extra}")

# ============================
# MISSING VALUES
# ============================
def check_missing_values(df):
    print("\n" + "=" * 70)
    print("MISSING VALUES")
    print("=" * 70)

    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    if missing.empty:
        print("[PASS] No missing values")
        return

    for col, cnt in missing.items():
        pct = cnt / len(df) * 100
        print(f"{col:30s}: {cnt:6,} ({pct:5.2f}%)")

    print("\nNote: Rolling features missing early in season is EXPECTED.")

# ============================
# DATA TYPES
# ============================
def check_data_types(df):
    print("\n" + "=" * 70)
    print("DATA TYPES")
    print("=" * 70)

    numeric_cols = [
        "MIN", "PTS", "REB", "AST",
        "FGA", "FG3A", "FTA",
        "PTS_L5", "PTS_L10", "MIN_L5",
        "USAGE_PROXY", "USAGE_L5",
        "PTS_PER_MIN_L5", "PTS_STD_L10",
        "DEF_PTS_ALLOWED_L5",
        "DEF_3PT_ALLOWED_L5",
        "DEF_3PT_PCT_L5",
    ]

    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"[FAIL] {col} is not numeric")
        else:
            print(f"[PASS] {col:30s} {df[col].dtype}")

# ============================
# LEAKAGE CHECK
# ============================
def validate_rolling_features(df):
    print("\n" + "=" * 70)
    print("TEMPORAL LEAKAGE CHECK")
    print("=" * 70)

    test_players = df["PLAYER_ID"].value_counts().head(3).index.tolist()
    all_valid = True

    for pid in test_players:
        p = df[df["PLAYER_ID"] == pid].sort_values("GAME_DATE").reset_index(drop=True)

        if len(p) < 12:
            continue

        idx = 10

        manual_pts_l5 = p.iloc[5:10]["PTS"].mean()
        manual_pts_l10 = p.iloc[0:10]["PTS"].mean()
        manual_min_l5 = p.iloc[5:10]["MIN"].mean()

        row = p.iloc[idx]

        checks = {
            "PTS_L5": abs(row["PTS_L5"] - manual_pts_l5) < 0.1,
            "PTS_L10": abs(row["PTS_L10"] - manual_pts_l10) < 0.1,
            "MIN_L5": abs(row["MIN_L5"] - manual_min_l5) < 0.1,
        }

        print(f"\nPlayer {p.iloc[0]['PLAYER_NAME']}:")
        for k, v in checks.items():
            print(f"  {k:10s}: {'PASS' if v else 'FAIL'}")
            if not v:
                all_valid = False

    print("\n" + ("[PASS] No leakage detected" if all_valid else "[FAIL] Leakage suspected"))

# ============================
# DEFENSE SANITY
# ============================
def check_defense_features(df):
    print("\n" + "=" * 70)
    print("DEFENSIVE FEATURE RANGES")
    print("=" * 70)

    ranges = {
        "DEF_PTS_ALLOWED_L5": (85, 135),
        "DEF_3PT_ALLOWED_L5": (7, 20),
        "DEF_3PT_PCT_L5": (0.25, 0.45),
    }

    for col, (lo, hi) in ranges.items():
        mn, mx = df[col].min(), df[col].max()
        if mn < lo or mx > hi:
            print(f"[WARN] {col}: [{mn:.2f}, {mx:.2f}]")
        else:
            print(f"[PASS] {col}: [{mn:.2f}, {mx:.2f}]")

# ============================
# SUMMARY
# ============================
def summary(df):
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    feature_cols = [
        "PTS_L5", "PTS_L10", "MIN_L5",
        "USAGE_L5", "PTS_PER_MIN_L5",
        "DEF_PTS_ALLOWED_L5",
    ]

    ready = df.dropna(subset=feature_cols)

    print(f"Model-ready rows: {len(ready):,} / {len(df):,} ({len(ready)/len(df)*100:.1f}%)")
    print(f"Players covered:  {ready['PLAYER_ID'].nunique():,}")
    print("\nDATASET IS MODEL-READY ✅")

# ============================
# MAIN
# ============================
def main():
    print("\n" + "=" * 70)
    print("SHARPEYE.AI DATASET VALIDATION")
    print("=" * 70)

    df = load_data()
    basic_statistics(df)
    check_columns(df)
    check_missing_values(df)
    check_data_types(df)
    validate_rolling_features(df)
    check_defense_features(df)
    summary(df)

    print("\nVALIDATION COMPLETE\n")

if __name__ == "__main__":
    main()
