import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.engine.progression import (
    level_progress,
    rank_for_level,
    total_xp_for_level,
    xp_to_next,
)
from app.engine.types import HunterRank


@pytest.mark.parametrize(
    ("level", "rank"),
    [
        (1, HunterRank.F),
        (4, HunterRank.F),
        (5, HunterRank.E),
        (11, HunterRank.E),
        (12, HunterRank.D),
        (20, HunterRank.C),
        (30, HunterRank.B),
        (44, HunterRank.B),
        (45, HunterRank.A),
        (64, HunterRank.A),
        (65, HunterRank.S),
        (500, HunterRank.S),
    ],
)
def test_rank_for_level(level: int, rank: HunterRank) -> None:
    assert rank_for_level(level) is rank


def test_rank_for_level_rejects_level_below_one() -> None:
    with pytest.raises(ValueError):
        rank_for_level(0)


@pytest.mark.parametrize(
    ("level", "cost"),
    [(1, 100), (4, 100), (5, 200), (12, 300), (20, 400), (30, 600), (45, 700), (65, 1000)],
)
def test_xp_to_next_matches_rank_table(level: int, cost: int) -> None:
    assert xp_to_next(level) == cost


@pytest.mark.parametrize(
    ("rank_start_level", "cumulative_xp"),
    [(1, 0), (5, 400), (12, 1_800), (20, 4_200), (30, 8_200), (45, 17_200), (65, 31_200)],
)
def test_total_xp_for_rank_thresholds(rank_start_level: int, cumulative_xp: int) -> None:
    # docs/design/game-mechanics.md §4: cumulative XP to S = 31,200.
    assert total_xp_for_level(rank_start_level) == cumulative_xp


def test_level_progress_at_zero() -> None:
    p = level_progress(0)
    assert (p.level, p.rank, p.xp_into_level, p.xp_to_next, p.xp_remaining) == (
        1,
        HunterRank.F,
        0,
        100,
        100,
    )


def test_level_progress_one_clear_at_f_is_one_level() -> None:
    assert level_progress(100).level == 2
    assert level_progress(99).level == 1


def test_level_progress_inside_level() -> None:
    p = level_progress(400 + 150)  # level 5 (E) with 150/200
    assert (p.level, p.rank, p.xp_into_level, p.xp_to_next) == (5, HunterRank.E, 150, 200)


def test_level_progress_clamps_negative_xp() -> None:
    p = level_progress(-50)
    assert (p.level, p.total_xp, p.xp_into_level) == (1, 0, 0)


@given(st.integers(min_value=0, max_value=200_000))
def test_level_progress_is_consistent(total_xp: int) -> None:
    p = level_progress(total_xp)
    assert 0 <= p.xp_into_level < p.xp_to_next
    assert total_xp_for_level(p.level) + p.xp_into_level == total_xp
    assert p.rank is rank_for_level(p.level)


@given(st.integers(min_value=0, max_value=100_000), st.integers(min_value=0, max_value=5_000))
def test_level_never_decreases_when_xp_grows(total_xp: int, gain: int) -> None:
    assert level_progress(total_xp + gain).level >= level_progress(total_xp).level
