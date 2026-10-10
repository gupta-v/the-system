from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.engine.types import DayStatus, Difficulty, HunterRank, Stat
from app.models.types import (
    BirthDate,
    DisplayName,
    HeightCm,
    ResetHour,
    Timezone,
    WeightKg,
)

CheckIns = Literal["morning", "evening", "both"]
Sex = Literal["male", "female", "other"]


class StatOut(BaseModel):
    value: int
    delta: int  # vs end of yesterday (▲ in the Status Window)
    xp: int


class PenaltyQuestOut(BaseModel):
    id: UUID
    description: str
    due: datetime
    status: str


class TitleOut(BaseModel):
    code: str
    name: str
    description: str


class StatusOut(BaseModel):
    """Status Window."""

    display_name: str
    awakened_on: date | None
    level: int
    hunter_rank: HunterRank
    total_xp: int
    xp_into_level: int
    xp_to_next: int
    stats: dict[Stat, StatOut]
    streak: int
    gold: int
    difficulty: Difficulty
    title: TitleOut | None
    titles: list[TitleOut]
    strikes: int
    max_strikes: int | None
    rank_sealed: bool
    recovery_potions: int  # held now
    penalty_quests: list[PenaltyQuestOut]


class SettingsIn(BaseModel):
    """Partial update: only fields sent are changed. `equipped_title: null` unequips."""

    display_name: DisplayName | None = None
    timezone: Timezone | None = None
    reset_hour: ResetHour | None = None
    difficulty: Difficulty | None = None
    day_start: time | None = None
    check_ins: CheckIns | None = None
    equipped_title: str | None = None
    # Hunter profile: send null to clear.
    sex: Sex | None = None
    birth_date: BirthDate | None = None
    height_cm: HeightCm | None = None
    weight_kg: WeightKg | None = None


class SettingsOut(BaseModel):
    display_name: str
    timezone: str
    reset_hour: int
    difficulty: Difficulty
    day_start: time
    check_ins: str
    equipped_title: str | None
    sex: str | None
    birth_date: date | None
    age: int | None
    height_cm: float | None
    weight_kg: float | None


class RatingOut(BaseModel):
    """Status as of the end of one game day ("Your Rating" tabs)."""

    day: date
    level: int
    hunter_rank: HunterRank
    total_xp: int
    xp_into_level: int
    xp_to_next: int
    stats: dict[Stat, int]


class StatDayOut(BaseModel):
    day: date
    xp: int


class StatGoalOut(BaseModel):
    name: str
    done_days: int
    total_days: int


class StatDetailOut(BaseModel):
    stat: Stat
    value: int
    xp: int
    history: list[StatDayOut]  # last 30 game days, oldest first, zero-filled
    goals: list[StatGoalOut]


class XpJourneyDayOut(BaseModel):
    day: date
    xp: int  # net XP that game day
    xp_quest: int  # from the Daily Quest
    xp_penalty: int  # taken away by the Penalty Zone (<= 0)
    gold: int
    total_xp: int  # cumulative at the end of the day
    level: int  # level at the end of the day
    level_up: bool  # level rose this day
    level_down: bool  # level fell this day (Hunter mode)
    quest_title: str | None  # None: no Daily Quest that day
    status: DayStatus | None
    completion: float | None
    potion_used: bool
    potion_earned: bool = False  # cleared Recovery Day that added a Potion


class XpJourneyOut(BaseModel):
    days: list[XpJourneyDayOut]  # Awakening day -> today, every day included


class HeatDayOut(BaseModel):
    day: date
    status: DayStatus | None  # None: no Daily Quest (before Awakening)
    completion: float | None


class InsightsOut(BaseModel):
    """Rating extras: pace and ETAs, clear rate, heatmap, personal records."""

    xp_per_day: float  # average net XP over the last INSIGHT_PACE_DAYS days
    next_level_eta_days: int | None  # None: no XP pace yet
    next_rank: HunterRank | None  # None: already S
    next_rank_level: int | None
    xp_to_next_rank: int | None
    next_rank_eta_days: int | None
    clear_rate_7d: float | None  # None: no judged days in the window
    clear_rate_30d: float | None
    clear_rate_all: float | None
    heatmap: list[HeatDayOut]  # last HEATMAP_DAYS days, oldest first
    current_streak: int
    best_streak: int
    best_day_xp: int
    best_day: date | None
    goals_done: int
    days_awakened: int
    potions_used: int
