from typing import List, Optional, Dict
from dataclasses import dataclass
import hashlib
import re
from datetime import datetime
import pytz

from app.core.config import settings
from app.betData.providers.theodds_client import TheOddsApiClient

SPORT_KEY = "basketball_nba"

@dataclass
class GameDTO:
    event_id: str
    commence_time: str
    home_team: str
    away_team: str

@dataclass
class BookmakerOdds:
    bookmaker_key: str
    bookmaker_name: str
    over_odds: Optional[int] #if odds are not available , set to none
    under_odds: Optional[int] 

@dataclass
class PlayerDTO:
    player_id: str
    name: str
    prop_line: float
    bookmakers: List['BookmakerOdds'] 
    data_as_of : str #timestamp when data was fetched 



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
        data = await self.client.get_json(
            f"/v4/sports/{SPORT_KEY}/events",
            params={"dateFormat": "iso"},
        )

        # Filter to only today's games (ET timezone)
        et_tz = pytz.timezone("America/New_York")
        today = datetime.now(et_tz).date()

        return [
            GameDTO(
                event_id=e["id"],
                commence_time=e["commence_time"],
                home_team=e["home_team"],
                away_team=e["away_team"],
            )
            for e in data
            if datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
               .astimezone(et_tz).date() == today
        ]

    async def get_prop_players(self, event_id: str) -> List[PlayerDTO]:
        #theoddsapi - documentation - extract players from player prop markets with
        #points line - over and under odds 
        data = await self.client.get_json(
            f"/v4/sports/{SPORT_KEY}/events/{event_id}/odds",
            params={
                "regions": "us",
                "markets": "player_points",
                "oddsFormat": "american",
                "dateFormat": "iso",
            },
        )

        # store player data: {player_name: {prop_line, bookmakers: [{bookmaker, over, under}]}}
        player_props: Dict[str, Dict] = {}

        for book in data.get("bookmakers", []):
            bookmaker_key = book.get("key", "unknown")
            bookmaker_name = book.get("title", "Unknown")

            for market in book.get("markets", []):
                if market.get("key") != "player_points":
                    continue

                # Group outcomes by player (Over and Under for same player)
                player_outcomes = {}
                for outcome in market.get("outcomes", []):
                    player_name = outcome.get("description", "").strip()
                    if not player_name:
                        continue

                    if player_name not in player_outcomes:
                        player_outcomes[player_name] = {
                            "prop_line": outcome.get("point", 0.0),
                            "over_odds": None,
                            "under_odds": None
                        }

                    # Store Over/Under odds
                    if outcome.get("name") == "Over":
                        player_outcomes[player_name]["over_odds"] = outcome.get("price", -110)
                    elif outcome.get("name") == "Under":
                        player_outcomes[player_name]["under_odds"] = outcome.get("price", -110)

                # Add this bookmaker's odds to each player
                for player_name, odds_data in player_outcomes.items():
                    if player_name not in player_props:
                        player_props[player_name] = {
                            "prop_line": odds_data["prop_line"],
                            "bookmakers": []
                        }

                    # Add this bookmaker's odds
                    player_props[player_name]["bookmakers"].append(
                        BookmakerOdds(
                            bookmaker_key=bookmaker_key,
                            bookmaker_name=bookmaker_name,
                            over_odds=odds_data["over_odds"],
                            under_odds=odds_data["under_odds"]
                        )
                    )
        et_tz = pytz.timezone("America/New_York")
        current_time_et = datetime.now(et_tz)
        data_timestamp = current_time_et.strftime("%Y-%m-%d 9:00AM ET") #hard coding when daily ingestino wouldn take palce
        return [
            PlayerDTO(
                player_id=_player_id(name),
                name=name,
                prop_line=props["prop_line"],
                bookmakers=props["bookmakers"],
                data_as_of=data_timestamp 
            )
            for name, props in sorted(player_props.items())
        ]