from datetime import date, time
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.config.presets import EXTRA_GOAL_CODES, RegimenPath
from app.engine.types import DayKind, Difficulty, GoalKind, Stat
from app.models.player import CheckIns
from app.models.types import (
    DayTypeName,
    DisplayName,
    GoalName,
    Id,
    ResetHour,
    Sets,
    Target,
    Timezone,
    Unit,
    Weekday,
    Weight,
)

# --- Goals --------------------------------------------------------------------------------


class GoalIn(BaseModel):
    name: GoalName
    stat: Stat
    kind: GoalKind
    target: Target = 1.0  # A-Rank target when scales_with_rank
    f_target: Target | None = None
    unit: Unit | None = None
    scales_with_rank: bool = False
    weight: Weight = 1.0
    sets: Sets | None = None

    @model_validator(mode="after")
    def _check_targets(self) -> Self:
        if self.kind is GoalKind.CHECK and self.target != 1.0:
            raise ValueError("check Goals have target 1")
        if self.f_target is not None and not self.scales_with_rank:
            raise ValueError("f_target needs scales_with_rank")
        if self.f_target is not None and self.f_target > self.target:
            raise ValueError("f_target must not exceed the A-Rank target")
        return self


class GoalPatch(BaseModel):
    """Partial update; kind can't change (would break logged history)."""

    name: GoalName | None = None
    stat: Stat | None = None
    target: Target | None = None
    f_target: Target | None = None
    unit: Unit | None = None
    scales_with_rank: bool | None = None
    weight: Weight | None = None
    sets: Sets | None = None  # null clears


class GoalOut(BaseModel):
    id: UUID
    name: str
    stat: Stat
    kind: GoalKind
    target: float
    f_target: float | None
    unit: str | None
    scales_with_rank: bool
    weight: float
    sets: int | None
    archived: bool


# --- Regimen ------------------------------------------------------------------------------


class DayTypeGoalIn(BaseModel):
    goal_id: Id
    target_override: Target | None = None


def _unique_goals(goals: list[DayTypeGoalIn]) -> list[DayTypeGoalIn]:
    ids = [g.goal_id for g in goals]
    if len(set(ids)) != len(ids):
        raise ValueError("a Goal can appear only once per Day Type")
    return goals


class DayTypeIn(BaseModel):
    name: DayTypeName
    goals: Annotated[list[DayTypeGoalIn], AfterValidator(_unique_goals), Field(max_length=20)] = []


class EditScope(StrEnum):
    THIS_WEEK = "this_week"
    FROM_NOW_ON = "from_now_on"


MAX_ROUTINES_PER_DAY = 2

DayRoutines = Annotated[list[DayTypeName], Field(max_length=MAX_ROUTINES_PER_DAY)]


class RegimenIn(BaseModel):
    """Full weekly structure. `day_types` are the Routines (sets of Goals); for Monday..Sunday,
    `day_kinds` is the day type and `week` lists up to 2 Routine names (merged into the quest)."""

    day_types: Annotated[list[DayTypeIn], Field(min_length=1, max_length=12)]
    day_kinds: Annotated[list[DayKind], Field(min_length=7, max_length=7)]
    week: Annotated[list[DayRoutines], Field(min_length=7, max_length=7)]
    scope: EditScope = EditScope.FROM_NOW_ON

    @model_validator(mode="after")
    def _check_structure(self) -> Self:
        names = [d.name for d in self.day_types]
        if len(set(names)) != len(names):
            raise ValueError("Day Type names must be unique")
        if any(len(set(day)) != len(day) for day in self.week):
            raise ValueError("a Routine can appear only once per day")
        unknown = {name for day in self.week for name in day} - set(names)
        if unknown:
            raise ValueError(f"unknown Routines in week: {sorted(unknown)}")
        if all(kind is DayKind.RECOVERY for kind in self.day_kinds):
            raise ValueError("a Regimen needs at least one non-Recovery day per week")
        if any(
            k is DayKind.TRAINING and not day
            for k, day in zip(self.day_kinds, self.week, strict=True)
        ):
            raise ValueError("every Training day needs at least one Routine")
        if any(
            k is DayKind.STANDARD and day for k, day in zip(self.day_kinds, self.week, strict=True)
        ):
            raise ValueError("Standard days run the Default Routine; pick no Routines")
        return self


class DayTypeGoalOut(BaseModel):
    goal_id: UUID
    name: str
    stat: Stat
    target: float
    unit: str | None
    target_override: float | None


class DayTypeOut(BaseModel):
    name: str
    goals: list[DayTypeGoalOut]


class RegimenOut(BaseModel):
    id: UUID
    name: str
    path: str
    daily_minutes: int
    effective_from: date
    day_types: list[DayTypeOut]
    day_kinds: list[DayKind]  # Monday..Sunday
    week: list[list[str]]  # Routine names per weekday


# --- Awakening (onboarding + Regimen interview, regimen.md §2) -----------------------------


def _unique_sorted(days: list[int]) -> list[int]:
    return sorted(set(days))


Weekdays = Annotated[list[Weekday], AfterValidator(_unique_sorted)]


def _known_extras(extras: list[str]) -> list[str]:
    unknown = set(extras) - set(EXTRA_GOAL_CODES)
    if unknown:
        raise ValueError(f"unknown extras: {sorted(unknown)}; allowed: {list(EXTRA_GOAL_CODES)}")
    return list(dict.fromkeys(extras))


class AwakeningIn(BaseModel):
    """Every field has a default, so `{}` is a valid Awakening."""

    display_name: DisplayName | None = None
    timezone: Timezone = "UTC"
    reset_hour: ResetHour = 4
    difficulty: Difficulty = Difficulty.AWAKENED
    day_start: time = time(7, 0)
    check_ins: CheckIns = "both"

    path: RegimenPath = RegimenPath.BALANCED
    training_days: Weekdays = [0, 2, 4]
    recovery_days: Weekdays = [6]
    daily_minutes: Literal[15, 30, 60, 90] = 30
    extras: Annotated[list[str], AfterValidator(_known_extras)] = []

    @model_validator(mode="after")
    def _check_days(self) -> Self:
        if set(self.training_days) & set(self.recovery_days):
            raise ValueError("a day can't be both Training and Recovery")
        if len(self.recovery_days) == 7:
            raise ValueError("a Regimen needs at least one non-Recovery day per week")
        return self
