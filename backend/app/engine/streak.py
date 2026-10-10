"""Streaks: consecutive non-failed days. Recovery Days neither count nor break the streak."""

from collections.abc import Sequence

from app.engine.types import DayStatus


def current_streak(statuses: Sequence[DayStatus]) -> int:
    """`statuses` ordered oldest -> newest. A trailing OPEN day (today) is ignored."""
    streak = 0
    for status in reversed(statuses):
        if status is DayStatus.OPEN:
            continue
        if status is DayStatus.FAILED:
            break
        if status is DayStatus.RECOVERY:
            continue
        streak += 1
    return streak
