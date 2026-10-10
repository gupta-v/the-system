"""Domain enums shared by the engine, services and repositories."""

from enum import StrEnum


class Stat(StrEnum):
    STR = "STR"  # Strength
    VIT = "VIT"  # Health / recovery
    AGI = "AGI"  # Cardio / mobility
    INT = "INT"  # Learning / mind
    PER = "PER"  # Focus / discipline (Sense)


class HunterRank(StrEnum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"


class Difficulty(StrEnum):
    AWAKENED = "awakened"
    ELITE = "elite"  # Elite Hunter
    NATIONAL = "national"  # National Level Hunter
    REAWAKENED = "reawakened"  # second awakening, one step below Monarch
    MONARCH = "monarch"


class GoalKind(StrEnum):
    CHECK = "check"  # done / not done
    NUMERIC = "numeric"  # progress toward a target, e.g. [50 / 100]


class DayKind(StrEnum):
    TRAINING = "training"
    STANDARD = "standard"
    RECOVERY = "recovery"


class DayStatus(StrEnum):
    OPEN = "open"  # today, not evaluated yet
    CLEARED = "cleared"  # 100% complete
    PASSED = "passed"  # above fail threshold, below 100%
    FAILED = "failed"  # below fail threshold -> Penalty Zone
    RECOVERY = "recovery"  # planned Recovery Day or Recovery Potion used
