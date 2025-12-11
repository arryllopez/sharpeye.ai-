from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter()

class PropsSimRequest(BaseModel):
    league: Literal["nba", "nhl", "nfl", "mlb"]
    player_name: str
    stat_type: str
    line: float
    opponent: str = "TBD"
    minutes_projection: float = 34.0
    pace_factor: float = 1.0
    recent_avg: float | None = None
    n_sims: int = Field(default=10000, ge=1000, le=200000)

@router.post("/simulate") #only uses the post method , keep in mind when building frontend
def simulate_prop(req: PropsSimRequest):
    #fake output just to test

    expected_mean = req.recent_avg if req.recent_avg is not None else 25.0
    expected_std = max(2.0, 0.22 * expected_mean)

    adjusted_mean = expected_mean * (req.minutes_projection / 34.0) * req.pace_factor
    adjusted_std = expected_std

    # Fake probabilities for now
    over_prob = 0.58
    under_prob = 0.42

    return {
        "expected_mean": expected_mean,
        "expected_std": expected_std,
        "adjusted_mean": adjusted_mean,
        "adjusted_std": adjusted_std,
        "probs": {"over_prob": over_prob, "under_prob": under_prob},
        "distribution_sample": [22, 24, 26, 28, 30],
        "edges": []
    }
