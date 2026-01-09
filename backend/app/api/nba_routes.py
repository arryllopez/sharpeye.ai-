from fastapi import APIRouter
from typing import List

from app.betData.providers.theodds_nba_provider import (
    TheOddsNbaProvider,
    GameDTO,
    PlayerDTO,
    BookmakerOdds,
)
from app.services.cache_service import cache_service

router = APIRouter(prefix="/nba", tags=["NBA"])
provider = TheOddsNbaProvider()

@router.get("/games", response_model=List[GameDTO])
async def nba_games():
    # List today's NBA games
    # Strategy: Check cache first, fallback to API if not cached

    # Try to get from cache
    cached_games = await cache_service.get_games()
    if cached_games is not None:
        # Cache hit - convert dict back to GameDTO objects
        return [GameDTO(**game) for game in cached_games]

    # Cache miss - fetch from TheOdds API
    games = await provider.get_games()

    # Cache the results for 24 hours
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

    return games

@router.get("/games/{event_id}/players", response_model=List[PlayerDTO])
async def nba_game_players(event_id: str):
    # List players that currently have props for this game
    # Strategy: Check cache first, fallback to API if not cached
    

    # Try to get from cache
    cached_players = await cache_service.get_players(event_id)
    if cached_players is not None:
        # Cache hit - convert dict back to PlayerDTO objects
        return [
            PlayerDTO(
                player_id=p["player_id"],
                name=p["name"],
                prop_line=p["prop_line"],
                bookmakers=[
                    BookmakerOdds(
                        bookmaker_key=b["bookmaker_key"],
                        bookmaker_name=b["bookmaker_name"],
                        over_odds=b["over_odds"],
                        under_odds=b["under_odds"]
                    )
                    for b in p["bookmakers"]
                ],
                data_as_of=p["data_as_of"]
            )
            for p in cached_players
        ]

    # Cache miss - fetch from TheOdds API (uses quota!)
    players = await provider.get_prop_players(event_id)

    # Cache the results for 24 hours
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

    return players
