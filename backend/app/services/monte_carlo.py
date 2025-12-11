import numpy as np
from app.utils.distributions import sample_normal, sample_poisson, choose_distribution
from app.utils.calibration import clamp_prob

def run_props_monte_carlo(stat_type: str, mean: float, std: float, line: float, n: int):
    dist = choose_distribution(stat_type)

    if dist == "poisson":
        samples = sample_poisson(mean, n)
    else:
        samples = sample_normal(mean, std, n)
        # Stats can't be negative
        samples = np.clip(samples, 0, None)

    over = float(np.mean(samples > line))
    under = 1.0 - over

    return clamp_prob(over), clamp_prob(under), samples.tolist()[:250]
