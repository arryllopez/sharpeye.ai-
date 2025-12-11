from app.services.feature_builder import PropsFeatures

class PropsBaselineModel:
 # Simple heuristic model for predicting mean and std dev of player props
 #later willbe implementing XGBoos or similar prediction model

    def predict_mean_std(self, stat_type: str, features: PropsFeatures):
        recent = features.recent_avg

        # Simple heuristic mean
        mean = recent * features.pace_factor * features.opponent_defense_scalar

        # Heuristic volatility: ~22% of mean, never below 2
        std = max(2.0, 0.22 * mean)

        return mean, std
