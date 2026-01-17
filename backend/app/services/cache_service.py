# Redis caching service for TheOdds API data
# Purpose: Cache games and player props to reduce API quota usage
# Strategy: Fetch data once at 10 AM ET, serve from cache for 24 hours
# Eventually integrated as an AWS Lambda function triggered by CloudWatch Events

#imports
import json
import redis.asyncio as aioredis
from typing import Optional, List, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os


class CacheService:
    # Redis-based caching service for odds data
    # Caches: NBA games list + player props per game (24-hour TTL)

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_client: Optional[aioredis.Redis] = None
        self.enabled = bool(self.redis_url)  # Disable if no REDIS_URL (local dev)

    async def connect(self):
        # Initialize Redis connection on app startup
        if not self.enabled:
            print("Redis caching disabled - no REDIS_URL provided")
            return

        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True  # Auto-decode bytes to strings
            )
            # Test connection
            await self.redis_client.ping()
            print("Redis cache service connected successfully")
        except Exception as e:
            print(f"Failed to connect to Redis cache: {e}")
            self.enabled = False

    async def close(self):
        # Close Redis connection on app shutdown
        if self.redis_client:
            await self.redis_client.close()

    def _get_today_et(self) -> str:
        # Get current date in ET timezone (YYYY-MM-DD format)
        et_tz = ZoneInfo("America/New_York")
        return datetime.now(et_tz).strftime("%Y-%m-%d")

    def _get_games_key(self) -> str:
        # Generate Redis key for today's games
        # Format: "nba:games:2026-01-08"
        today = self._get_today_et()
        return f"nba:games:{today}"

    def _get_players_key(self, event_id: str) -> str:
        # Generate Redis key for player props for a specific game
        # Format: "nba:game:abc123:players:2026-01-08"
        today = self._get_today_et()
        return f"nba:game:{event_id}:players:{today}"

    async def get_games(self) -> Optional[List[dict]]:
        # Get cached games list
        # Returns: List of game dicts if cached, None if not cached or Redis disabled
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._get_games_key()
            cached = await self.redis_client.get(key)

            if cached:
                return json.loads(cached)  # Deserialize JSON string to Python list
            return None
        except Exception as e:
            print(f"Error reading games from cache: {e}")
            return None

    async def set_games(self, games: List[dict], ttl_hours: int = 24) -> bool:
        # Cache games list with TTL (time-to-live)
        # Args:
        #   games: List of game dicts from TheOdds API
        #   ttl_hours: How long to keep in cache (default 24 hours)
        # Returns: True if cached successfully, False otherwise
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._get_games_key()
            value = json.dumps(games)  # Serialize Python list to JSON string
            ttl_seconds = ttl_hours * 3600

            await self.redis_client.setex(key, ttl_seconds, value)  # Set with expiration
            print(f"Cached {len(games)} games with {ttl_hours}h TTL")
            return True
        except Exception as e:
            print(f"Error caching games: {e}")
            return False

    async def get_players(self, event_id: str) -> Optional[List[dict]]:
        # Get cached player props for a specific game
        # Args: event_id: TheOdds API event ID (e.g., "abc123")
        # Returns: List of player dicts if cached, None if not cached or Redis disabled
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._get_players_key(event_id)
            cached = await self.redis_client.get(key)

            if cached:
                return json.loads(cached)  # Deserialize JSON string to Python list
            return None
        except Exception as e:
            print(f"Error reading players from cache: {e}")
            return None

    async def set_players(self, event_id: str, players: List[dict], ttl_hours: int = 12) -> bool:
        # Cache player props for a specific game with TTL
        # Args:
        #   event_id: TheOdds API event ID
        #   players: List of player dicts from TheOdds API
        #   ttl_hours: How long to keep in cache (default 24 hours)
        # Returns: True if cached successfully, False otherwise
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._get_players_key(event_id)
            value = json.dumps(players)  # Serialize Python list to JSON string
            ttl_seconds = ttl_hours * 3600

            await self.redis_client.setex(key, ttl_seconds, value)  # Set with expiration
            print(f"Cached {len(players)} players for event {event_id} with {ttl_hours}h TTL")
            return True
        except Exception as e:
            print(f"Error caching players: {e}")
            return False

    async def clear_today(self) -> int:
        # Clear all cached data for today (force refresh)
        # Returns: Number of keys deleted
        if not self.enabled or not self.redis_client:
            return 0

        try:
            today = self._get_today_et()
            pattern = f"nba:*:{today}"

            # Find all keys matching pattern (games + all player props for today)
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            # Delete them all at once
            if keys:
                deleted = await self.redis_client.delete(*keys)
                print(f"Cleared {deleted} cached entries for {today}")
                return deleted
            return 0
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return 0


# Global cache service instance (singleton pattern)
# Import this in your endpoints: from app.services.cache_service import cache_service
cache_service = CacheService()
