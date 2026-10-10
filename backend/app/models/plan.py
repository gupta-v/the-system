"""Domain DTOs passed from regimen_service to quest_service (not API models)."""

from dataclasses import dataclass, field
from uuid import UUID

from app.engine.types import DayKind, GoalKind, Stat


@dataclass(frozen=True)
class PlannedGoal:
    goal_id: UUID
    name: str
    stat: Stat
    kind: GoalKind
    target: float  # A-Rank target if scales_with_rank
    f_target: float | None
    scales_with_rank: bool
    unit: str | None
    weight: float
    sets: int | None = None


@dataclass(frozen=True)
class DayPlan:
    title: str
    day_kind: DayKind
    goals: list[PlannedGoal] = field(default_factory=list)
