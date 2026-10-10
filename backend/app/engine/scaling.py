"""Rank scaling: Daily Quest targets grow with Hunter Rank (F 20% -> A 100%)."""

from app.config.game import RANK_TIERS
from app.engine.types import HunterRank

_INTENSITY = {tier.rank: tier.intensity for tier in RANK_TIERS}
_F_INTENSITY = _INTENSITY[HunterRank.F]
_A_INTENSITY = _INTENSITY[HunterRank.A]


def scaled_target(a_target: float, rank: HunterRank, f_target: float | None = None) -> float:
    """Target for `rank`, given the A-Rank target (and optionally a custom F-Rank target).

    Without `f_target` the A target is multiplied by the rank's intensity.
    With `f_target` the target is interpolated between the F and A targets.
    """
    intensity = _INTENSITY[rank]
    if f_target is None:
        return round(a_target * intensity, 1)
    t = (intensity - _F_INTENSITY) / (_A_INTENSITY - _F_INTENSITY)
    return round(f_target + (a_target - f_target) * t, 1)
