import pytest

from app.engine.scaling import scaled_target
from app.engine.stats import stat_value
from app.engine.streak import current_streak
from app.engine.types import DayStatus, HunterRank

S = DayStatus


@pytest.mark.parametrize(
    ("rank", "pushups", "run_km"),
    [
        (HunterRank.F, 20, 2.0),
        (HunterRank.E, 35, 3.5),
        (HunterRank.D, 50, 5.0),
        (HunterRank.C, 65, 6.5),
        (HunterRank.B, 80, 8.0),
        (HunterRank.A, 100, 10.0),
        (HunterRank.S, 100, 10.0),
    ],
)
def test_default_daily_quest_scaling(rank: HunterRank, pushups: int, run_km: float) -> None:
    assert scaled_target(100, rank) == pushups
    assert scaled_target(10, rank) == run_km


def test_custom_f_target_interpolates() -> None:
    assert scaled_target(60, HunterRank.F, f_target=20) == 20
    assert scaled_target(60, HunterRank.A, f_target=20) == 60
    assert scaled_target(60, HunterRank.D, f_target=20) == 35  # 37.5% of the way


def test_stat_value() -> None:
    assert stat_value(0) == 10
    assert stat_value(49) == 10
    assert stat_value(50) == 11
    assert stat_value(-100) == 10


@pytest.mark.parametrize(
    ("statuses", "streak"),
    [
        ([], 0),
        ([S.CLEARED, S.PASSED, S.CLEARED], 3),
        ([S.CLEARED, S.FAILED, S.CLEARED, S.PASSED], 2),
        ([S.CLEARED, S.RECOVERY, S.CLEARED], 2),
        ([S.CLEARED, S.CLEARED, S.OPEN], 2),
        ([S.CLEARED, S.FAILED], 0),
    ],
)
def test_current_streak(statuses: list[DayStatus], streak: int) -> None:
    assert current_streak(statuses) == streak
