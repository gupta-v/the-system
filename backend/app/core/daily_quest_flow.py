"""Daily Quest use cases: today, Goal logs, Clear All, Recovery Potion, Penalty Quests, history."""

from datetime import date, datetime
from uuid import UUID

from app.core.context import Services
from app.core.day_close_flow import ensure_days_closed, ensure_quest
from app.core.rewards import sync_quest_rewards
from app.core.unit_of_work import UnitOfWork
from app.engine.types import DayKind
from app.models.notice import Notice
from app.models.quest import (
    DailyQuestOut,
    GoalLogOut,
    HistoryDayOut,
    NoticesOut,
    QuestUpdateOut,
    TodayOut,
)
from app.repositories.db_schema import DailyQuest, Profile
from app.services import notification_service as notify
from app.utils.errors import Conflict, NotFound
from app.utils.time import game_date, next_reset, seconds_until_reset


def quest_out(quest: DailyQuest) -> DailyQuestOut:
    return DailyQuestOut(
        id=quest.id,
        day=quest.day,
        title=quest.title,
        day_kind=quest.day_kind,
        status=quest.status,
        completion=quest.completion,
        potion_used=quest.potion_used,
        goals=[
            GoalLogOut(
                id=log.id,
                goal_id=log.goal_id,
                name=log.name,
                stat=log.stat,
                kind=log.kind,
                target=log.target,
                unit=log.unit,
                sets=log.sets,
                progress=log.progress,
                done=log.progress >= log.target,
            )
            for log in quest.goal_logs
        ],
    )


async def _awakened_profile(svc: Services, user_id: UUID, now: datetime) -> Profile:
    """Load the Player, close any finished days. Every Daily Quest flow starts here."""
    profile = await svc.player.profile(user_id)
    if profile.awakened_on is None:
        raise Conflict("[You have not Awakened yet.]")
    await ensure_days_closed(svc, profile, now)
    return profile


async def build_today(svc: Services, profile: Profile, now: datetime) -> TodayOut:
    today = game_date(now, profile.timezone, profile.reset_hour)
    quest = await ensure_quest(svc, profile, today)
    notices = await svc.notifications.pop(profile.user_id)
    arrived = quest.seen_at is None
    if arrived:
        quest.seen_at = now
        notices.append(notify.quest_arrived(quest.title, len(quest.goal_logs)))
        if quest.day_kind is DayKind.RECOVERY:
            notices.append(notify.recovery_day())
        elif quest.goal_logs:
            notices.append(notify.penalty_warning())
    return TodayOut(
        quest=quest_out(quest),
        arrived=arrived,
        resets_at=next_reset(now, profile.timezone, profile.reset_hour),
        seconds_until_reset=seconds_until_reset(now, profile.timezone, profile.reset_hour),
        notices=notices,
    )


async def get_today(uow: UnitOfWork, user_id: UUID, now: datetime) -> TodayOut:
    async with uow:
        svc = Services.of(uow)
        profile = await _awakened_profile(svc, user_id, now)
        return await build_today(svc, profile, now)


async def log_goal(
    uow: UnitOfWork, user_id: UUID, goal_log_id: UUID, progress: float, now: datetime
) -> QuestUpdateOut:
    async with uow:
        svc = Services.of(uow)
        profile = await _awakened_profile(svc, user_id, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        log = await svc.quests.open_goal_log(user_id, goal_log_id, today)
        svc.quests.set_progress(log, progress, now)
        quest = await ensure_quest(svc, profile, today)
        return await _updated(svc, profile, quest)


async def clear_all(uow: UnitOfWork, user_id: UUID, now: datetime) -> QuestUpdateOut:
    """`[Clear All]`: every remaining Goal done as planned -> one-tap perfect day."""
    async with uow:
        svc = Services.of(uow)
        profile = await _awakened_profile(svc, user_id, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        quest = await ensure_quest(svc, profile, today)
        for log in quest.goal_logs:
            if log.progress < log.target:
                svc.quests.set_progress(log, log.target, now)
        return await _updated(svc, profile, quest)


async def use_recovery_potion(uow: UnitOfWork, user_id: UUID, now: datetime) -> QuestUpdateOut:
    async with uow:
        svc = Services.of(uow)
        profile = await _awakened_profile(svc, user_id, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        quest = await ensure_quest(svc, profile, today)
        left = await svc.quests.use_potion(quest, profile.difficulty)
        update = await _updated(svc, profile, quest)
        update.notices.insert(0, notify.potion_used(left))
        return update


async def _updated(svc: Services, profile: Profile, quest: DailyQuest) -> QuestUpdateOut:
    synced = await sync_quest_rewards(svc, profile, quest)
    return QuestUpdateOut(
        quest=quest_out(quest),
        xp_gained=synced.xp,
        gold_gained=synced.gold,
        notices=synced.notices,
    )


async def clear_penalty(
    uow: UnitOfWork, user_id: UUID, penalty_id: UUID, now: datetime
) -> NoticesOut:
    async with uow:
        svc = Services.of(uow)
        await _awakened_profile(svc, user_id, now)
        await svc.quests.clear_penalty(user_id, penalty_id, now)
        return NoticesOut(notices=[notify.penalty_cleared()])


async def history(
    uow: UnitOfWork, user_id: UUID, start: date, end: date, now: datetime
) -> list[HistoryDayOut]:
    async with uow:
        svc = Services.of(uow)
        await _awakened_profile(svc, user_id, now)
        return [
            HistoryDayOut(
                day=q.day,
                title=q.title,
                day_kind=q.day_kind,
                status=q.status,
                completion=q.completion,
            )
            for q in await svc.quests.history(user_id, start, end)
        ]


async def get_day(uow: UnitOfWork, user_id: UUID, day: date, now: datetime) -> DailyQuestOut:
    """One past (or today's) Daily Quest, read-only, for the History calendar."""
    async with uow:
        svc = Services.of(uow)
        await _awakened_profile(svc, user_id, now)
        quest = await svc.quests.get(user_id, day)
        if quest is None:
            raise NotFound("[No Daily Quest on this day.]")
        return quest_out(quest)


async def pending_notices(uow: UnitOfWork, user_id: UUID, now: datetime) -> list[Notice]:
    async with uow:
        svc = Services.of(uow)
        await _awakened_profile(svc, user_id, now)
        return await svc.notifications.pop(user_id)
