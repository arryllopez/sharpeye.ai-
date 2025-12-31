from fastapi import APIRouter
from typing import List

from app.betData.providers.theodds_nba_provider import (
    TheOddsNbaProvider,
    GameDTO,
    PlayerDTO,
    BookmakerOdds,
)

router = APIRouter(prefix="/nba", tags=["NBA"])
provider = TheOddsNbaProvider()

@router.get("/games", response_model=List[GameDTO])
async def nba_games():
    """
    List today’s NBA games (quota-free).
    """
    return await provider.get_games()

@router.get("/games/{event_id}/players", response_model=List[PlayerDTO])
async def nba_game_players(event_id: str):
    """
    List players that currently have props for this game.
    """
    return await provider.get_prop_players(event_id)
