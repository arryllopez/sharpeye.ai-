# Pydantic models for prediction request and response

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, List, Literal
from datetime import date


class PredictionRequest(BaseModel):
    # Request body for /predict endpoint
    # All fields populated by frontend from TheOddsAPI data
    # User can adjust prop_line, over_odds, under_odds via sliders

    player: str = Field(..., description="Player's full name from TheOddsAPI")
    player_team: str = Field(..., description="Player's team abbreviation (e.g., 'LAL')")
    opponent: str = Field(..., description="Opponent team full name (e.g., 'Boston Celtics')")
    game_date: date = Field(..., description="Game date (YYYY-MM-DD)")
    is_home: bool = Field(..., description="True if home game, False if away")

    # Optional betting line info - adjustable via slider
    prop_line: Optional[float] = Field(None, description="Points prop line (e.g., 25.5)")
    over_odds: Optional[int] = Field(-110, description="Over odds in American format (e.g., -110)")
    under_odds: Optional[int] = Field(-110, description="Under odds in American format (e.g., -110)")

    class Config:
        json_schema_extra = {
            "example": {
                "player": "LeBron James",
                "player_team": "LAL",
                "opponent": "Boston Celtics",
                "game_date": "2025-01-15",
                "is_home": True,
                "prop_line": 24.5,
                "over_odds": -110,
                "under_odds": -110
            }
        }


class PlayerStats(BaseModel):
    # Player's recent performance stats
    last_5_avg: float = Field(..., description="Last 5 games points average")
    last_10_avg: float = Field(..., description="Last 10 games points average")
    consistency_std: float = Field(..., description="Standard deviation (consistency indicator)")
    minutes_per_game: float = Field(..., description="Average minutes per game")
    rest_days: int = Field(..., description="Days since last game")


class MatchupAnalysis(BaseModel):
    # Opponent defensive matchup analysis
    opponent_defense_ppg: float = Field(..., description="Points allowed per game by opponent")
    defense_vs_position: float = Field(..., description="Points allowed to player's position")
    defense_quality: Literal["Weak", "Average", "Strong"] = Field(..., description="Defensive quality classification")


class PaceContext(BaseModel):
    # Game pace analysis
    player_team_pace: float = Field(..., description="Player's team pace (possessions/game)")
    opponent_pace: float = Field(..., description="Opponent pace (possessions/game)")
    expected_game_pace: float = Field(..., description="Expected game pace")
    pace_environment: Literal["Fast", "Average", "Slow"] = Field(..., description="Pace classification")
    expected_possessions: float = Field(..., description="Expected player possessions")


class MonteCarloAnalysis(BaseModel):
    # Monte Carlo simulation results
    probability_over: float = Field(..., description="Probability of going over prop line (0-1)")
    probability_under: float = Field(..., description="Probability of going under prop line (0-1)")
    edge: float = Field(..., description="Expected value / edge as percentage")
    confidence_score: float = Field(..., description="Confidence in prediction (0-100)")
    percentiles: Dict[int, float] = Field(..., description="Outcome percentiles (5, 25, 50, 75, 95)")
    recommendation: Literal["OVER", "UNDER", "PASS"] = Field(..., description="Betting recommendation")

    @field_validator('probability_over', 'probability_under')
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError('Probability must be between 0 and 1')
        return v

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError('Confidence score must be between 0 and 100')
        return v


class PredictionInterval(BaseModel):
    # Prediction confidence interval (90%)
    lower_90: float = Field(..., description="90% confidence interval lower bound")
    upper_90: float = Field(..., description="90% confidence interval upper bound")
    model_mae: float = Field(..., description="Model's mean absolute error")


class KeyFactors(BaseModel):
    # Key factors influencing the prediction
    recent_form: str = Field(..., description="Player's recent form description")
    matchup_favorability: Literal["Favorable", "Neutral", "Unfavorable"] = Field(..., description="Matchup assessment")
    pace_impact: Literal["Positive", "Neutral", "Negative"] = Field(..., description="Pace impact on scoring")
    rest_impact: Literal["Well-rested", "Normal", "Back-to-back"] = Field(..., description="Rest status")


class PredictionResponse(BaseModel):
    # Complete prediction response

    # Basic info
    player_name: str
    position: str
    team: str
    opponent: str
    location: Literal["HOME", "AWAY"]
    game_date: str

    # Main prediction
    predicted_points: float

    # Recent performance
    player_stats: PlayerStats

    # Matchup analysis
    matchup_analysis: MatchupAnalysis

    # Pace context
    pace_context: PaceContext

    # Confidence interval
    prediction_interval: PredictionInterval

    # Monte Carlo (only if prop_line provided)
    monte_carlo: Optional[MonteCarloAnalysis] = None

    # Key factors
    key_factors: KeyFactors

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "LeBron James",
                "position": "Forward",
                "team": "LAL",
                "opponent": "Boston Celtics",
                "location": "HOME",
                "game_date": "2025-01-15",
                "predicted_points": 26.3,
                "player_stats": {
                    "last_5_avg": 25.8,
                    "last_10_avg": 24.9,
                    "consistency_std": 5.2,
                    "minutes_per_game": 35.2,
                    "rest_days": 2
                },
                "matchup_analysis": {
                    "opponent_defense_ppg": 112.5,
                    "defense_vs_position": 58.3,
                    "defense_quality": "Average"
                },
                "pace_context": {
                    "player_team_pace": 101.2,
                    "opponent_pace": 99.8,
                    "expected_game_pace": 100.5,
                    "pace_environment": "Average",
                    "expected_possessions": 74.2
                },
                "prediction_interval": {
                    "lower_90": 15.8,
                    "upper_90": 36.8,
                    "model_mae": 4.85
                },
                "monte_carlo": {
                    "probability_over": 0.62,
                    "probability_under": 0.38,
                    "edge": 3.2,
                    "confidence_score": 68.0,
                    "percentiles": {
                        5: 16.2,
                        25: 21.8,
                        50: 26.3,
                        75: 30.9,
                        95: 36.4
                    },
                    "recommendation": "OVER"
                },
                "key_factors": {
                    "recent_form": "Consistent scorer averaging 25.8 PPG in last 5 games",
                    "matchup_favorability": "Favorable",
                    "pace_impact": "Neutral",
                    "rest_impact": "Well-rested"
                }
            }
        }