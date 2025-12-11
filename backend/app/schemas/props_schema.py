from pydantic import BaseModel, Field
from typing import Literal, List

StatType = Literal["points", "rebounds", "assists", "threes", "shots", "goals", "saves", "yards"]

class ProbabilityBreakdown(BaseModel):
    over_prob: float
    under_prob: float

class EdgeResult(BaseModel):
    sportsbook: str
    market: str
    selection: str
    odds: float
    implied_prob: float
    model_prob: float
    edge: float

class PropsSimRequest(BaseModel):
    league: Literal["nba", "nhl", "nfl", "mlb"]
    player_name: str
    stat_type: StatType
    line: float
    opponent: str = "TBD"

    minutes_projection: float = 34.0
    pace_factor: float = 1.0
    recent_avg: float | None = None

    n_sims: int = Field(default=10000, ge=1000, le=200000)

class PropsSimResponse(BaseModel):
    expected_mean: float
    expected_std: float
    adjusted_mean: float
    adjusted_std: float
    probs: ProbabilityBreakdown
    distribution_sample: List[float]
    edges: List[EdgeResult] = []
