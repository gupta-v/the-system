"""Player progress: Status Window, rating snapshots, stat detail, XP Journey."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, Now, Uow
from app.core import status_flow
from app.engine.types import Stat
from app.models.player import InsightsOut, RatingOut, StatDetailOut, StatusOut, XpJourneyOut

router = APIRouter(tags=["progress"])


@router.get("/me/status")
async def status(user_id: CurrentUser, uow: Uow, now: Now) -> StatusOut:
    return await status_flow.get_status(uow, user_id, now)


@router.get("/me/rating")
async def rating(
    user_id: CurrentUser, uow: Uow, now: Now, at: Annotated[date | None, Query()] = None
) -> RatingOut:
    """Level, XP and stats as of the end of game day `at` (default today)."""
    return await status_flow.get_rating(uow, user_id, at, now)


@router.get("/me/stats/{stat}")
async def stat_detail(stat: Stat, user_id: CurrentUser, uow: Uow, now: Now) -> StatDetailOut:
    """One stat: value, last 30 days of stat XP, and the Goals that feed it."""
    return await status_flow.get_stat_detail(uow, user_id, stat, now)


@router.get("/me/xp-journey")
async def xp_journey(user_id: CurrentUser, uow: Uow, now: Now) -> XpJourneyOut:
    """XP per day and running total since Awakening, with level-up days marked."""
    return await status_flow.get_xp_journey(uow, user_id, now)


@router.get("/me/insights")
async def insights(user_id: CurrentUser, uow: Uow, now: Now) -> InsightsOut:
    """Rating extras: XP pace, level/rank ETA, clear rate, 12-week heatmap, personal records."""
    return await status_flow.get_insights(uow, user_id, now)
