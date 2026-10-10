"""System notices: messages the UI animates as System windows. The UI never decides outcomes."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NoticeType(StrEnum):
    AWAKENING = "awakening"
    QUEST_ARRIVED = "quest_arrived"
    QUEST_COMPLETE = "quest_complete"
    LEVEL_UP = "level_up"
    RANK_UP = "rank_up"
    PENALTY = "penalty"
    PENALTY_CLEARED = "penalty_cleared"
    PENALTY_EXPIRED = "penalty_expired"
    TITLE_ACQUIRED = "title_acquired"
    RECOVERY = "recovery"
    REWARD = "reward"
    WARNING = "warning"


class Notice(BaseModel):
    type: NoticeType
    message: str  # bracketed System voice, e.g. "[Level Up!]"
    data: dict[str, Any] = Field(default_factory=dict)
