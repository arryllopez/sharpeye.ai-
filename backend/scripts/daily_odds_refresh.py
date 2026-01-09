# Daily cron job to fetch and cache TheOddsAPI NBA odds data
# Runs at 4 PM ET every day (after lineups/injuries announced)
# Purpose: Fetch all games + player props with odds, cache for 24 hours
# Reduces API quota usage by serving from cache throughout the day - since theoddsapi is limited 

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


async def refresh_cache():
    # Main cron job logic
    print("=" * 60)
    print(f"Daily odds refresh started at {datetime.now()}")
    print("=" * 60)

    # Step 1: Connect to Redis
    await cache_service.connect()
    if not cache_service.enabled:
        print("ERROR: Redis not available, cannot cache data")
        return

    # Step 2: Check cached games (already fetched at 3 AM)
    print("\n[1/2] Checking cached games...")
    cached_games = await cache_service.get_games()

    if not cached_games:
        print("  WARNING: No cached games found! Fetching from API...")
        # Fallback: fetch games if cache miss
        provider = TheOddsNbaProvider()
        games = await provider.get_games()
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
        cached_games = games_dict

    print(f"  Found {len(cached_games)} games in cache")

    # Step 3: Initialize provider
    provider = TheOddsNbaProvider()

    try:
        # Step 4: Fetch player props with odds for each game
        print(f"\n[2/2] Fetching player props with odds for {len(cached_games)} games...")
        for i, game_dict in enumerate(cached_games, 1):
            event_id = game_dict["event_id"]
            away = game_dict["away_team"]
            home = game_dict["home_team"]
            print(f"  [{i}/{len(cached_games)}] {away} @ {home}")

            try:
                # Fetch player props for this game
                players = await provider.get_prop_players(event_id)
                print(f"    Found {len(players)} players with props")

                # Cache player props
                players_dict = [
                    {
                        "player_id": p.player_id,
                        "name": p.name,
                        "prop_line": p.prop_line,
                        "bookmakers": [
                            {
                                "bookmaker_key": b.bookmaker_key,
                                "bookmaker_name": b.bookmaker_name,
                                "over_odds": b.over_odds,
                                "under_odds": b.under_odds
                            }
                            for b in p.bookmakers
                        ],
                        "data_as_of": p.data_as_of
                    }
                    for p in players
                ]
                await cache_service.set_players(event_id, players_dict, ttl_hours=24)
                print(f"    Cached {len(players)} players")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"    ERROR fetching players for {event_id}: {e}")
                continue

        # Step 5: Summary
        print("\n" + "=" * 60)
        print(f"Odds refresh complete!")
        et_tz = ZoneInfo("America/New_York")
        current_time_et = datetime.now(et_tz).strftime("%Y-%m-%d %I:%M %p ET")
        print(f"  Timestamp: {current_time_et}")
        print(f"  Games processed: {len(cached_games)}")
        print(f"  Cache TTL: 24 hours")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR during cache refresh: {e}")
        raise

    finally:
        # Step 7: Cleanup
        await cache_service.close()


if __name__ == "__main__":
    # Run the async function
    asyncio.run(refresh_cache())
