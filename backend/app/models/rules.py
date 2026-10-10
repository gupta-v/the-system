from pydantic import BaseModel

from app.engine.types import Difficulty, HunterRank


class DifficultyRuleOut(BaseModel):
    difficulty: Difficulty
    fail_below: float  # completion fraction; below this the day fails
    xp_multiplier: float
    xp_loss_fraction: float
    can_level_down: bool
    max_potions: int
    max_strikes: int | None


class RankRuleOut(BaseModel):
    rank: HunterRank
    min_level: int
    max_level: int | None
    clears_per_level: int
    xp_per_level: int
    intensity: float  # Daily Quest target scale (A = 100%)


class StreakRuleOut(BaseModel):
    days: int
    title: str
    gold: int


class RulesOut(BaseModel):
    """The System's rules, straight from app/config so the UI never hardcodes numbers."""

    base_daily_xp: int
    clear_all_bonus: float
    recovery_day_xp_factor: float
    gold_per_xp: float
    standard_day_gold: int
    base_stat_value: int
    stat_xp_per_point: int
    strike_window_days: int
    potion_use_window_days: int
    difficulties: list[DifficultyRuleOut]
    ranks: list[RankRuleOut]
    streaks: list[StreakRuleOut]
