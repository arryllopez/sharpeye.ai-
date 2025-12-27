"""
FAST ingestion of NBA player game logs using LeagueGameLog.

One row = one player-game.
This is the correct way to build large historical datasets.
"""

import time
import pandas as pd
from tqdm import tqdm
from nba_api.stats.endpoints import leaguegamelog, leaguedashplayerstats
import os


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
#absolute path to output csv
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BACKEND_DIR, "data", "raw", "player_game_logs.csv")
ADVANCED_OUTPUT_PATH = os.path.join(BACKEND_DIR, "data", "raw", "player_advanced_stats.csv")


# ======================
# MAIN
# ======================

def main():
    all_seasons = []
    all_advanced = []

    for season in tqdm(SEASONS, desc="Seasons"):
        print(f"\nFetching season {season}...")

        try:
            # Basic game logs
            lg = leaguegamelog.LeagueGameLog(
                season=season,
                season_type_all_star="Regular Season",
                player_or_team_abbreviation="P",
            )

            df = lg.get_data_frames()[0]
            df["SEASON"] = season
            all_seasons.append(df)

            time.sleep(SLEEP_SECONDS)
            
            # Advanced stats (real usage rate)
            print(f"  Fetching advanced stats for {season}...")
            try:
                advanced = leaguedashplayerstats.LeagueDashPlayerStats(
                    season=season,
                    measure_type_detailed_defense="Advanced",
                    per_mode_detailed="PerGame",
                    season_type_all_star="Regular Season"
                )
                
                adv_df = advanced.get_data_frames()[0]
                adv_df["SEASON"] = season
                
                # Keep only relevant columns
                adv_df = adv_df[[
                    "PLAYER_ID",
                    "PLAYER_NAME",
                    "SEASON",
                    "USG_PCT",      # Real usage rate
                    "PACE",         # Pace of play
                    "TS_PCT",       # True shooting %
                ]]
                
                all_advanced.append(adv_df)
                time.sleep(SLEEP_SECONDS)
                
            except Exception as e:
                print(f"  [WARN] Advanced stats failed for {season}: {e}")

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
        #adding more features 
        "PLAYER_ID",
        "PLAYER_NAME",
        "TEAM_ABBREVIATION",
        "GAME_DATE",
        "MATCHUP",
        "MIN",
        "PTS",
        "REB",
        "AST",
        "FGM",
        "FGA",
        "FG3M",
        "FG3A",
        "FTM",
        "FTA",
        "TOV",
        "PF",
        "PLUS_MINUS",
        "SEASON",  
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
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")
    
    # Save advanced stats if available
    if all_advanced:
        advanced_df = pd.concat(all_advanced, ignore_index=True)
        print(f"\nAdvanced stats size: {len(advanced_df)} rows")
        advanced_df.to_csv(ADVANCED_OUTPUT_PATH, index=False)
        print(f"Saved to {ADVANCED_OUTPUT_PATH}")
    else:
        print("[WARN] No advanced stats collected")


if __name__ == "__main__":
    main()