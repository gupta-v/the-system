"""Game tuning constants. See docs/design/game-mechanics.md.

All balance numbers live here so they can be tuned without touching engine logic.
"""

from dataclasses import dataclass

from app.engine.types import Difficulty, HunterRank

# A fully cleared Daily Quest is worth this much base XP, regardless of Goal count.
BASE_DAILY_XP = 100

# "Complete all Goals" bonus, applied to the day's XP when the Daily Quest is cleared.
CLEAR_ALL_BONUS = 0.20

# Goals on a Recovery Day are optional and give reduced XP.
RECOVERY_DAY_XP_FACTOR = 0.5

# Stats start at 10 (as in the series) and gain +1 per this much stat XP.
BASE_STAT_VALUE = 10
STAT_XP_PER_POINT = 50

# Gold earned per XP gained.
GOLD_PER_XP = 0.5

# Standard days are maintenance: no XP, flat Gold once every Goal is done (any difficulty/rank).
STANDARD_DAY_GOLD = 5


@dataclass(frozen=True)
class RankTier:
    rank: HunterRank
    min_level: int
    max_level: int | None  # None = no cap (S)
    clears_per_level: int  # full-clear days needed per level inside this rank
    intensity: float  # Daily Quest target scale; A = 1.0 (anime baseline)


RANK_TIERS: tuple[RankTier, ...] = (
    RankTier(HunterRank.F, 1, 4, 1, 0.20),
    RankTier(HunterRank.E, 5, 11, 2, 0.35),
    RankTier(HunterRank.D, 12, 19, 3, 0.50),
    RankTier(HunterRank.C, 20, 29, 4, 0.65),
    RankTier(HunterRank.B, 30, 44, 6, 0.80),
    RankTier(HunterRank.A, 45, 64, 7, 1.00),
    RankTier(HunterRank.S, 65, None, 10, 1.00),
)


@dataclass(frozen=True)
class DifficultyRules:
    fail_threshold: float  # completion below this fails the day
    xp_multiplier: float
    xp_loss_fraction: float  # share of the current level's requirement lost on a failed day
    can_level_down: bool
    max_potions: int  # Potions you can carry, and the most you can use per POTION_USE_WINDOW_DAYS
    max_strikes: int | None  # strikes within STRIKE_WINDOW_DAYS before the Hunter Rank is sealed


STRIKE_WINDOW_DAYS = 30

# Rating insights: ETA uses the average XP/day over this many days; heatmap shows this many days.
INSIGHT_PACE_DAYS = 14
HEATMAP_DAYS = 84
POTION_USE_WINDOW_DAYS = 14

DIFFICULTY_RULES: dict[Difficulty, DifficultyRules] = {
    Difficulty.AWAKENED: DifficultyRules(0.60, 1.0, 0.0, False, 5, None),
    Difficulty.ELITE: DifficultyRules(0.70, 1.1, 0.05, False, 4, None),
    Difficulty.NATIONAL: DifficultyRules(0.80, 1.2, 0.10, False, 3, None),
    Difficulty.REAWAKENED: DifficultyRules(0.90, 1.3, 0.15, False, 2, None),
    Difficulty.MONARCH: DifficultyRules(1.00, 1.5, 0.20, True, 1, 3),
}

# Penalty Quest issued for a failed Daily Quest; must be cleared before the next game day ends.
PENALTY_QUESTS: dict[Difficulty, str] = {
    Difficulty.AWAKENED: "Survive: 20 push-ups, 20 squats, 1 km walk.",
    Difficulty.ELITE: "Survive: 30 push-ups, 30 squats, 2 km walk.",
    Difficulty.NATIONAL: "Survive: 50 push-ups, 50 squats, 3 km run.",
    Difficulty.REAWAKENED: "Survive: 75 push-ups, 75 squats, 4 km run.",
    Difficulty.MONARCH: "Survive: 100 push-ups, 100 sit-ups, 100 squats, 5 km run.",
}
