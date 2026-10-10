"""Status Window and Player settings."""

from datetime import date, datetime, timedelta
from uuid import UUID

from app.config.game import DIFFICULTY_RULES, HEATMAP_DAYS, INSIGHT_PACE_DAYS
from app.config.titles import TITLES
from app.core.context import Services
from app.core.day_close_flow import ensure_days_closed
from app.core.unit_of_work import UnitOfWork
from app.engine.insights import clear_rate, eta_days, longest_streak, next_rank_tier, xp_pace
from app.engine.penalties import is_rank_sealed
from app.engine.progression import level_progress, total_xp_for_level
from app.engine.types import DayStatus, Stat
from app.models.player import (
    HeatDayOut,
    InsightsOut,
    PenaltyQuestOut,
    RatingOut,
    SettingsIn,
    SettingsOut,
    StatDetailOut,
    StatusOut,
    TitleOut,
    XpJourneyOut,
)
from app.models.types import age
from app.repositories.db_schema import Profile
from app.utils.errors import Conflict, InvalidAction
from app.utils.time import game_date


def _title(code: str) -> TitleOut:
    t = TITLES[code]
    return TitleOut(code=t.code, name=t.name, description=t.description)


def settings_out(profile: Profile) -> SettingsOut:
    return SettingsOut(
        display_name=profile.display_name,
        timezone=profile.timezone,
        reset_hour=profile.reset_hour,
        difficulty=profile.difficulty,
        day_start=profile.day_start,
        check_ins=profile.check_ins,
        equipped_title=profile.equipped_title,
        sex=profile.sex,
        birth_date=profile.birth_date,
        age=age(profile.birth_date, date.today()) if profile.birth_date else None,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
    )


async def get_status(uow: UnitOfWork, user_id: UUID, now: datetime) -> StatusOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)

        progress = await svc.player.progress(user_id)
        strikes = await svc.quests.strikes(user_id, today)
        penalties = await svc.quests.open_penalties(user_id)
        title_codes = [c for c in await svc.player.title_codes(user_id) if c in TITLES]
        return StatusOut(
            display_name=profile.display_name,
            awakened_on=profile.awakened_on,
            level=progress.level,
            hunter_rank=progress.rank,
            total_xp=progress.total_xp,
            xp_into_level=progress.xp_into_level,
            xp_to_next=progress.xp_to_next,
            stats=await svc.player.stats(user_id, today),
            streak=await svc.quests.streak(user_id),
            gold=await svc.player.gold(user_id),
            difficulty=profile.difficulty,
            title=_title(profile.equipped_title) if profile.equipped_title in TITLES else None,
            titles=[_title(c) for c in title_codes],
            strikes=strikes,
            max_strikes=DIFFICULTY_RULES[profile.difficulty].max_strikes,
            # Sealed until the Penalty Zone is cleared (game-mechanics §6).
            rank_sealed=is_rank_sealed(strikes, profile.difficulty) and bool(penalties),
            recovery_potions=await svc.quests.potions(user_id, profile.difficulty),
            penalty_quests=[
                PenaltyQuestOut(id=p.id, description=p.description, due=p.due, status=p.status)
                for p in penalties
            ],
        )


async def get_settings(uow: UnitOfWork, user_id: UUID) -> SettingsOut:
    async with uow:
        return settings_out(await Services.of(uow).player.profile(user_id))


async def update_settings(
    uow: UnitOfWork, user_id: UUID, changes: SettingsIn, now: datetime
) -> SettingsOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        # Close days under the old timezone/reset hour before they change.
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        await svc.player.update_settings(profile, changes, today)
        return settings_out(profile)


STAT_HISTORY_DAYS = 30


async def get_rating(uow: UnitOfWork, user_id: UUID, at: date | None, now: datetime) -> RatingOut:
    """Snapshot at the end of game day `at` (default: today, i.e. current)."""
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        if profile.awakened_on is None:
            raise Conflict("[You have not Awakened yet.]")
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        day = at or today
        if not profile.awakened_on <= day <= today:
            raise InvalidAction(
                f"[Rating is available from {profile.awakened_on.isoformat()} to today.]"
            )
        return await svc.player.rating_at(user_id, day)


