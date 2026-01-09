# Morning cron job - runs at 3 AM ET (after last night's games finish)
# Purpose: Fetch tonight's game schedule and cache it (no odds yet)
# This gives users early visibility into tonight's games before odds are available

import asyncio
import sys
from pathlib import Path

# Add backend to Python path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.services.cache_service import cache_service
from app.betData.providers.theodds_nba_provider import TheOddsNbaProvider
from datetime import datetime
from zoneinfo import ZoneInfo


async def fetch_tonights_games():
    # Main cron job logic
    print("=" * 60)
    print(f"Fetch tonight's games started at {datetime.now()}")
    print("=" * 60)

    # Step 1: Connect to Redis
    await cache_service.connect()
    if not cache_service.enabled:
        print("ERROR: Redis not available, cannot cache data")
        return

    # Step 2: Initialize TheOdds provider
    provider = TheOddsNbaProvider()

    try:
        # Step 1: Fetch games for today (tonight's games) BEFORE clearing cache
        # This prevents data loss if the API fetch fails
        print("\n[1/2] Fetching tonight's game schedule...")
        games = await provider.get_games()
        print(f"  Found {len(games)} games scheduled for tonight")

        # Step 2: Clear yesterday's cache now that we have fresh data
        print("\n[2/2] Clearing yesterday's cache...")
        cleared = await cache_service.clear_today()
        print(f"  Cleared {cleared} stale cache entries")

        # Cache games list (without odds - odds come at 4 PM)
        games_dict = [
            {
                "event_id": g.event_id,
                "commence_time": g.commence_time,
                "home_team": g.home_team,
                "away_team": g.away_team
            }
            for g in games
        ]
        await cache_service.set_games(games_dict, ttl_hours=24)
        print(f"  Cached {len(games)} games")

        # Summary
        print("\nFetch tonight's games complete!")
        et_tz = ZoneInfo("America/New_York")
        current_time_et = datetime.now(et_tz).strftime("%Y-%m-%d %I:%M %p ET")
        print(f"  Timestamp: {current_time_et}")
        print(f"  Games cached: {len(games)}")
        print(f"  Note: Odds will be fetched at 4 PM ET")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR fetching tonight's games: {e}")
        raise

    finally:
        # Cleanup
        await cache_service.close()


if __name__ == "__main__":
    # Run the async function
    asyncio.run(fetch_tonights_games())
