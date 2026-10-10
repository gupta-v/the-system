"""Stat values (STR / VIT / AGI / INT / PER) derived from stat XP."""

from app.config.game import BASE_STAT_VALUE, STAT_XP_PER_POINT


def stat_value(stat_xp: int) -> int:
    return BASE_STAT_VALUE + max(stat_xp, 0) // STAT_XP_PER_POINT