async def get_stat_detail(
    uow: UnitOfWork, user_id: UUID, stat: Stat, now: datetime
) -> StatDetailOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        current = (await svc.player.stats(user_id, today))[stat]
        return StatDetailOut(
            stat=stat,
            value=current.value,
            xp=current.xp,
            history=await svc.player.stat_history(user_id, stat, today, STAT_HISTORY_DAYS),
            goals=await svc.quests.goal_breakdown(user_id, stat),
        )


async def get_xp_journey(uow: UnitOfWork, user_id: UUID, now: datetime) -> XpJourneyOut:
    """Daily and cumulative XP from the Awakening day to today."""
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        if profile.awakened_on is None:
            raise Conflict("[You have not Awakened yet.]")
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)
        # shortcut: journey covers at most the last year (history query limit); paginate if needed.
        start = max(profile.awakened_on, today - timedelta(days=365))
        days = await svc.player.xp_journey(user_id, start, today)
        quests = {q.day: q for q in await svc.quests.history(user_id, start, today)}
        earned = await svc.quests.potion_earned_days(user_id, profile.difficulty)
        for d in days:
            if q := quests.get(d.day):
                d.quest_title = q.title
                d.status = q.status
                d.completion = q.completion
                d.potion_used = q.potion_used
                d.potion_earned = d.day in earned
        return XpJourneyOut(days=days)


async def get_insights(uow: UnitOfWork, user_id: UUID, now: datetime) -> InsightsOut:
    async with uow:
        svc = Services.of(uow)
        profile = await svc.player.profile(user_id)
        if profile.awakened_on is None:
            raise Conflict("[You have not Awakened yet.]")
        await ensure_days_closed(svc, profile, now)
        today = game_date(now, profile.timezone, profile.reset_hour)

        daily = await svc.player.daily_xp(user_id)
        progress = level_progress(sum(daily.values()))
        pace = xp_pace(daily, today, INSIGHT_PACE_DAYS, profile.awakened_on)
        tier = next_rank_tier(progress.level)
        to_rank = total_xp_for_level(tier.min_level) - progress.total_xp if tier else None

        start = today - timedelta(days=HEATMAP_DAYS - 1)
        quests = {q.day: q for q in await svc.quests.history(user_id, start, today)}
        heat = [
            HeatDayOut(
                day=d,
                status=q.status if (q := quests.get(d)) else None,
                completion=q.completion if q else None,
            )
            for d in (start + timedelta(days=i) for i in range(HEATMAP_DAYS))
        ]

        def window(days: int) -> list[DayStatus]:
            return [h.status for h in heat[-days:] if h.status is not None]

        statuses = await svc.quests.day_statuses(user_id)
        best_day = max(daily, key=lambda d: daily[d], default=None)
        return InsightsOut(
            xp_per_day=round(pace, 1),
            next_level_eta_days=eta_days(progress.xp_remaining, pace),
            next_rank=tier.rank if tier else None,
            next_rank_level=tier.min_level if tier else None,
            xp_to_next_rank=to_rank,
            next_rank_eta_days=eta_days(to_rank, pace) if to_rank is not None else None,
            clear_rate_7d=clear_rate(window(7)),
            clear_rate_30d=clear_rate(window(30)),
            clear_rate_all=clear_rate(statuses),
            heatmap=heat,
            current_streak=await svc.quests.streak(user_id),
            best_streak=longest_streak(statuses),
            best_day_xp=daily[best_day] if best_day else 0,
            best_day=best_day,
            goals_done=await svc.quests.goals_done(user_id),
            days_awakened=(today - profile.awakened_on).days + 1,
            potions_used=await svc.quests.potions_used(user_id),
        )
