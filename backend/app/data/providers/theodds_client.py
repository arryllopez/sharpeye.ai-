from __future__ import annotations
from typing import Any, Dict, Optional
import httpx

class TheOddsApiClient:
    """
    Minimal client for The Odds API (v4).
    We'll use:
      - GET /v4/sports/{sport}/events
      - GET /v4/sports/{sport}/events/{eventId}/odds
    """

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
            return r.json()
  