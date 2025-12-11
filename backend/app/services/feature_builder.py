#where historical dta will be fetched and features will be built

from dataclasses import dataclass
from typing import Optional

@dataclass
class PropsFeatures:
    recent_avg: float
    minutes_projection: float
    pace_factor: float
    opponent_defense_scalar: float

def build_props_features(
    recent_avg: Optional[float],
    minutes_projection: float,
    pace_factor: float,
    opponent: str
) -> PropsFeatures:
    # If recent_avg is not provided, use a safe generic baseline
    base_recent = recent_avg if recent_avg is not None else 20.0

    # Placeholder: 1.0 = neutral.
    # Later: look up opponent defense from data and scale down/up.
    opponent_defense_scalar = 1.0

    return PropsFeatures(
        recent_avg=base_recent,
        minutes_projection=minutes_projection,
        pace_factor=pace_factor,
        opponent_defense_scalar=opponent_defense_scalar
    )
