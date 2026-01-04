
# Monte Carlo Simulation Engine for NBA Player Props
# Simulates player performance to calculate probabilities and expected value


import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MonteCarloResult:
    # Results from Monte Carlo simulation
    predicted_value: float
    prop_line: float
    probability_over: float
    probability_under: float
    edge: float
    confidence_score: float
    percentiles: Dict[int, float]
    simulations: np.ndarray
    mean: float
    std: float


class MonteCarloSimulator:
    
    # Monte Carlo simulator for player props betting analysis.

    # Uses the XGBoost prediction and model residual distribution to simulate
    # thousands of possible game outcomes and calculate probabilities.
    

    def __init__(self, n_simulations: int = 10000):
        
        # Initialize Monte Carlo simulator.

        # Args:
        #     n_simulations: Number of simulations to run (default: 10,000)
        
        self.n_simulations = n_simulations

    def simulate_prop(
        self,
        predicted_value: float,
        residual_std: float,
        prop_line: float,
        over_odds: int = -110,
        under_odds: int = -110
    ) -> MonteCarloResult:
        
        # Run Monte Carlo simulation for a player prop.

        # Args:
        #     predicted_value: XGBoost model prediction (e.g., 25.3 points)
        #     residual_std: Standard deviation from model residuals (e.g., 6.2)
        #     prop_line: Betting line (e.g., 24.5 points)
        #     over_odds: American odds for over (e.g., -110)
        #     under_odds: American odds for under (e.g., -110)

        # Returns:
        #     MonteCarloResult with probabilities and edge analysis
        
        # Run simulations using normal distribution
        # The model already accounts for all features, so we just add residual noise
        simulations = np.random.normal(
            loc=predicted_value,
            scale=residual_std,
            size=self.n_simulations
        )

        # Calculate probabilities
        prob_over = (simulations > prop_line).mean()
        prob_under = (simulations <= prop_line).mean()

        # Calculate edge (expected value)
        edge_over = self._calculate_edge(prob_over, over_odds)
        edge_under = self._calculate_edge(prob_under, under_odds)

        # Determine best bet
        best_edge = max(edge_over, edge_under)

        # Confidence score based on higher probability - deterministic but vague
        prob_confidence = max(prob_over, prob_under)
        confidence_score = prob_confidence * 100

        # Calculate percentiles for visualization
        percentiles = {
            5: np.percentile(simulations, 5),
            10: np.percentile(simulations, 10),
            25: np.percentile(simulations, 25),
            50: np.percentile(simulations, 50),
            75: np.percentile(simulations, 75),
            90: np.percentile(simulations, 90),
            95: np.percentile(simulations, 95),
        }

        return MonteCarloResult(
            predicted_value=predicted_value,
            prop_line=prop_line,
            probability_over=prob_over,
            probability_under=prob_under,
            edge=best_edge,
            confidence_score=confidence_score,
            percentiles=percentiles,
            simulations=simulations,
            mean=simulations.mean(),
            std=simulations.std()
        )

    def find_best_edges(
        self,
        props_with_predictions: List[Dict]
    ) -> List[Dict]:
        
        # Analyze multiple props and rank by edge.

        # Args:
        #     props_with_predictions: List of dicts with:
        #         - player_name
        #         - predicted_value
        #         - residual_std
        #         - prop_line
        #         - over_odds
        #         - under_odds

        # Returns:
        #     List of props sorted by edge (best first)
        
        results = []

        for prop in props_with_predictions:
            mc_result = self.simulate_prop(
                predicted_value=prop['predicted_value'],
                residual_std=prop['residual_std'],
                prop_line=prop['prop_line'],
                over_odds=prop.get('over_odds', -110),
                under_odds=prop.get('under_odds', -110)
            )

            # Determine bet direction
            bet_direction = "OVER" if mc_result.probability_over > mc_result.probability_under else "UNDER"
            bet_probability = max(mc_result.probability_over, mc_result.probability_under)

            results.append({
                'player_name': prop['player_name'],
                'team': prop.get('team', 'N/A'),
                'opponent': prop.get('opponent', 'N/A'),
                'prop_line': prop['prop_line'],
                'predicted_value': mc_result.predicted_value,
                'bet_direction': bet_direction,
                'probability': bet_probability,
                'edge': mc_result.edge,
                'confidence_score': mc_result.confidence_score,
                'percentiles': mc_result.percentiles,
                'recommended': mc_result.edge > 5.0 and mc_result.confidence_score > 60
            })

        # Sort by edge (highest first)
        results.sort(key=lambda x: x['edge'], reverse=True)

        return results

    def _calculate_edge(self, probability: float, american_odds: int) -> float:
        
        # Calculate expected value (edge) for a bet.

        # Args:
        #     probability: True probability of outcome (0-1)
        #     american_odds: American odds (e.g., -110, +150)

        # Returns:
        #     Edge as percentage (positive = +EV, negative = -EV)
        
        # Convert American odds to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1

        # Calculate expected value
        # EV = (probability * profit) - (1 - probability) * stake
        # For $100 stake:
        profit = (decimal_odds - 1) * 100
        ev = (probability * profit) - ((1 - probability) * 100)

        # Convert to edge percentage
        edge = ev / 100 * 100

        return edge

    def generate_visualization_data(self, mc_result: MonteCarloResult) -> Dict:
        
        # Generate data for frontend visualization (histogram, distribution).

        # Args:
        #     mc_result: MonteCarloResult object

        # Returns:
        #     Dict with histogram bins and distribution data
        
        # Create histogram bins
        hist, bin_edges = np.histogram(mc_result.simulations, bins=50)

        # Calculate where prop line falls
        prop_line_percentile = (
            (mc_result.simulations <= mc_result.prop_line).sum() /
            len(mc_result.simulations) * 100
        )

        return {
            'histogram': {
                'bins': bin_edges.tolist(),
                'counts': hist.tolist(),
            },
            'prop_line': mc_result.prop_line,
            'prop_line_percentile': prop_line_percentile,
            'predicted_value': mc_result.predicted_value,
            'percentiles': mc_result.percentiles,
            'probability_over': mc_result.probability_over,
            'probability_under': mc_result.probability_under,
        }


# Example usage
if __name__ == "__main__":
    # Example: LeBron James predicted 26.5 points, line is 24.5
    simulator = MonteCarloSimulator(n_simulations=10000)

    result = simulator.simulate_prop(
        predicted_value=26.5,
        residual_std=6.2,  # From model metadata
        prop_line=24.5,
        over_odds=-110,
        under_odds=-110
    )

    print(f"Predicted: {result.predicted_value:.1f} points")
    print(f"Line: {result.prop_line:.1f}")
    print(f"Probability OVER: {result.probability_over*100:.1f}%")
    print(f"Probability UNDER: {result.probability_under*100:.1f}%")
    print(f"Edge: {result.edge:+.2f}%")
    print(f"Confidence: {result.confidence_score:.0f}/100")
    print(f"\n90% Range: {result.percentiles[5]:.1f} - {result.percentiles[95]:.1f}")
