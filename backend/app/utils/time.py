"""Game-day helpers. All timestamps are stored in UTC; the game day depends on the
Player's timezone and reset hour (default 04:00, so late nights count for the previous day).
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    return datetime.now(UTC)


def game_date(now: datetime, tz: str, reset_hour: int) -> date:
    local = now.astimezone(ZoneInfo(tz))
    if local.hour < reset_hour:
        return local.date() - timedelta(days=1)
    return local.date()


def next_reset(now: datetime, tz: str, reset_hour: int) -> datetime:
    """UTC moment the current game day ends."""
    zone = ZoneInfo(tz)
    day = game_date(now, tz, reset_hour) + timedelta(days=1)
    return datetime.combine(day, time(hour=reset_hour), tzinfo=zone).astimezone(UTC)


def seconds_until_reset(now: datetime, tz: str, reset_hour: int) -> int:
    return max(int((next_reset(now, tz, reset_hour) - now).total_seconds()), 0)


def day_end(day: date, tz: str, reset_hour: int) -> datetime:
    """UTC moment game day `day` ends (the next reset)."""
    local = datetime.combine(day + timedelta(days=1), time(hour=reset_hour), tzinfo=ZoneInfo(tz))
    return local.astimezone(UTC)
