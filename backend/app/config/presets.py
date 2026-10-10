"""Regimen interview presets (docs/design/regimen.md §2-3).

Targets are A-Rank values; Goals with `scales_with_rank` are scaled down by Hunter Rank
(F 20% -> A 100%), so the default Training Day is the System's own Daily Quest:
100 push-ups, 100 sit-ups, 100 squats, 10 km run.
"""

from dataclasses import dataclass
from enum import StrEnum

from app.engine.types import DayKind, GoalKind, Stat


@dataclass(frozen=True)
class GoalPreset:
    name: str
    stat: Stat
    kind: GoalKind
    target: float = 1.0
    unit: str | None = None
    scales_with_rank: bool = False


GOAL_LIBRARY: dict[str, GoalPreset] = {
    "pushups": GoalPreset("Push-ups", Stat.STR, GoalKind.NUMERIC, 100, "reps", True),
    "situps": GoalPreset("Sit-ups", Stat.STR, GoalKind.NUMERIC, 100, "reps", True),
    "squats": GoalPreset("Squats", Stat.STR, GoalKind.NUMERIC, 100, "reps", True),
    "run": GoalPreset("Run", Stat.AGI, GoalKind.NUMERIC, 10, "km", True),
    "strength_workout": GoalPreset("Strength Workout", Stat.STR, GoalKind.CHECK),
    "steps": GoalPreset("Walk", Stat.AGI, GoalKind.NUMERIC, 6000, "steps"),
    "stretch": GoalPreset("Stretch", Stat.AGI, GoalKind.NUMERIC, 10, "min"),
    "reading": GoalPreset("Read", Stat.INT, GoalKind.NUMERIC, 20, "pages"),
    "study": GoalPreset("Deep Work", Stat.INT, GoalKind.NUMERIC, 120, "min", True),
    "water": GoalPreset("Water", Stat.VIT, GoalKind.NUMERIC, 3, "L"),
    "sleep": GoalPreset("Sleep last night", Stat.VIT, GoalKind.NUMERIC, 7, "hrs"),
    "meditation": GoalPreset("Meditation", Stat.PER, GoalKind.NUMERIC, 10, "min"),
    "no_sugar": GoalPreset("No sugar", Stat.PER, GoalKind.CHECK),
}

# Quick-add chips in interview question 7.
EXTRA_GOAL_CODES = ("water", "sleep", "reading", "meditation", "no_sugar", "steps")


class RegimenPath(StrEnum):
    BALANCED = "balanced"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    SCHOLAR = "scholar"
    CUSTOM = "custom"  # starts as Balanced; the Player edits from there


DAY_TYPE_NAMES: dict[DayKind, str] = {
    DayKind.TRAINING: "Training Day",
    DayKind.STANDARD: "Standard Day",
    DayKind.RECOVERY: "Recovery Day",
}
# Runs on every Standard day (days with no Routines picked). Awakening fills it with these Goals
# plus the extras, and also adds it as 2nd Routine on Training/Recovery days.
DEFAULT_ROUTINE_NAME = "Default Routine"
DEFAULT_ROUTINE_GOALS = ("sleep", "water")
REST_DAY_NAME = "Rest Day"  # title of a Recovery day with no Routines

_BALANCED: dict[DayKind, tuple[str, ...]] = {
    DayKind.TRAINING: ("pushups", "situps", "squats", "run"),
    DayKind.STANDARD: ("steps", "reading"),
    DayKind.RECOVERY: ("stretch",),
}

PATHS: dict[RegimenPath, dict[DayKind, tuple[str, ...]]] = {
    RegimenPath.BALANCED: _BALANCED,
    RegimenPath.STRENGTH: {
        DayKind.TRAINING: ("pushups", "situps", "squats", "strength_workout"),
        DayKind.STANDARD: ("steps", "stretch"),
        DayKind.RECOVERY: ("stretch",),
    },
    RegimenPath.ENDURANCE: {
        DayKind.TRAINING: ("run", "squats", "stretch"),
        DayKind.STANDARD: ("steps",),
        DayKind.RECOVERY: ("stretch",),
    },
    RegimenPath.SCHOLAR: {
        DayKind.TRAINING: ("study", "pushups"),
        DayKind.STANDARD: ("reading", "study"),
        DayKind.RECOVERY: ("reading",),
    },
    RegimenPath.CUSTOM: _BALANCED,
}

# Interview defaults: Mon/Wed/Fri training, Sunday recovery (0 = Monday).
DEFAULT_TRAINING_DAYS = (0, 2, 4)
DEFAULT_RECOVERY_DAYS = (6,)
