"""Penalty Zone consequences of a failed Daily Quest."""

import math
from collections.abc import Iterable
from datetime import date, timedelta

from app.config.game import DIFFICULTY_RULES, STRIKE_WINDOW_DAYS
from app.engine.progression import level_progress
from app.engine.types import Difficulty


def xp_penalty(total_xp: int, difficulty: Difficulty) -> int:
    """XP lost for a failed day (returned as a non-positive number).

    Awakened: nothing. Elite/National/Reawakened: a share of progress inside the current level,
    so the level is kept. Monarch: a share of the whole level's requirement, which can drop
    the Player a level.
    """
    rules = DIFFICULTY_RULES[difficulty]
    if rules.xp_loss_fraction == 0:
        return 0
    progress = level_progress(total_xp)
    base = progress.xp_to_next if rules.can_level_down else progress.xp_into_level
    loss = min(math.floor(base * rules.xp_loss_fraction), progress.total_xp)
    return -loss


def active_strikes(failed_days: Iterable[date], today: date) -> int:
    window_start = today - timedelta(days=STRIKE_WINDOW_DAYS)
    return sum(1 for d in failed_days if window_start < d <= today)


def is_rank_sealed(strikes: int, difficulty: Difficulty) -> bool:
    max_strikes = DIFFICULTY_RULES[difficulty].max_strikes
    return max_strikes is not None and strikes >= max_strikes
