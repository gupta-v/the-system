from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, Now, Uow
from app.core import daily_quest_flow
from app.models.quest import (
    DailyQuestOut,
    GoalProgressIn,
    HistoryDayOut,
    NoticesOut,
    QuestUpdateOut,
    TodayOut,
)

router = APIRouter(tags=["daily quest"])


@router.get("/days/today")
async def today(user_id: CurrentUser, uow: Uow, now: Now) -> TodayOut:
    return await daily_quest_flow.get_today(uow, user_id, now)


@router.patch("/days/today/goals/{goal_log_id}")
async def log_goal(
    goal_log_id: UUID, data: GoalProgressIn, user_id: CurrentUser, uow: Uow, now: Now
) -> QuestUpdateOut:
    return await daily_quest_flow.log_goal(uow, user_id, goal_log_id, data.progress, now)


@router.post("/days/today/clear-all")
async def clear_all(user_id: CurrentUser, uow: Uow, now: Now) -> QuestUpdateOut:
    return await daily_quest_flow.clear_all(uow, user_id, now)


@router.post("/days/today/recovery-potion")
async def recovery_potion(user_id: CurrentUser, uow: Uow, now: Now) -> QuestUpdateOut:
    return await daily_quest_flow.use_recovery_potion(uow, user_id, now)


@router.get("/days")
async def history(
    start: Annotated[date, Query(alias="from")],
    end: Annotated[date, Query(alias="to")],
    user_id: CurrentUser,
    uow: Uow,
    now: Now,
) -> list[HistoryDayOut]:
    return await daily_quest_flow.history(uow, user_id, start, end, now)


@router.get("/days/{day}")
async def get_day(day: date, user_id: CurrentUser, uow: Uow, now: Now) -> DailyQuestOut:
    """One day's Daily Quest with its Goals (History detail). Read-only."""
    return await daily_quest_flow.get_day(uow, user_id, day, now)


@router.post("/penalty-quests/{penalty_id}/clear")
async def clear_penalty(penalty_id: UUID, user_id: CurrentUser, uow: Uow, now: Now) -> NoticesOut:
    return await daily_quest_flow.clear_penalty(uow, user_id, penalty_id, now)
