#All necessary imports 
from fastapi import FastAPI, Depends, HTTPException
#import the nba routes from app/api/nba_routes.py
#that script holds all  api endpoints related to FETCHING nba games. list of games , list players that have props
from app.api.nba_routes import router as nba_router 
from sqlalchemy import select, func, and_
from datetime import date, datetime
from app.models.nba_models import PlayerGameLog
#rate limiting with fastapi-limiter + Redis (Upstash)
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as aioredis
#debug routers hidden in production
from fastapi import APIRouter, Depends, HTTPException 
#additional imports - to be used in the future for model loading etc
from contextlib import asynccontextmanager #lifespan function --> run once when sserver starts to ingest model and model data, cleanup on shutdown
import pickle #for loading model data
import pandas as pd
from pathlib import Path #abosltue paths
from dotenv import load_dotenv
#security middleware 
from fastapi import Request
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware 
#os for environment variables
import os
#logging
import logging


#prediction imports
from app.core.database import get_db
from app.services.prediction_service import PredictionService
from app.services.feature_service import FeatureCalculationService
from app.schemas.prediction import PredictionRequest, PredictionResponse
#cache service for odds data
from app.services.cache_service import cache_service

#global model storage
model_data = {} #avoids reloading model on every request and is cleared on shutdown

#load environment variables from .env file
load_dotenv() #solely for checking environment mode

ENV = os.getenv("ENV", "development")

