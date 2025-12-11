from dataclasses import dataclass

@dataclass
class AdjustmentContext:
    minutes_projection: float
    pace_factor: float

def apply_bayesian_adjustment(mean: float, std: float, ctx: AdjustmentContext):
    """
    Not full Bayesian math yet — but acts like a correction layer
    based on context (minutes + pace).
    """

    # Minutes effect
    minute_scalar = ctx.minutes_projection / 34.0
    minute_scalar = max(0.75, min(1.25, minute_scalar))

    # Slight pace nudging
    pace_scalar = max(0.9, min(1.1, ctx.pace_factor))

    adjusted_mean = mean * minute_scalar * pace_scalar
    adjusted_std = max(1.5, std * 0.98)

    return adjusted_mean, adjusted_std
