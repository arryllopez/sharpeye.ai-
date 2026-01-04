"""
FAST ingestion of NBA player game logs using LeagueGameLog.

One row = one player-game.
This is the correct way to build large historical datasets.
"""

import time
import pandas as pd
from tqdm import tqdm
from nba_api.stats.endpoints import leaguegamelog, commonplayerinfo
import os
import pickle
from pathlib import Path 


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

SLEEP_SECONDS = 2.0  # conservative rate limit to avoid timeouts
#absolute path to output csv
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BACKEND_DIR, "data", "raw", "player_game_logs.csv")
CACHE_PATH = os.path.join(BACKEND_DIR, "data", "raw", "player_positions_cache.pkl")



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

    #ingesting player positions (Guard, Forward, Center)
    print("\nAdding player positions...")

    # Build position mapping from NBA API
    player_positions = {}

    # Load cached positions if available
    if os.path.exists(CACHE_PATH):
        print(f"  Loading position cache...")
        with open(CACHE_PATH, 'rb') as f:
            cached_positions = pickle.load(f)
        player_positions = cached_positions
        print(f"  Loaded {len(player_positions)} cached positions")

    # Get unique players that need positions
    unique_players_df = df[['PLAYER_ID', 'PLAYER_NAME']].drop_duplicates()
    missing_players = [
        (row['PLAYER_ID'], row['PLAYER_NAME'])
        for _, row in unique_players_df.iterrows()
        if row['PLAYER_ID'] not in player_positions
    ]

    print(f"\nUnique players in dataset: {len(unique_players_df)}")
    print(f"Need to fetch positions: {len(missing_players)}")

    if missing_players:
        print("\nFetching missing positions from NBA API...")
        checkpoint_interval = 50  # Save progress every 50 players

        for idx, (player_id, _) in enumerate(tqdm(missing_players, desc="Positions"), start=1):
            max_retries = 3
            retry_delay = 2.0

            position = 'Unknown'

            for attempt in range(max_retries):
                try:
                    # Fetch from NBA API
                    player_info = commonplayerinfo.CommonPlayerInfo(
                        player_id=player_id,
                        timeout=30
                    )
                    info_df = player_info.get_data_frames()[0]

                    if not info_df.empty and 'POSITION' in info_df.columns:
                        api_position = info_df['POSITION'].iloc[0]

                        # Use NBA API position as-is (Guard, Forward, Center)
                        if api_position and api_position in ['Guard', 'Forward', 'Center']:
                            position = api_position
                        else:
                            position = 'Unknown'

                    player_positions[player_id] = position
                    break

                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        # Final fallback
                        player_positions[player_id] = 'Unknown'

            # Rate limit between players
            time.sleep(SLEEP_SECONDS)

            # Checkpoint: Save progress every N players
            if idx % checkpoint_interval == 0:
                print(f"\n  Checkpoint: Saving progress ({idx}/{len(missing_players)} players)...")
                with open(CACHE_PATH, 'wb') as f:
                    pickle.dump(player_positions, f)
                print(f"  Checkpoint saved")

        # Save final cache
        print(f"\nSaving final position cache...")
        with open(CACHE_PATH, 'wb') as f:
            pickle.dump(player_positions, f)
        print("  Cache saved")

    # Map positions to dataframe
    df['POSITION'] = df['PLAYER_ID'].map(player_positions).fillna('Unknown')

    print(f"\nPosition distribution:")
    print(df['POSITION'].value_counts())

    print(f"\nFinal dataset size: {len(df)} rows")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
