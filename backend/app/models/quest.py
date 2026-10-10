from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.engine.types import DayKind, DayStatus, GoalKind, Stat
from app.models.notice import Notice
from app.models.types import Progress


class GoalLogOut(BaseModel):
    id: UUID
    goal_id: UUID | None
    name: str
    stat: Stat
    kind: GoalKind
    target: float
    unit: str | None
    sets: int | None  # tap the box once per set; progress steps by target / sets
    progress: float
    done: bool


class DailyQuestOut(BaseModel):
    id: UUID
    day: date
    title: str
    day_kind: DayKind
    status: DayStatus
    completion: float
    potion_used: bool
    goals: list[GoalLogOut]


class TodayOut(BaseModel):
    quest: DailyQuestOut
    arrived: bool  # first open of this game day -> "[Daily Quest has arrived.]"
    resets_at: datetime
    seconds_until_reset: int
    notices: list[Notice]


class GoalProgressIn(BaseModel):
    progress: Progress


class QuestUpdateOut(BaseModel):
    quest: DailyQuestOut
    xp_gained: int  # negative when progress is lowered
    gold_gained: int
    notices: list[Notice]


class HistoryDayOut(BaseModel):
    day: date
    title: str
    day_kind: DayKind
    status: DayStatus
    completion: float


class NoticesOut(BaseModel):
    notices: list[Notice]
