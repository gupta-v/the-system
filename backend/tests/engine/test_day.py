import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.engine.day import GoalProgress, evaluate_day, goal_shares
from app.engine.types import DayKind, DayStatus, Difficulty, GoalKind, Stat


def check(stat: Stat, done: bool, weight: float = 1.0) -> GoalProgress:
    return GoalProgress(stat=stat, kind=GoalKind.CHECK, progress=1 if done else 0, weight=weight)


def numeric(stat: Stat, progress: float, target: float, weight: float = 1.0) -> GoalProgress:
    return GoalProgress(
        stat=stat, kind=GoalKind.NUMERIC, progress=progress, target=target, weight=weight
    )


class TestGoalFraction:
    def test_check(self) -> None:
        assert check(Stat.STR, True).fraction() == 1.0
        assert check(Stat.STR, False).fraction() == 0.0

    def test_numeric_partial(self) -> None:
        assert numeric(Stat.STR, 50, 100).fraction() == 0.5

    def test_numeric_clamped(self) -> None:
        assert numeric(Stat.STR, 150, 100).fraction() == 1.0
        assert numeric(Stat.STR, -5, 100).fraction() == 0.0

    def test_numeric_zero_target_counts_as_done(self) -> None:
        assert numeric(Stat.STR, 0, 0).fraction() == 1.0


def test_goal_shares_split_the_daily_budget() -> None:
    assert goal_shares([check(Stat.STR, True)] * 4) == [25, 25, 25, 25]
    assert goal_shares([numeric(Stat.AGI, 1, 3)]) == [33]  # floored
    assert goal_shares([check(Stat.STR, True, weight=0)]) == [0]


def test_full_clear_is_100_base_xp_for_any_goal_count() -> None:
    for n in range(1, 13):
        r = evaluate_day([check(Stat.STR, True)] * n, Difficulty.AWAKENED)
        assert r.base_xp == 100 and r.xp == 120, n


def test_full_clear_awakened() -> None:
    goals = [check(s, True) for s in (Stat.STR, Stat.VIT, Stat.AGI, Stat.INT)]
    r = evaluate_day(goals, Difficulty.AWAKENED)
    assert r.status is DayStatus.CLEARED
    assert r.completion == 1.0
    assert r.base_xp == 100
    assert r.xp == 120  # +20% clear-all bonus
    assert r.gold == 60
    assert r.stat_xp == {Stat.STR: 25, Stat.VIT: 25, Stat.AGI: 25, Stat.INT: 25}


def test_goal_count_cannot_farm_xp() -> None:
    few = evaluate_day([check(Stat.STR, True)] * 2, Difficulty.AWAKENED)
    many = evaluate_day([check(Stat.STR, True)] * 10, Difficulty.AWAKENED)
    assert few.xp == many.xp == 120


@pytest.mark.parametrize(
    ("difficulty", "xp"),
    [
        (Difficulty.AWAKENED, 120),
        (Difficulty.ELITE, 132),
        (Difficulty.NATIONAL, 144),
        (Difficulty.MONARCH, 180),
    ],
)
def test_difficulty_multiplier_on_clear(difficulty: Difficulty, xp: int) -> None:
    assert evaluate_day([check(Stat.STR, True)], difficulty).xp == xp


@pytest.mark.parametrize(
    ("difficulty", "completion", "status"),
    [
        (Difficulty.AWAKENED, 0.6, DayStatus.PASSED),
        (Difficulty.AWAKENED, 0.5, DayStatus.FAILED),
        (Difficulty.ELITE, 0.7, DayStatus.PASSED),
        (Difficulty.ELITE, 0.6, DayStatus.FAILED),
        (Difficulty.NATIONAL, 0.8, DayStatus.PASSED),
        (Difficulty.NATIONAL, 0.7, DayStatus.FAILED),
        (Difficulty.REAWAKENED, 0.9, DayStatus.PASSED),
        (Difficulty.REAWAKENED, 0.8, DayStatus.FAILED),
        (Difficulty.MONARCH, 0.9, DayStatus.FAILED),
    ],
)
def test_fail_thresholds(difficulty: Difficulty, completion: float, status: DayStatus) -> None:
    r = evaluate_day([numeric(Stat.STR, completion * 100, 100)], difficulty)
    assert r.status is status
    assert r.completion == pytest.approx(completion)


def test_partial_day_gets_no_clear_bonus() -> None:
    goals = [check(Stat.STR, True), check(Stat.INT, True), check(Stat.PER, False)]
    r = evaluate_day(goals, Difficulty.AWAKENED)
    assert r.status is DayStatus.PASSED
    assert r.base_xp == 66  # 33 + 33
    assert r.xp == 66
    assert Stat.PER not in r.stat_xp


def test_weights_shift_xp_between_goals() -> None:
    goals = [check(Stat.STR, True, weight=3), check(Stat.INT, True, weight=1)]
    r = evaluate_day(goals, Difficulty.AWAKENED)
    assert r.stat_xp == {Stat.STR: 75, Stat.INT: 25}


def test_recovery_day_halves_xp_and_never_fails() -> None:
    goals = [check(Stat.VIT, True), check(Stat.STR, False)]
    r = evaluate_day(goals, Difficulty.MONARCH, DayKind.RECOVERY)
    assert r.status is DayStatus.RECOVERY
    assert r.xp == 37  # floor(50 * 1.5 * 0.5)


def test_empty_day_is_neutral_with_no_xp() -> None:
    r = evaluate_day([], Difficulty.MONARCH)
    assert (r.status, r.completion, r.xp, r.gold) == (DayStatus.RECOVERY, 1.0, 0, 0)


goal_strategy = st.builds(
    GoalProgress,
    stat=st.sampled_from(Stat),
    kind=st.sampled_from(GoalKind),
    progress=st.floats(min_value=0, max_value=200),
    target=st.floats(min_value=1, max_value=100),
    weight=st.floats(min_value=0.1, max_value=10),
)


@given(st.lists(goal_strategy, min_size=1, max_size=12), st.sampled_from(Difficulty))
def test_evaluate_day_invariants(goals: list[GoalProgress], difficulty: Difficulty) -> None:
    r = evaluate_day(goals, difficulty)
    assert 0.0 <= r.completion <= 1.0
    assert 0 <= r.base_xp <= 100
    assert sum(r.stat_xp.values()) == r.base_xp
    assert r.xp >= r.base_xp  # all multipliers are >= 1 outside Recovery Days
    assert r.gold == r.xp // 2


def test_check_goal_split_into_sets_counts_partially() -> None:
    half = GoalProgress(stat=Stat.VIT, kind=GoalKind.CHECK, progress=0.5)
    assert half.fraction() == 0.5
    assert evaluate_day([half], Difficulty.AWAKENED).base_xp == 50
