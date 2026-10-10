"""Lazy day evaluation (architecture §3). Runs at the start of every Player request.

For each game day from the last evaluated one up to yesterday: generate the Daily Quest if the
Player never opened that day, finalise rewards, set the status, apply penalties and streak
milestones. Idempotent. Notices raised here are held until the UI fetches them.
"""

from datetime import date, datetime, timedelta

from app.config.titles import STREAK_MILESTONES
from app.core.context import Services
from app.core.rewards import sync_quest_rewards
from app.engine.penalties import xp_penalty
from app.engine.types import DayStatus
from app.models.notice import Notice
from app.repositories.db_schema import DailyQuest, Profile
from app.services import notification_service as notify
from app.services.player_service import PENALTY_SOURCE
from app.utils.time import day_end, game_date

MILESTONE_SOURCE = "streak_milestone"


async def ensure_quest(svc: Services, profile: Profile, day: date) -> DailyQuest:
    quest = await svc.quests.get(profile.user_id, day)
    if quest is not None:
        return quest
    plan = await svc.regimen.plan_for(profile.user_id, day)
    rank = (await svc.player.progress(profile.user_id)).rank
    return await svc.quests.create(profile.user_id, day, plan, rank)


async def ensure_days_closed(svc: Services, profile: Profile, now: datetime) -> None:
    if profile.awakened_on is None:
        return
    today = game_date(now, profile.timezone, profile.reset_hour)
    day = (
        profile.last_evaluated_day + timedelta(days=1)
        if profile.last_evaluated_day
        else profile.awakened_on
    )
    notices: list[Notice] = []
    while day < today:
        quest = await ensure_quest(svc, profile, day)
        if quest.status is DayStatus.OPEN:
            notices += await _close(svc, profile, quest, now)
        profile.last_evaluated_day = day
        day += timedelta(days=1)

    expired = await svc.quests.expire_penalties(profile.user_id, now)
    if expired:
        notices.append(notify.penalty_expired(expired))
    await svc.notifications.hold(profile.user_id, notices)


async def _close(svc: Services, profile: Profile, quest: DailyQuest, now: datetime) -> list[Notice]:
    synced = await sync_quest_rewards(svc, profile, quest)
    notices = list(synced.notices)
    result = svc.quests.evaluate(quest, profile.difficulty)
    svc.quests.close(quest, result, now)

    if result.status is DayStatus.FAILED:
        notices += await _penalise(svc, profile, quest, now)
    else:
        notices += await _streak_milestones(svc, profile, quest)
    return notices


async def _penalise(
    svc: Services, profile: Profile, quest: DailyQuest, now: datetime
) -> list[Notice]:
    total_xp = (await svc.player.progress(profile.user_id)).total_xp
    loss = xp_penalty(total_xp, profile.difficulty)
    if loss:
        await svc.player.award(
            profile.user_id, quest.day, xp=loss, source=PENALTY_SOURCE, ref_id=quest.id
        )
    # The Penalty Quest must be cleared before the next game day ends. If the Player was away
    # longer than that, it's already over: record nothing rather than flood them with notices.
    due = day_end(quest.day + timedelta(days=1), profile.timezone, profile.reset_hour)
    if due <= now:
        return []
    penalty = await svc.quests.issue_penalty(quest, profile.difficulty, due)
    return [notify.penalty(penalty.description, -loss, penalty.id)]


async def _streak_milestones(svc: Services, profile: Profile, quest: DailyQuest) -> list[Notice]:
    if quest.status is DayStatus.RECOVERY:
        return []
    streak = await svc.quests.streak(profile.user_id)
    notices = []
    for milestone in STREAK_MILESTONES:
        if streak >= milestone.days and await svc.player.grant_title(
            profile.user_id, milestone.title.code
        ):
            await svc.player.award(
                profile.user_id, quest.day, gold=milestone.gold, source=MILESTONE_SOURCE
            )
            notices.append(notify.title_acquired(milestone.title, milestone.gold))
    return notices
