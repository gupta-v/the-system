"""Rating insights: pace, ETAs, clear rate, records. Pure functions over Daily Quest history."""

import math
from collections.abc import Mapping, Sequence
from datetime import date, timedelta

from app.config.game import RANK_TIERS, RankTier
from app.engine.types import DayStatus


def longest_streak(statuses: Sequence[DayStatus]) -> int:
    """Best run of non-failed days, oldest -> newest. Same rules as `current_streak`."""
    best = run = 0
    for status in statuses:
        if status is DayStatus.FAILED:
            run = 0
        elif status in (DayStatus.CLEARED, DayStatus.PASSED):
            run += 1
            best = max(best, run)
    return best


def clear_rate(statuses: Sequence[DayStatus]) -> float | None:
    """Share of judged days (cleared, passed, failed) that didn't fail. None: nothing judged yet."""
    judged = [s for s in statuses if s in (DayStatus.CLEARED, DayStatus.PASSED, DayStatus.FAILED)]
    if not judged:
        return None
    return sum(s is not DayStatus.FAILED for s in judged) / len(judged)


def xp_pace(daily_xp: Mapping[date, int], today: date, days: int, since: date) -> float:
    """Average net XP per day over the last `days` game days (fewer if Awakened recently)."""
    start = max(today - timedelta(days=days - 1), since)
    span = (today - start).days + 1
    return sum(xp for d, xp in daily_xp.items() if start <= d <= today) / span


def eta_days(xp_needed: int, pace: float) -> int | None:
    """Days to earn `xp_needed` at `pace`. None when the pace is zero or negative."""
    if xp_needed <= 0:
        return 0
    return math.ceil(xp_needed / pace) if pace > 0 else None


def next_rank_tier(level: int) -> RankTier | None:
    return next((t for t in RANK_TIERS if t.min_level > level), None)
