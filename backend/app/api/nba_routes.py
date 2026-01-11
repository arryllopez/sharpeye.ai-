from fastapi import APIRouter, Header, HTTPException, Depends
from typing import List
import os

from app.betData.providers.theodds_nba_provider import (
    TheOddsNbaProvider,
    GameDTO,
    PlayerDTO,
    BookmakerOdds,
)
from app.services.cache_service import cache_service

router = APIRouter(prefix="/nba", tags=["NBA"])
provider = TheOddsNbaProvider()

# Security: Secret token for cron endpoints
CRON_SECRET = os.getenv("CRON_SECRET", "")

def verify_cron_secret(x_cron_secret: str = Header(None)):
    """Verify the cron secret token"""
    if not CRON_SECRET:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    return True

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

    # Cache the results for 10 hours (expires at 2 AM ET)
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
    await cache_service.set_players(event_id, players_dict, ttl_hours=10)

    return players


# Cron job endpoints -- utilizes the secret token and the verify function to be accessible

# Fetching tonight's games - Morning CRON job (3 AM ET) 
@router.post("/cron/fetch-tonights-games", dependencies=[Depends(verify_cron_secret)])
async def cron_fetch_tonights_games():
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    #reuse script fetch tonghts games logic 
    from scripts.fetch_tonights_games import fetch_tonights_games

    try:
        await fetch_tonights_games()
        return {"status": "success", "message": "Fetched and cached tonight's games"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cron job failed: {str(e)}")


@router.post("/cron/ingest-and-cleanup", dependencies=[Depends(verify_cron_secret)])
async def cron_ingest_and_cleanup():
    # Morning cron job (3 AM ET) - Ingest new data and clean up old records
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    from scripts.ingest_and_cleanup_db import ingest_and_cleanup

    try:
        await ingest_and_cleanup()
        return {"status": "success", "message": "Ingested data and cleaned up old records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cron job failed: {str(e)}")


@router.post("/cron/daily-odds-refresh", dependencies=[Depends(verify_cron_secret)])
async def cron_daily_odds_refresh():
    # Evening cron job (8 PM ET) - Refresh odds cache
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))

    from scripts.daily_odds_refresh import refresh_cache

    try:
        await refresh_cache()
        return {"status": "success", "message": "Refreshed odds cache"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cron job failed: {str(e)}")
