"""Daily Quest evaluation: Goal XP, completion and day status."""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.config.game import (
    BASE_DAILY_XP,
    CLEAR_ALL_BONUS,
    DIFFICULTY_RULES,
    GOLD_PER_XP,
    RECOVERY_DAY_XP_FACTOR,
    STANDARD_DAY_GOLD,
)
from app.engine.types import DayKind, DayStatus, Difficulty, GoalKind, Stat


@dataclass(frozen=True)
class GoalProgress:
    stat: Stat
    kind: GoalKind
    progress: float  # CHECK: 0 or 1. NUMERIC: amount done.
    target: float = 1.0
    weight: float = 1.0  # share of the day's BASE_DAILY_XP

    def fraction(self) -> float:
        if self.kind is GoalKind.CHECK:
            # 0 or 1, or k/sets when the Goal is split into sets.
            return min(max(self.progress, 0.0), 1.0)
        if self.target <= 0:
            return 1.0
        return min(max(self.progress / self.target, 0.0), 1.0)


@dataclass(frozen=True)
class DayResult:
    status: DayStatus
    completion: float  # weighted 0..1
    base_xp: int  # before multipliers
    xp: int  # final XP awarded
    gold: int
    stat_xp: dict[Stat, int] = field(default_factory=dict)


def goal_shares(goals: Sequence[GoalProgress]) -> list[int]:
    """Each Goal's whole-XP share of BASE_DAILY_XP (by weight x progress).

    Largest remainder: shares sum to floor(BASE_DAILY_XP * completion), so a full clear is always
    exactly BASE_DAILY_XP however many Goals there are (6 Goals: 17+17+17+17+16+16, not 6x16).
    """
    total_weight = sum(g.weight for g in goals)
    if total_weight <= 0:
        return [0] * len(goals)
    exact = [BASE_DAILY_XP * g.weight / total_weight * g.fraction() for g in goals]
    shares = [math.floor(round(e, 6)) for e in exact]
    owed = math.floor(round(sum(exact), 6)) - sum(shares)
    by_remainder = sorted(range(len(goals)), key=lambda i: exact[i] - shares[i], reverse=True)
    for i in by_remainder[:owed]:
        shares[i] += 1
    return shares


def evaluate_day(
    goals: Sequence[GoalProgress],
    difficulty: Difficulty,
    day_kind: DayKind = DayKind.TRAINING,
) -> DayResult:
    rules = DIFFICULTY_RULES[difficulty]
    total_weight = sum(g.weight for g in goals)

    stat_xp: dict[Stat, int] = {}
    shares = goal_shares(goals)
    base_xp = sum(shares)
    for goal, earned in zip(goals, shares, strict=True):
        if earned:
            stat_xp[goal.stat] = stat_xp.get(goal.stat, 0) + earned

    if total_weight > 0:
        completion = round(sum(g.weight * g.fraction() for g in goals) / total_weight, 6)
    else:
        completion = 1.0

    if day_kind is DayKind.STANDARD:
        # Maintenance day: never fails, streak kept; flat Gold for a full clear, no XP.
        gold = STANDARD_DAY_GOLD if goals and completion >= 1.0 else 0
        return DayResult(DayStatus.RECOVERY, completion, base_xp=0, xp=0, gold=gold)

    if day_kind is DayKind.RECOVERY:
        status = DayStatus.RECOVERY
    elif not goals:
        status = DayStatus.RECOVERY  # nothing to do: can't fail, streak kept
    elif completion >= 1.0:
        status = DayStatus.CLEARED
    elif completion < rules.fail_threshold:
        status = DayStatus.FAILED
    else:
        status = DayStatus.PASSED

    multiplier = rules.xp_multiplier
    if status is DayStatus.CLEARED:
        multiplier *= 1 + CLEAR_ALL_BONUS
    if day_kind is DayKind.RECOVERY:
        multiplier *= RECOVERY_DAY_XP_FACTOR
    # Round first so float noise (100 * 1.5 * 1.2 = 179.999...) doesn't cost a point.
    xp = math.floor(round(base_xp * multiplier, 6))

    return DayResult(
        status=status,
        completion=completion,
        base_xp=base_xp,
        xp=xp,
        gold=math.floor(xp * GOLD_PER_XP),
        stat_xp=stat_xp,
    )
