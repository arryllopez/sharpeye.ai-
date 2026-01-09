# Daily database maintenance - runs at 3 AM ET (after last night's games finish)
# Purpose:
#   1. Fetch last night's completed NBA game results
#   2. Insert new game logs into database
#   3. Delete game logs older than 60 days (maintain rolling window)

import asyncio
import sys
from pathlib import Path

# Add backend to Python path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.core.database import AsyncSessionLocal
from app.services.nba_data_service import nba_data_service


async def ingest_and_cleanup():
    # Main cron job logic
    print("=" * 60)
    print(f"Database ingestion and cleanup started at {datetime.now()}")
    print("=" * 60)

    et_tz = ZoneInfo("America/New_York")
    now = datetime.now(et_tz)

    # Last night = yesterday's date
    # (Games played last night have yesterday's date)
    yesterday = now - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    player_count = 0
    team_count = 0
    deleted_count = 0
    errors = []

    # Step 1: Ingest last night's game results
    print(f"\n[1/3] Ingesting last night's NBA game results ({date_str})...")

    try:
        # Fetch data from NBA Stats API
        player_logs = await nba_data_service.fetch_player_game_logs(date_str)
        team_logs = await nba_data_service.fetch_team_defensive_logs(date_str)

        # Insert into database
        try:
            async with AsyncSessionLocal() as session:
                player_count = await nba_data_service.insert_player_logs(player_logs, session)
                team_count = await nba_data_service.insert_team_defensive_logs(team_logs, session)
        except Exception as e:
            error_msg = f"Database insertion failed: {e}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

    except Exception as e:
        error_msg = f"NBA API fetch failed: {e}"
        print(f"  ERROR: {error_msg}")
        errors.append(error_msg)

    # Step 2 & 3: Cleanup old data from both tables (maintain 60-day rolling window)
    print("\n[2/3] Cleaning up old data (keeping last 60 days)...")
    cutoff_date = (now - timedelta(days=60)).strftime("%Y-%m-%d")
    print(f"  Cutoff date: {cutoff_date}")

    try:
        async with AsyncSessionLocal() as session:
            deleted_count = await nba_data_service.cleanup_old_data(cutoff_date, session)
    except Exception as e:
        error_msg = f"Database cleanup failed: {e}"
        print(f"  ERROR: {error_msg}")
        errors.append(error_msg)

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("Database maintenance completed WITH ERRORS!")
        print(f"  Errors encountered: {len(errors)}")
        for i, error in enumerate(errors, 1):
            print(f"  [{i}] {error}")
    else:
        print("Database maintenance complete!")

    print(f"  Ingested {player_count} player game logs")
    print(f"  Ingested {team_count} team defensive logs")
    print(f"  Cleaned up {deleted_count} old records")
    current_time_et = now.strftime("%Y-%m-%d %I:%M %p ET")
    print(f"  Timestamp: {current_time_et}")
    print("=" * 60)

    # Exit with error code if there were failures
    if errors:
        raise RuntimeError(f"Cron job completed with {len(errors)} error(s)")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(ingest_and_cleanup())
