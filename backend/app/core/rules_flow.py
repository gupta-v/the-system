"""The System's rules for the Rules scroll. Static: built from app/config, no DB."""

from app.config import game
from app.config.titles import STREAK_MILESTONES
from app.models.rules import DifficultyRuleOut, RankRuleOut, RulesOut, StreakRuleOut


def get_rules() -> RulesOut:
    return RulesOut(
        base_daily_xp=game.BASE_DAILY_XP,
        clear_all_bonus=game.CLEAR_ALL_BONUS,
        recovery_day_xp_factor=game.RECOVERY_DAY_XP_FACTOR,
        gold_per_xp=game.GOLD_PER_XP,
        standard_day_gold=game.STANDARD_DAY_GOLD,
        base_stat_value=game.BASE_STAT_VALUE,
        stat_xp_per_point=game.STAT_XP_PER_POINT,
        strike_window_days=game.STRIKE_WINDOW_DAYS,
        potion_use_window_days=game.POTION_USE_WINDOW_DAYS,
        difficulties=[
            DifficultyRuleOut(
                difficulty=d,
                fail_below=r.fail_threshold,
                xp_multiplier=r.xp_multiplier,
                xp_loss_fraction=r.xp_loss_fraction,
                can_level_down=r.can_level_down,
                max_potions=r.max_potions,
                max_strikes=r.max_strikes,
            )
            for d, r in game.DIFFICULTY_RULES.items()
        ],
        ranks=[
            RankRuleOut(
                rank=t.rank,
                min_level=t.min_level,
                max_level=t.max_level,
                clears_per_level=t.clears_per_level,
                xp_per_level=game.BASE_DAILY_XP * t.clears_per_level,
                intensity=t.intensity,
            )
            for t in game.RANK_TIERS
        ],
        streaks=[
            StreakRuleOut(days=m.days, title=m.title.name, gold=m.gold) for m in STREAK_MILESTONES
        ],
    )
