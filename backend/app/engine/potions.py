"""Recovery Potions: earned by clearing a Recovery Day's Daily Quest, spent to shield another day.

The balance is derived from Daily Quest history (no separate ledger): walk the days in order,
+1 for each cleared planned Recovery Day (up to the carry cap), -1 for each day a Potion was used.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from app.config.game import POTION_USE_WINDOW_DAYS
from app.engine.types import DayKind


@dataclass(frozen=True)
class PotionDay:
    kind: DayKind
    completion: float
    potion_used: bool
    has_goals: bool


def earns_potion(day: PotionDay) -> bool:
    """A planned Recovery Day whose Goals were all done. Potion days and empty days don't earn."""
    return (
        day.kind is DayKind.RECOVERY
        and not day.potion_used
        and day.has_goals
        and day.completion >= 1
    )


def potion_walk(days: Iterable[PotionDay], cap: int) -> tuple[int, list[bool]]:
    """(Potions held now, per day: was a Potion actually earned). `days` oldest -> newest.

    A cleared Recovery Day with the bag already full earns nothing.
    """
    balance, earned = 0, []
    for day in days:
        gained = not day.potion_used and earns_potion(day) and balance < cap
        if day.potion_used:
            balance = max(balance - 1, 0)
        elif gained:
            balance += 1
        earned.append(gained)
    return balance, earned


def potion_balance(days: Iterable[PotionDay], cap: int) -> int:
    """Potions held now. `days` oldest -> newest."""
    return potion_walk(days, cap)[0]


def can_use_potion(used_days: Iterable[date], today: date, limit: int) -> bool:
    """At most `limit` Potions in any POTION_USE_WINDOW_DAYS-day window ending today."""
    since = today - timedelta(days=POTION_USE_WINDOW_DAYS)
    return sum(1 for d in used_days if since < d <= today) < limit
