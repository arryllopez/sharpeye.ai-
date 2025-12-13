from typing import List, Set
from dataclasses import dataclass
import hashlib
import re

from app.core.config import settings
from app.data.providers.theodds_client import TheOddsApiClient

SPORT_KEY = "basketball_nba"

@dataclass
class GameDTO:
    event_id: str
    commence_time: str
    home_team: str
    away_team: str

@dataclass
class PlayerDTO:
    player_id: str
    name: str


def _player_id(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip().lower())
    return hashlib.sha1(clean.encode()).hexdigest()[:12]


class TheOddsNbaProvider:
    def __init__(self):
        self.client = TheOddsApiClient(
            settings.theodds_base_url,
            settings.theodds_api_key
        )

    async def get_games(self) -> List[GameDTO]:
        """
        GET /v4/sports/basketball_nba/events
        Quota cost: 0
        """
        data = await self.client.get_json(
            f"/v4/sports/{SPORT_KEY}/events",
            params={"dateFormat": "iso"},
        )

        return [
            GameDTO(
                event_id=e["id"],
                commence_time=e["commence_time"],
                home_team=e["home_team"],
                away_team=e["away_team"],
            )
            for e in data
        ]

    async def get_prop_players(self, event_id: str) -> List[PlayerDTO]:
        """
        GET /v4/sports/basketball_nba/events/{event_id}/odds
        Extract players from player prop markets
        """
        data = await self.client.get_json(
            f"/v4/sports/{SPORT_KEY}/events/{event_id}/odds",
            params={
                "regions": "us",
                "markets": "player_points,player_rebounds,player_assists,player_threes",
                "oddsFormat": "american",
                "dateFormat": "iso",
            },
        )

        players: Set[str] = set()

        for book in data.get("bookmakers", []):
            for market in book.get("markets", []):
                for outcome in market.get("outcomes", []):
                    if "description" in outcome:
                        players.add(outcome["description"].strip())

        return [
            PlayerDTO(player_id=_player_id(name), name=name)
            for name in sorted(players)
        ]
