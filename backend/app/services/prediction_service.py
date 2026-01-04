
# Prediction Service
# Orchestrates feature calculation, XGBoost prediction, and Monte Carlo simulation


from datetime import date
from typing import Optional, Dict
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.feature_service import FeatureCalculationService, TEAM_ABBR_TO_NAME
from app.core.monte_carlo import MonteCarloSimulator
from app.schemas.prediction import (
    PredictionResponse,
    PlayerStats,
    MatchupAnalysis,
    PaceContext,
    MonteCarloAnalysis,
    PredictionInterval,
    KeyFactors
)


class PredictionService:
    def __init__(
        self,
        model,
        feature_cols: list,
        model_metadata: dict,
        db: AsyncSession
    ):
        
        self.model = model
        self.feature_cols = feature_cols
        self.model_metadata = model_metadata
        self.db = db
        self.feature_service = FeatureCalculationService(db)
        self.monte_carlo = MonteCarloSimulator(n_simulations=10000)

    async def predict(
        self,
        player: str,
        player_team: str,
        opponent: str,
        game_date: date,
        is_home: bool,
        prop_line: Optional[float] = None,
        over_odds: int = -110,
        under_odds: int = -110
    ) -> PredictionResponse:
      
        # Step 1: Calculate features from database
        features_dict = await self.feature_service.build_features_for_prediction(
            player_name=player,
            player_team=player_team,
            opponent=opponent,
            game_date=game_date,
            is_home=is_home
        )

        # Get player info
        full_name, current_team, position = await self.feature_service.get_player_info(player, game_date)

        # CRITICAL: Validate critical features before proceeding
        # These features are essential for model accuracy - fail fast if missing
        critical_features = ['PTS_L5', 'PTS_L10', 'MIN_L5', 'DEF_PTS_ALLOWED_L5', 'REST_DAYS']
        for feat in critical_features:
            if feat not in features_dict or features_dict[feat] == 0:
                raise ValueError(
                    f"Critical feature '{feat}' is missing or zero. "
                    f"Cannot generate reliable prediction without this feature."
                )

        # Step 2: Add categorical features (one-hot encoding for teams)
        # Initialize all categorical features to 0
        for col in self.feature_cols:
            if col not in features_dict:
                features_dict[col] = 0

        # Set player's team
        team_col = f"TEAM_ABBREVIATION_{current_team}"
        if team_col in self.feature_cols:
            features_dict[team_col] = 1

        # Set opponent team
        opp_col = f"OPP_TEAM_NAME_{opponent}"
        if opp_col in self.feature_cols:
            features_dict[opp_col] = 1

        # Step 3: Create prediction DataFrame with correct column order
        X = pd.DataFrame([features_dict])[self.feature_cols]

        # Step 4: Make prediction
        predicted_points = float(self.model.predict(X)[0])

        # Step 5: Build response components
        player_stats = PlayerStats(
            last_5_avg=features_dict.get('PTS_L5', 0.0),
            last_10_avg=features_dict.get('PTS_L10', 0.0),
            consistency_std=features_dict.get('PTS_STD_L10', 0.0),
            minutes_per_game=features_dict.get('MIN_L5', 0.0),
            rest_days=features_dict.get('REST_DAYS', 0)
        )

        # Matchup analysis
        def_pts_allowed = features_dict.get('DEF_PTS_ALLOWED_L5', 110.0)
        defense_quality = self._classify_defense(def_pts_allowed)

        matchup_analysis = MatchupAnalysis(
            opponent_defense_ppg=def_pts_allowed,
            defense_vs_position=features_dict.get('DEF_PTS_VS_POSITION_L5', 55.0),
            defense_quality=defense_quality
        )

        # Pace context
        player_pace = features_dict.get('PLAYER_TEAM_PACE_L5', 100.0)
        opp_pace = features_dict.get('OPP_PACE_L5', 100.0)
        expected_pace = features_dict.get('EXPECTED_GAME_PACE_L5', 100.0)
        expected_poss = features_dict.get('EXPECTED_POSSESSIONS_L5', 70.0)
        pace_env = self._classify_pace(expected_pace)

        pace_context = PaceContext(
            player_team_pace=player_pace,
            opponent_pace=opp_pace,
            expected_game_pace=expected_pace,
            pace_environment=pace_env,
            expected_possessions=expected_poss
        )

        # Prediction interval
        residual_std = self.model_metadata['monte_carlo']['recommended_std']
        lower_90 = predicted_points + self.model_metadata['monte_carlo']['prediction_interval_90']['lower_percentile']
        upper_90 = predicted_points + self.model_metadata['monte_carlo']['prediction_interval_90']['upper_percentile']

        prediction_interval = PredictionInterval(
            lower_90=lower_90,
            upper_90=upper_90,
            model_mae=self.model_metadata['cv_mean_mae']
        )

        # Monte Carlo analysis (if prop line provided)
        monte_carlo_analysis = None
        if prop_line is not None:
            mc_result = self.monte_carlo.simulate_prop(
                predicted_value=predicted_points,
                residual_std=residual_std,
                prop_line=prop_line,
                over_odds=over_odds,
                under_odds=under_odds
            )

            # Determine recommendation
            recommendation = self._get_recommendation(
                mc_result.edge,
                mc_result.confidence_score,
                mc_result.probability_over,
                mc_result.probability_under
            )

            monte_carlo_analysis = MonteCarloAnalysis(
                probability_over=mc_result.probability_over,
                probability_under=mc_result.probability_under,
                edge=mc_result.edge,
                confidence_score=mc_result.confidence_score,
                percentiles=mc_result.percentiles,
                recommendation=recommendation
            )

        # Key factors
        key_factors = self._generate_key_factors(
            features_dict, predicted_points, full_name, position
        )

        # Build final response
        return PredictionResponse(
            player_name=full_name,
            position=position,
            team=current_team,
            opponent=opponent,
            location="HOME" if is_home else "AWAY",
            game_date=str(game_date),
            predicted_points=round(predicted_points, 1),
            player_stats=player_stats,
            matchup_analysis=matchup_analysis,
            pace_context=pace_context,
            prediction_interval=prediction_interval,
            monte_carlo=monte_carlo_analysis,
            key_factors=key_factors
        )

    def _classify_defense(self, pts_allowed: float) -> str:
        if pts_allowed > 115:
            return "Weak"
        elif pts_allowed < 105:
            return "Strong"
        else:
            return "Average"

    def _classify_pace(self, pace: float) -> str:
        if pace > 102:
            return "Fast"
        elif pace < 98:
            return "Slow"
        else:
            return "Average"

    def _get_recommendation(
        self,
        edge: float,
        confidence: float,
        prob_over: float,
        prob_under: float
    ) -> str:
        # Conservative betting recommendation
        # Requires BOTH minimum edge AND minimum confidence (deterministic)

        # Conservative thresholds: edge >= 3% AND confidence >= 55%
        if edge < 3.0 and confidence < 55:
            return "PASS"

        # Determine direction based on probability
        if prob_over > prob_under:
            return "OVER"
        else:
            return "UNDER"

    def _generate_key_factors(
        self,
        features: Dict[str, float],
        predicted: float,
        player_name: str,
        position: str
    ) -> KeyFactors:
       

        # Recent form
        pts_l5 = features.get('PTS_L5', 0.0)
        pts_std = features.get('PTS_STD_L10', 0.0)

        if pts_std < 4:
            consistency = "very consistent"
        elif pts_std < 6:
            consistency = "consistent"
        else:
            consistency = "volatile"

        recent_form = f"{consistency.capitalize()} scorer averaging {pts_l5:.1f} PPG in last 5 games"

        # Matchup favorability
        def_pts = features.get('DEF_PTS_ALLOWED_L5', 110.0)
        def_pos = features.get('DEF_PTS_VS_POSITION_L5', 55.0)

        if def_pts > 115 or def_pos > 60:
            matchup = "Favorable"
        elif def_pts < 105 or def_pos < 50:
            matchup = "Unfavorable"
        else:
            matchup = "Neutral"

        # Pace impact
        expected_pace = features.get('EXPECTED_GAME_PACE_L5', 100.0)
        if expected_pace > 102:
            pace_impact = "Positive"
        elif expected_pace < 98:
            pace_impact = "Negative"
        else:
            pace_impact = "Neutral"

        # Rest impact
        rest_days = features.get('REST_DAYS', 2)
        if rest_days >= 3:
            rest_impact = "Well-rested"
        elif rest_days <= 1:
            rest_impact = "Back-to-back"
        else:
            rest_impact = "Normal"

        return KeyFactors(
            recent_form=recent_form,
            matchup_favorability=matchup,
            pace_impact=pace_impact,
            rest_impact=rest_impact
        )
