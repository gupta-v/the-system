"""Awakening: settings + Regimen interview -> profile, Goals, Regimen, first Daily Quest."""

from datetime import datetime
from uuid import UUID

from app.core.context import Services
from app.core.daily_quest_flow import build_today
from app.core.unit_of_work import UnitOfWork
from app.models.notice import Notice, NoticeType
from app.models.player import SettingsIn
from app.models.quest import TodayOut
from app.models.regimen import AwakeningIn
from app.utils.errors import Conflict
from app.utils.time import game_date


async def awaken(uow: UnitOfWork, user_id: UUID, answers: AwakeningIn, now: datetime) -> TodayOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        if profile.awakened_on is not None:
            raise Conflict("[You have already Awakened.]")

        settings = SettingsIn.model_validate(
            answers.model_dump(
                include={
                    "display_name",
                    "timezone",
                    "reset_hour",
                    "difficulty",
                    "day_start",
                    "check_ins",
                },
                exclude_none=True,
            )
        )
        await svc.player.update_settings(profile, settings, today=None)

        today = game_date(now, profile.timezone, profile.reset_hour)
        await svc.regimen.create_from_awakening(user_id, answers, today)
        profile.awakened_on = today

        result = await build_today(svc, profile, now)
        result.notices.insert(
            0, Notice(type=NoticeType.AWAKENING, message="[You have been chosen as a Player.]")
        )
        return result
