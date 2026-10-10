"""Player: profile, settings, XP/Gold/stat ledgers, level and Hunter Rank, Titles."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.titles import TITLES
from app.engine.progression import LevelProgress, level_progress
from app.engine.stats import stat_value
from app.engine.types import Stat
from app.models.player import (
    RatingOut,
    SettingsIn,
    StatDayOut,
    StatOut,
    XpJourneyDayOut,
)
from app.repositories.db_schema import Profile
from app.repositories.ledger_repo import LedgerRepo
from app.repositories.user_repo import UserRepo
from app.utils.errors import InvalidAction, NotFound

DIFFICULTY_CHANGE_COOLDOWN_DAYS = 7
# Ledger source names (written by core/rewards.py and core/day_close_flow.py).
DAILY_QUEST_SOURCE = "daily_quest"
PENALTY_SOURCE = "penalty"


@dataclass(frozen=True)
class Award:
    before: LevelProgress
    after: LevelProgress


class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepo(session)
        self.ledger = LedgerRepo(session)

    async def profile(self, user_id: UUID) -> Profile:
        profile = await self.users.get_profile(user_id)
        if profile is None:
            raise NotFound("[Player not found.]")
        return profile

    async def progress(self, user_id: UUID) -> LevelProgress:
        return level_progress(await self.ledger.total_xp(user_id))

    async def gold(self, user_id: UUID) -> int:
        return await self.ledger.total_gold(user_id)

    async def award(
        self,
        user_id: UUID,
        day: date,
        *,
        xp: int = 0,
        gold: int = 0,
        stat_xp: dict[Stat, int] | None = None,
        source: str,
        ref_id: UUID | None = None,
    ) -> Award:
        """Append ledger events (amounts may be negative) and report the level change."""
        before = await self.progress(user_id)
        if xp:
            await self.ledger.add_xp(user_id, day, xp, source, ref_id)
        if gold:
            await self.ledger.add_gold(user_id, day, gold, source, ref_id)
        for stat, amount in (stat_xp or {}).items():
            if amount:
                await self.ledger.add_stat_xp(user_id, day, stat, amount, source, ref_id)
        return Award(before=before, after=await self.progress(user_id))

    async def awarded_for(
        self, user_id: UUID, source: str, ref_id: UUID
    ) -> tuple[int, int, dict[Stat, int]]:
        xp, gold = await self.ledger.awarded_for(user_id, source, ref_id)
        stats = await self.ledger.stat_awarded_for(user_id, source, ref_id)
        return xp, gold, stats

    async def stats(self, user_id: UUID, today: date) -> dict[Stat, StatOut]:
        now = await self.ledger.stat_xp_totals(user_id)
        yesterday = await self.ledger.stat_xp_totals(user_id, before=today)
        return {
            stat: StatOut(
                value=stat_value(now.get(stat, 0)),
                delta=stat_value(now.get(stat, 0)) - stat_value(yesterday.get(stat, 0)),
                xp=now.get(stat, 0),
            )
            for stat in Stat
        }

    # Titles

    async def title_codes(self, user_id: UUID) -> list[str]:
        return await self.users.title_codes(user_id)

    async def grant_title(self, user_id: UUID, code: str) -> bool:
        """False if the Player already holds it."""
        if code in await self.users.title_codes(user_id):
            return False
        await self.users.add_title(user_id, code)
        return True

    # Settings

    async def update_settings(
        self, profile: Profile, changes: SettingsIn, today: date | None
    ) -> None:
        """`today` is None during Awakening (no difficulty cooldown yet)."""
        sent = changes.model_fields_set
        # Hunter profile fields: null clears them, so apply whatever was sent.
        for field in ("sex", "birth_date", "height_cm", "weight_kg"):
            if field in sent:
                setattr(profile, field, getattr(changes, field))
        if changes.display_name is not None:
            profile.display_name = changes.display_name
        if changes.timezone is not None:
            profile.timezone = changes.timezone
        if changes.reset_hour is not None:
            profile.reset_hour = changes.reset_hour
        if changes.day_start is not None:
            profile.day_start = changes.day_start
        if changes.check_ins is not None:
            profile.check_ins = changes.check_ins
        if changes.difficulty is not None and changes.difficulty is not profile.difficulty:
            last = profile.difficulty_changed_on
            if (
                today is not None
                and last is not None
                and (today - last).days < DIFFICULTY_CHANGE_COOLDOWN_DAYS
            ):
                raise InvalidAction("[Difficulty can be changed once per week.]")
            profile.difficulty = changes.difficulty
            profile.difficulty_changed_on = today
        if "equipped_title" in sent:
            code = changes.equipped_title
            if code is not None and (
                code not in TITLES or code not in await self.users.title_codes(profile.user_id)
            ):
                raise InvalidAction("[You do not hold this Title.]")
            profile.equipped_title = code

    # Rating snapshots and stat detail (read-only, from the ledgers)

    async def rating_at(self, user_id: UUID, day: date) -> RatingOut:
        progress = level_progress(await self.ledger.total_xp(user_id, until=day))
        stat_xp = await self.ledger.stat_xp_totals(user_id, before=day + timedelta(days=1))
        return RatingOut(
            day=day,
            level=progress.level,
            hunter_rank=progress.rank,
            total_xp=progress.total_xp,
            xp_into_level=progress.xp_into_level,
            xp_to_next=progress.xp_to_next,
            stats={stat: stat_value(stat_xp.get(stat, 0)) for stat in Stat},
        )

    async def stat_history(
        self, user_id: UUID, stat: Stat, today: date, days: int
    ) -> list[StatDayOut]:
        since = today - timedelta(days=days - 1)
        by_day = await self.ledger.stat_xp_by_day(user_id, stat, since)
        return [
            StatDayOut(day=d, xp=by_day.get(d, 0))
            for d in (since + timedelta(days=i) for i in range(days))
        ]

    async def daily_xp(self, user_id: UUID) -> dict[date, int]:
        """Net XP per game day (all sources)."""
        return {
            d: sum(src.values()) for d, src in (await self.ledger.xp_by_day_source(user_id)).items()
        }

    async def xp_journey(self, user_id: UUID, start: date, end: date) -> list[XpJourneyDayOut]:
        """XP side of the journey; quest fields are filled in by core (quest domain)."""
        by_day = await self.ledger.xp_by_day_source(user_id)
        gold = await self.ledger.gold_by_day(user_id, start)
        total = sum(sum(src.values()) for day, src in by_day.items() if day < start)
        level = level_progress(total).level
        days = []
        for i in range((end - start).days + 1):
            day = start + timedelta(days=i)
            sources = by_day.get(day, {})
            xp = sum(sources.values())
            total += xp
            new_level = level_progress(total).level
            days.append(
                XpJourneyDayOut(
                    day=day,
                    xp=xp,
                    xp_quest=sources.get(DAILY_QUEST_SOURCE, 0),
                    xp_penalty=sources.get(PENALTY_SOURCE, 0),
                    gold=gold.get(day, 0),
                    total_xp=total,
                    level=new_level,
                    level_up=new_level > level,
                    level_down=new_level < level,
                    quest_title=None,
                    status=None,
                    completion=None,
                    potion_used=False,
                )
            )
            level = new_level
        return days
