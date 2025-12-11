import numpy as np

def sample_normal(mean: float, std: float, n: int) -> np.ndarray:
    std = max(std, 1e-6)  # avoid zero std
    return np.random.normal(loc=mean, scale=std, size=n)

def sample_poisson(lam: float, n: int) -> np.ndarray:
    lam = max(lam, 1e-6)  # avoid zero rate
    return np.random.poisson(lam=lam, size=n)

def choose_distribution(stat_type: str):
    # Simple rule: count stats → Poisson, others → Normal
    if stat_type in {"shots", "goals", "saves"}:
        return "poisson"
    return "normal"
