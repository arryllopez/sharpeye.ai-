#keeping probabilities within [0,1] range to minimize sampling and numerical noise

def clamp_prob(p: float) -> float:
    return max(0.0, min(1.0, p))
