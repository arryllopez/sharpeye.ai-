from __future__ import annotations
from typing import Any, Dict, Optional
import httpx
import logging 

logger = logging.getLogger(__name__)
class TheOddsApiClient:
   
    def __init__(self, base_url: str, api_key: str, timeout_s: float = 15.0):
        if not api_key:
            raise ValueError("THEODDS_API_KEY is missing. Set it in your environment.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_s

    async def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = dict(params or {})
        params["apiKey"] = self.api_key

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()

            # Get JSON data before context closes
            data = r.json()

            # Log quota usage from headers
            remaining = r.headers.get("x-requests-remaining", "unknown")
            used = r.headers.get("x-requests-used", "unknown")
            last = r.headers.get("x-requests-last", "unknown")
            logger.info(
                "TheOdds API quota - Remaining: %s, Used: %s, Last request cost: %s",
                remaining, used, last
            )

            return data