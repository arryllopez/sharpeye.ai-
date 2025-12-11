from fastapi import APIRouter
from app.schemas.props_schema import (
    PropsSimRequest,
    PropsSimResponse,
    ProbabilityBreakdown,
    EdgeResult,
)
from app.services.feature_builder import build_props_features
from app.services.props_model import PropsBaselineModel
from app.services.bayesian_adjustment import apply_bayesian_adjustment, AdjustmentContext
from app.services.monte_carlo import run_props_monte_carlo

router = APIRouter()

@router.post("/simulate", response_model=PropsSimResponse)
def simulate_prop(req: PropsSimRequest):
    # 1) Build features from request
    features = build_props_features(
        recent_avg=req.recent_avg,
        minutes_projection=req.minutes_projection,
        pace_factor=req.pace_factor,
        opponent=req.opponent
    )

    # 2) Baseline model prediction
    model = PropsBaselineModel()
    mean, std = model.predict_mean_std(req.stat_type, features)

    # 3) Context-aware adjustment
    ctx = AdjustmentContext(
        minutes_projection=req.minutes_projection,
        pace_factor=req.pace_factor
    )
    adj_mean, adj_std = apply_bayesian_adjustment(mean, std, ctx)

    # 4) Monte Carlo simulation
    over_p, under_p, sample = run_props_monte_carlo(
        req.stat_type, adj_mean, adj_std, req.line, req.n_sims
    )

    # 5) No odds/edges yet – we’ll add sportsbook comparison later
    edges: list[EdgeResult] = []

    return PropsSimResponse(
        expected_mean=mean,
        expected_std=std,
        adjusted_mean=adj_mean,
        adjusted_std=adj_std,
        probs=ProbabilityBreakdown(over_prob=over_p, under_prob=under_p),
        distribution_sample=sample,
        edges=edges
    )
