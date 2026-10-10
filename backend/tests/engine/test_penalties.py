from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.engine.penalties import active_strikes, is_rank_sealed, xp_penalty
from app.engine.progression import level_progress
from app.engine.types import Difficulty


def test_awakened_never_loses_xp() -> None:
    assert xp_penalty(5_000, Difficulty.AWAKENED) == 0


def test_national_loses_share_of_level_progress() -> None:
    # Level 5 (E, 200 per level) with 150 into the level -> lose 10% of 150.
    assert xp_penalty(400 + 150, Difficulty.NATIONAL) == -15


def test_national_at_level_start_loses_nothing() -> None:
    assert xp_penalty(400, Difficulty.NATIONAL) == 0


def test_monarch_loses_share_of_full_level_and_can_level_down() -> None:
    total = 400 + 10  # level 5, 10 into a 200 XP level
    loss = xp_penalty(total, Difficulty.MONARCH)
    assert loss == -40
    assert level_progress(total + loss).level == 4


def test_monarch_cannot_go_below_zero() -> None:
    assert xp_penalty(5, Difficulty.MONARCH) == -5
    assert xp_penalty(0, Difficulty.MONARCH) == 0


@given(st.integers(min_value=0, max_value=100_000))
def test_national_never_drops_a_level(total_xp: int) -> None:
    loss = xp_penalty(total_xp, Difficulty.NATIONAL)
    assert loss <= 0
    assert level_progress(total_xp + loss).level == level_progress(total_xp).level


def test_active_strikes_uses_30_day_window() -> None:
    today = date(2026, 10, 9)
    failed = [
        today,
        today - timedelta(days=29),
        today - timedelta(days=30),
        today + timedelta(days=1),
    ]
    assert active_strikes(failed, today) == 2


def test_rank_sealed_only_on_hunter() -> None:
    assert is_rank_sealed(3, Difficulty.MONARCH)
    assert not is_rank_sealed(2, Difficulty.MONARCH)
    assert not is_rank_sealed(99, Difficulty.NATIONAL)
