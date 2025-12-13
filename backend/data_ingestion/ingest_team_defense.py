import os
import time
import pandas as pd
from nba_api.stats.endpoints import LeagueGameFinder

# -------------------------
# CONFIG
# -------------------------
# -------------------------
# PATH CONFIG (DO NOT CHANGE)
# -------------------------

# Absolute path to backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Absolute path to backend/data/raw/
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")

# Final CSV output path
OUTPUT_PATH = os.path.join(
    RAW_DATA_DIR,
    "team_defensive_game_logs.csv"
)

# Ensure directory exists
os.makedirs(RAW_DATA_DIR, exist_ok=True)


SEASON_START_YEARS = [
    2023,  # 2023–24
    2024,  # 2024–25 
    2025,  # this will be the partial season 
]

SLEEP_BETWEEN_SEASONS = 20  # seconds


# -------------------------
# HELPERS
# -------------------------
def nba_season_string(start_year: int) -> str:
    """
    2023 -> '2023-24'
    """
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def fetch_season_games(season: str) -> pd.DataFrame:
    """
    One request per season. This is critical.
    """
    print(f"Fetching season {season}")
    lgf = LeagueGameFinder(season_nullable=season)
    df = lgf.get_data_frames()[0]
    return df


def build_defensive_logs(df: pd.DataFrame, season: str) -> pd.DataFrame:
    df = df.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df["SEASON"] = season

    # Select stats we want from the opponent
    opp = df[
        [
            "GAME_ID",
            "TEAM_ID",
            "TEAM_NAME",
            "PTS",
            "FG3M",
            "FG3A",
        ]
    ].rename(
        columns={
            "TEAM_ID": "OPP_TEAM_ID",
            "TEAM_NAME": "OPPONENT",
            "PTS": "PTS_ALLOWED",
            "FG3M": "FG3_ALLOWED",
            "FG3A": "FG3A_ALLOWED",
        }
    )

    # Self-join on GAME_ID
    merged = df.merge(
        opp,
        on="GAME_ID",
        how="inner",
    )

    # Drop self-joins (team matched to itself)
    merged = merged[merged["TEAM_ID"] != merged["OPP_TEAM_ID"]]

    merged["OPP_FG3_PCT"] = (
        merged["FG3_ALLOWED"] / merged["FG3A_ALLOWED"]
    )

    final = merged[
        [
            "GAME_ID",
            "GAME_DATE",
            "SEASON",
            "TEAM_ID",
            "TEAM_NAME",
            "OPPONENT",
            "PTS_ALLOWED",
            "FG3_ALLOWED",
            "FG3A_ALLOWED",
            "OPP_FG3_PCT",
        ]
    ].copy()

    return final



# -------------------------
# MAIN INGESTION
# -------------------------
def ingest_team_defense():
    all_frames = []

    for year in SEASON_START_YEARS:
        season = nba_season_string(year)

        try:
            raw = fetch_season_games(season)
            defense = build_defensive_logs(raw, season)
            all_frames.append(defense)
        except Exception as e:
            print(f"[WARN] Failed season {season}: {e}")

        time.sleep(SLEEP_BETWEEN_SEASONS)

    if not all_frames:
        raise RuntimeError("No team defense data ingested.")

    final_df = pd.concat(all_frames, ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved team defense data → {OUTPUT_PATH}")
    print(f"Rows: {len(final_df)}")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    ingest_team_defense()
