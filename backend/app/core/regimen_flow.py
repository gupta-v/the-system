"""Regimen and Goal management."""

from datetime import datetime
from uuid import UUID

from app.config.settings import get_settings
from app.core.context import Services
from app.core.rewards import sync_quest_rewards
from app.core.unit_of_work import UnitOfWork
from app.engine.types import DayStatus
from app.models.regimen import GoalIn, GoalOut, GoalPatch, RegimenIn, RegimenOut
from app.repositories.db_schema import Goal
from app.utils.time import game_date


def goal_out(goal: Goal) -> GoalOut:
    return GoalOut(
        id=goal.id,
        name=goal.name,
        stat=goal.stat,
        kind=goal.kind,
        target=goal.target,
        f_target=goal.f_target,
        unit=goal.unit,
        scales_with_rank=goal.scales_with_rank,
        weight=goal.weight,
        sets=goal.sets,
        archived=goal.archived,
    )


async def get_regimen(uow: UnitOfWork, user_id: UUID, now: datetime) -> RegimenOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        return await svc.regimen.view(user_id, game_date(now, profile.timezone, profile.reset_hour))


async def update_regimen(
    uow: UnitOfWork, user_id: UUID, spec: RegimenIn, now: datetime
) -> RegimenOut:
    """Applies from the next Daily Quest; today's, already issued, stays as it is.

    Testing switch (`reissue_today_on_plan_edit`): also rebuild today's open quest from the new
    plan, keeping progress on Goals that stay. Closed or Potion-shielded days are never touched.
    """
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        today = game_date(now, profile.timezone, profile.reset_hour)
        await svc.regimen.replace(user_id, spec, today)
        quest = await svc.quests.get(user_id, today)
        if (
            get_settings().reissue_today_on_plan_edit
            and quest is not None
            and quest.status is DayStatus.OPEN
            and not quest.potion_used
        ):
            plan = await svc.regimen.plan_for(user_id, today)
            rank = (await svc.player.progress(user_id)).rank
            svc.quests.reissue(quest, plan, rank)
            synced = await sync_quest_rewards(svc, profile, quest)
            await svc.notifications.hold(user_id, synced.notices)
        return await svc.regimen.view(user_id, today)


async def list_goals(uow: UnitOfWork, user_id: UUID, include_archived: bool) -> list[GoalOut]:
    async with uow:
        goals = await Services.of(uow).regimen.list_goals(user_id, include_archived)
        return [goal_out(g) for g in goals]


async def create_goal(uow: UnitOfWork, user_id: UUID, data: GoalIn) -> GoalOut:
    async with uow:
        return goal_out(await Services.of(uow).regimen.create_goal(user_id, data))


async def update_goal(uow: UnitOfWork, user_id: UUID, goal_id: UUID, patch: GoalPatch) -> GoalOut:
    async with uow:
        return goal_out(await Services.of(uow).regimen.update_goal(user_id, goal_id, patch))


async def archive_goal(uow: UnitOfWork, user_id: UUID, goal_id: UUID) -> None:
    async with uow:
        await Services.of(uow).regimen.archive_goal(user_id, goal_id)
