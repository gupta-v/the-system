"""Levels, XP curve and Hunter Ranks.

Level cost is measured in full-clear days: a level inside a rank costs
BASE_DAILY_XP * clears_per_level of that rank (1 day at F, a week at A, 10 days at S).
"""

from dataclasses import dataclass

from app.config.game import BASE_DAILY_XP, RANK_TIERS, RankTier
from app.engine.types import HunterRank


def rank_tier_for_level(level: int) -> RankTier:
    if level < 1:
        raise ValueError(f"level must be >= 1, got {level}")
    for tier in RANK_TIERS:
        if tier.max_level is None or level <= tier.max_level:
            return tier
    raise AssertionError("RANK_TIERS must end with an uncapped tier")


def rank_for_level(level: int) -> HunterRank:
    """Hunter Rank the Player is eligible for at this level (Gates may still gate it later)."""
    return rank_tier_for_level(level).rank


def xp_to_next(level: int) -> int:
    """XP needed to go from `level` to `level + 1`."""
    return BASE_DAILY_XP * rank_tier_for_level(level).clears_per_level


def total_xp_for_level(level: int) -> int:
    """Cumulative XP needed to reach `level`, starting from level 1 with 0 XP."""
    return sum(xp_to_next(lvl) for lvl in range(1, level))


@dataclass(frozen=True)
class LevelProgress:
    level: int
    rank: HunterRank
    total_xp: int
    xp_into_level: int
    xp_to_next: int

    @property
    def xp_remaining(self) -> int:
        return self.xp_to_next - self.xp_into_level


def level_progress(total_xp: int) -> LevelProgress:
    total_xp = max(total_xp, 0)
    level = 1
    remaining = total_xp
    while remaining >= (cost := xp_to_next(level)):
        remaining -= cost
        level += 1
    return LevelProgress(
        level=level,
        rank=rank_for_level(level),
        total_xp=total_xp,
        xp_into_level=remaining,
        xp_to_next=cost,
    )
