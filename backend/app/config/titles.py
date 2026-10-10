"""Titles (docs/design/game-mechanics.md §7-8). Cosmetic in MVP.

Streak milestones grant a Title and Gold. Gold amounts are placeholders — tune after dogfooding.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Title:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class StreakMilestone:
    days: int
    title: Title
    gold: int


STREAK_MILESTONES: tuple[StreakMilestone, ...] = (
    StreakMilestone(7, Title("streak_7", "Persistent", "Held a 7-day streak."), 50),
    StreakMilestone(21, Title("streak_21", "Unbroken", "Held a 21-day streak."), 150),
    StreakMilestone(66, Title("streak_66", "Iron Will", "Held a 66-day streak."), 500),
    StreakMilestone(100, Title("streak_100", "The Relentless", "Held a 100-day streak."), 1000),
)

TITLES: dict[str, Title] = {m.title.code: m.title for m in STREAK_MILESTONES}
