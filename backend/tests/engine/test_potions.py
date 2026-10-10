from datetime import date, timedelta

from app.engine.potions import PotionDay, can_use_potion, earns_potion, potion_balance, potion_walk
from app.engine.types import DayKind

REC = DayKind.RECOVERY
TRN = DayKind.TRAINING


def day(kind: DayKind = REC, completion: float = 1.0, used: bool = False, goals: bool = True):
    return PotionDay(kind=kind, completion=completion, potion_used=used, has_goals=goals)


def test_only_cleared_recovery_days_earn() -> None:
    assert earns_potion(day())
    assert not earns_potion(day(completion=0.9))
    assert not earns_potion(day(kind=TRN))
    assert not earns_potion(day(goals=False))  # empty Recovery Day: nothing to clear
    assert not earns_potion(day(used=True))  # a Potion day is Recovery but doesn't earn


def test_balance_earn_spend_and_cap() -> None:
    assert potion_balance([], cap=4) == 0
    assert potion_balance([day(), day(), day(kind=TRN, used=True)], cap=4) == 1
    assert potion_balance([day()] * 5, cap=2) == 2  # carry cap
    assert potion_balance([day(), day(kind=TRN, used=True), day(kind=TRN, used=True)], cap=4) == 0


def test_use_limit_per_window() -> None:
    today = date(2026, 10, 20)
    used = [today - timedelta(days=d) for d in (1, 5, 13)]
    assert not can_use_potion(used, today, limit=3)  # 3 used in the last 14 days
    assert can_use_potion(used, today, limit=4)
    assert can_use_potion([today - timedelta(days=14)], today, limit=1)  # fell out of the window


def test_walk_flags_only_days_that_added_a_potion() -> None:
    held, earned = potion_walk([day(), day(), day(), day(kind=TRN, used=True), day()], cap=2)
    assert held == 2
    assert earned == [True, True, False, False, True]  # 3rd: bag full; 5th: room after using one
