"""
FAST ingestion of NBA player game logs using LeagueGameLog.

One row = one player-game.
This is the correct way to build large historical datasets.
"""

import time
import pandas as pd
from tqdm import tqdm
from nba_api.stats.endpoints import leaguegamelog


# ======================
# CONFIG
# ======================

SEASONS = [
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
]

SLEEP_SECONDS = 1.0  # safe rate limit
OUTPUT_PATH = "data/raw/player_game_logs.csv"


# ======================
# MAIN
# ======================

def main():
    all_seasons = []

    for season in tqdm(SEASONS, desc="Seasons"):
        print(f"\nFetching season {season}...")

        try:
            lg = leaguegamelog.LeagueGameLog(
                season=season,
                season_type_all_star="Regular Season",
                player_or_team_abbreviation="P",
            )

            df = lg.get_data_frames()[0]
            df["SEASON"] = season
            all_seasons.append(df)

            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            print(f"[ERROR] Season {season} failed: {e}")
            continue

    if not all_seasons:
        raise RuntimeError("No data collected")

    df = pd.concat(all_seasons, ignore_index=True)

    # ======================
    # SELECT + CLEAN
    # ======================

    df = df[
        [
            "PLAYER_ID",
            "PLAYER_NAME",
            "TEAM_ABBREVIATION",
            "GAME_DATE",
            "MATCHUP",
            "MIN",
            "PTS",
            "REB",
            "AST",
            "FG3M",
        ]
    ]

    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df["IS_HOME"] = df["MATCHUP"].apply(lambda x: 1 if "vs." in x else 0)

    # Drop DNPs
    df = df[df["MIN"] > 0]

    # Sort for rolling features
    df = df.sort_values(
        by=["PLAYER_ID", "GAME_DATE"]
    ).reset_index(drop=True)

    print(f"\nFinal dataset size: {len(df)} rows")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
