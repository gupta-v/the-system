"""Player profile: Awakening, settings, held System notices."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, Now, Uow
from app.core import daily_quest_flow, onboarding_flow, status_flow
from app.models.player import SettingsIn, SettingsOut
from app.models.quest import NoticesOut, TodayOut
from app.models.regimen import AwakeningIn

router = APIRouter(tags=["player"])


@router.post("/awakening")
async def awaken(answers: AwakeningIn, user_id: CurrentUser, uow: Uow, now: Now) -> TodayOut:
    """Onboarding + Regimen interview. Returns the first Daily Quest."""
    return await onboarding_flow.awaken(uow, user_id, answers, now)


@router.get("/me/settings")
async def get_settings(user_id: CurrentUser, uow: Uow) -> SettingsOut:
    return await status_flow.get_settings(uow, user_id)


@router.patch("/me/settings")
async def update_settings(
    changes: SettingsIn, user_id: CurrentUser, uow: Uow, now: Now
) -> SettingsOut:
    return await status_flow.update_settings(uow, user_id, changes, now)


@router.get("/me/notices")
async def notices(user_id: CurrentUser, uow: Uow, now: Now) -> NoticesOut:
    """System notices raised while the Player was away (day close, penalties)."""
    return NoticesOut(notices=await daily_quest_flow.pending_notices(uow, user_id, now))
