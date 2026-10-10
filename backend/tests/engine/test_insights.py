from datetime import date

from app.engine.insights import clear_rate, eta_days, longest_streak, next_rank_tier, xp_pace
from app.engine.types import DayStatus, HunterRank

C, P, F, R, OPEN = (
    DayStatus.CLEARED,
    DayStatus.PASSED,
    DayStatus.FAILED,
    DayStatus.RECOVERY,
    DayStatus.OPEN,
)


def test_longest_streak_skips_recovery_and_resets_on_fail() -> None:
    assert longest_streak([C, C, R, P, F, C, OPEN]) == 3
    assert longest_streak([]) == 0


def test_clear_rate_ignores_recovery_and_open() -> None:
    assert clear_rate([C, P, F, R, OPEN]) == 2 / 3
    assert clear_rate([R, OPEN]) is None


def test_pace_counts_only_days_since_awakening() -> None:
    today = date(2026, 10, 14)
    daily = {date(2026, 10, 13): 100, date(2026, 10, 14): 50, date(2026, 9, 1): 999}
    assert xp_pace(daily, today, days=14, since=date(2026, 10, 13)) == 75


def test_eta() -> None:
    assert eta_days(250, 100) == 3
    assert eta_days(0, 0) == 0
    assert eta_days(10, 0) is None


def test_next_rank() -> None:
    tier = next_rank_tier(1)
    assert tier is not None and tier.rank is HunterRank.E
    assert next_rank_tier(65) is None  # S