#debug router for development only
debug_router=APIRouter(prefix="/debug", tags=["debug"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model and initialize Redis
    print("Loading XGBoost model and metadata...")

    models_dir = Path(__file__).parent.parent / "models"

    try:
        # Load model
        with open(models_dir / "xgb_points_model.pkl", "rb") as f:
            model_data['model'] = pickle.load(f)

        # Load feature columns
        with open(models_dir / "feature_cols.pkl", "rb") as f:
            model_data['feature_cols'] = pickle.load(f)

        # Load metadata
        with open(models_dir / "model_metadata.pkl", "rb") as f:
            model_data['metadata'] = pickle.load(f)

        print(f"Model loaded successfully!")
        print(f"  CV MAE: {model_data['metadata']['cv_mean_mae']:.2f} points")
        print(f"  Features: {len(model_data['feature_cols'])}")

    except Exception as e:
        print(f"ERROR loading model: {e}")
        raise

    # Initialize Redis rate limiting (optional - graceful fallback if no REDIS_URL)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_connection = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
            await FastAPILimiter.init(redis_connection)
            print("Redis rate limiting initialized successfully")
        except Exception as e:
            print(f"WARNING: Redis connection failed: {e}")
            print("Rate limiting will be disabled")
    else:
        print("No REDIS_URL provided - rate limiting disabled (dev mode)")

    # Initialize cache service for odds data
    await cache_service.connect()

    yield

    # Shutdown: Cleanup
    print("Shutting down...")
    if redis_url:
        try:
            await FastAPILimiter.close()
        except:
            pass
    # Close cache service
    await cache_service.close()
    model_data.clear()


#class for security middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Looser CSP for /docs endpoints
        if request.url.path.startswith(('/docs', '/openapi.json')):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' https://fastapi.tiangolo.com data:; "
                "font-src 'self' https://cdn.jsdelivr.net data:"
            )
        else:
            # Strict CSP for API endpoints
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

#logging middleware
#define the logging config
logging.basicConfig(
    filename="app.log", #log the data into this file 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        response = await call_next(request) #await the next request 
        #log the request details
        client_ip = request.client.host
        method = request.method #get post put or delete
        url = request.url.path
        status_code = response.status_code

        logger.info(f"Request type: {method} ,{url} returned {status_code} to {client_ip}")

        return response


#application instance
app = FastAPI(
    title="SharpEye Backend",
    version="0.1.0",
    lifespan=lifespan,
    #adding doc disabling when in production can be done here
    docs_url = None if ENV == "production" else "/docs",
    redoc_url = None if ENV == "production" else "/redoc",
    #hiding openapi spec in production
    openapi_url=None if ENV == "production" else "/openapi.json"

)

app.include_router(nba_router) #include the nba router to the main app, so all endpoints defined in nba_routes.py are accessible

#include the security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

#include the logging middleware
app.add_middleware(LoggingMiddleware)

if ENV == "development":
    app.include_router(debug_router)

@app.get("/health") #check if the api is running
async def health(db = Depends(get_db)):
    try: 
        await db.execute(select(1))
        model_loaded=bool(model_data.get('model'))
        return {
            "status": "ok" if model_loaded else "degraded",
            "model_loaded": model_loaded,
            "database": "connected" 
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail = "Service unavailable")

@app.get("/info") #root endpoint 
def info():
    return {"service": "SharpEye Backend", "version": "0.1.0"} #return basic info about the service

@app.get("/") #root endpoint
def root():
    return {"message": "Welcome to the SharpEye Backend API, type in /docs to view the API documentation"} #return a welcome message at the root endpoint

@debug_router.get("/database-date-range")
async def debug_database_date_range(db = Depends(get_db)):
    #check the date range of data in the database - verifying the rolling window
   
    #get min and max dates

    # SELECT MIN(game_date), MAX(game_date), COUNT(*)
    # FROM player_game_logs;

    stmt = select (
        func.min(PlayerGameLog.game_date),
        func.max(PlayerGameLog.game_date),
        func.count()
    )
    result = await db.execute(stmt)
    min_result, max_result, count_result = result.fetchone()

    return {
        "earliest_game": str(min_result),
        "most_recent_game": str(max_result),
        "total_games": count_result
    }

@debug_router.get("/player/{player_name}")
async def debug_player_data(player_name: str, db = Depends(get_db)):
    #debug endpoint to fetch recent  games for a player and total games in db

    #get all games for player
    stmt = select(PlayerGameLog).where(
        PlayerGameLog.player.ilike(f'%{player_name}%')
    ).order_by(PlayerGameLog.game_date.desc()).limit(20)

    result = await db.execute(stmt)
    games = result.scalars().all()

    #secondary check if any games found - if not found raise 404 error
    if not games:
        raise HTTPException(status_code=404, detail={"error": f"No games found for '{player_name}'"})

    # count total games
    count_stmt = select(func.count()).select_from(PlayerGameLog).where(
        PlayerGameLog.player.ilike(f'%{player_name}%')
    )
    total_result = await db.execute(count_stmt)
    total_games = total_result.scalar()

    return {
        "player": games[0].player if games else None,
        "team": games[0].team if games else None,
        "position": games[0].position if games else None,
        "total_games_in_db": total_games,
        "most_recent_20_games": [
            {
                "date": str(g.game_date),
                "opponent": g.matchup,
                "points": g.points,
                "minutes": g.minutes,
                "is_home": g.is_home
            }
            for g in games
        ]
    }


#debug endpoint to verify feature calculations step-by-step
@debug_router.get("/features/{player_name}")
async def debug_feature_calculation(
    player_name: str,
    game_date: str,
    opponent: str,
    player_team: str,
    is_home: bool = True,
    db = Depends(get_db)
):
    feature_service = FeatureCalculationService(db)
    pred_date = datetime.strptime(game_date, "%Y-%m-%d").date()

    #Get L5 stats
    l5_stmt = select(PlayerGameLog).where(
        and_(
            PlayerGameLog.player == player_name,
            PlayerGameLog.game_date < pred_date
        )
    ).order_by(PlayerGameLog.game_date.desc()).limit(5)
    l5_result = await db.execute(l5_stmt)
    l5_games = l5_result.scalars().all()

    #Get L10 stats
    l10_stmt = select(PlayerGameLog).where(
        and_(
            PlayerGameLog.player == player_name,
            PlayerGameLog.game_date < pred_date
        )
    ).order_by(PlayerGameLog.game_date.desc()).limit(10)
    l10_result = await db.execute(l10_stmt)
    l10_games = l10_result.scalars().all()

    #Get L20 stats
    l20_stmt = select(PlayerGameLog).where(
        and_(
            PlayerGameLog.player == player_name,
            PlayerGameLog.game_date < pred_date
        )
    ).order_by(PlayerGameLog.game_date.desc()).limit(20)
    l20_result = await db.execute(l20_stmt)
    l20_games = l20_result.scalars().all()

    # Calculate features using service
    l5_features = await feature_service.get_player_rolling_stats(player_name, pred_date, 5)
    l10_features = await feature_service.get_player_rolling_stats(player_name, pred_date, 10)
    l20_features = await feature_service.get_player_rolling_stats(player_name, pred_date, 20)
    rest_days = await feature_service.get_rest_days(player_name, pred_date)

    # Get opponent defense
    opp_defense = await feature_service.get_opponent_defensive_stats(opponent, pred_date, 10)

    # Get pace stats
    pace_stats = await feature_service.get_team_pace_stats(player_team, pred_date, lookback_days=5)

    return {
        "player": player_name,
        "game_date": game_date,
        "opponent": opponent,
        "games_found": {
            "l5": len(l5_games),
            "l10": len(l10_games),
            "l20": len(l20_games)
        },
        "l5_raw_games": [
            {
                "date": str(g.game_date),
                "opponent": g.matchup,
                "points": g.points,
                "minutes": g.minutes,
                "fga": g.fg_attempted,
                "rebounds": g.rebounds,
                "assists": g.assists
            }
            for g in l5_games
        ],
        "l10_raw_games": [
            {
                "date": str(g.game_date),
                "points": g.points,
                "minutes": g.minutes
            }
            for g in l10_games
        ],
        "calculated_features": {
            "l5_stats": l5_features,
            "l10_stats": l10_features,
            "l20_stats": l20_features,
            "rest_days": rest_days,
            "opponent_defense": opp_defense,
            "pace_stats": pace_stats
        },
        "manual_verification": {
            "l5_pts_avg": sum(g.points for g in l5_games) / len(l5_games) if l5_games else 0,
            "l10_pts_avg": sum(g.points for g in l10_games) / len(l10_games) if l10_games else 0,
            "l20_pts_avg": sum(g.points for g in l20_games) / len(l20_games) if l20_games else 0,
            "l5_min_avg": sum(g.minutes for g in l5_games) / len(l5_games) if l5_games else 0,
            "l10_min_avg": sum(g.minutes for g in l10_games) / len(l10_games) if l10_games else 0
        }
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_player_points(
    prediction_request: PredictionRequest,
    db = Depends(get_db),
    rate_limit: None = Depends(RateLimiter(times=10, seconds=60))  # 10 requests per minute
):
    #docstring for the endpoint
    """
    Predict NBA player points for upcoming game.

    This endpoint calculates all features from the database, runs XGBoost prediction,
    and optionally performs Monte Carlo simulation if a prop line is provided.

    Required parameters:
    - player: Player name (full or partial)
    - player_team: Team abbreviation (e.g., "LAL")
    - opponent: Opponent full name (e.g., "Boston Celtics")
    - game_date: Game date (YYYY-MM-DD)
    - is_home: True if home game, False if away

    Optional parameters:
    - prop_line: Betting line (e.g., 25.5)
    - over_odds: Over odds (default: -110)
    - under_odds: Under odds (default: -110)

    Returns comprehensive prediction with:
    - Predicted points
    - Player recent stats
    - Matchup analysis
    - Pace context
    - Confidence intervals
    - Monte Carlo analysis (if prop_line provided)
    - Key factors
    """
    # Check if model is loaded
    if 'model' not in model_data:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Server is starting up."
        )
    try:
        # Initialize prediction service
        prediction_service = PredictionService(
            model=model_data['model'],
            feature_cols=model_data['feature_cols'],
            model_metadata=model_data['metadata'],
            db=db
        )

        # Generate prediction
        result = await prediction_service.predict(
            player=prediction_request.player,
            player_team=prediction_request.player_team,
            opponent=prediction_request.opponent,
            game_date=prediction_request.game_date,
            is_home=prediction_request.is_home,
            prop_line=prediction_request.prop_line,
            over_odds=prediction_request.over_odds or -110,
            under_odds=prediction_request.under_odds or -110
        )

        return result
    except ValueError as e:
        # Player not found or invalid input
        raise HTTPException(
            status_code=404, 
            detail="Player not found in database. Data may not be available yet."
        )
    except Exception as e:
        # Unexpected error
        logging.error(f"Prediction error: {str(e)}", exc_info=True)  # Log details server-side
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Please try again later."  # Generic message to user
        )