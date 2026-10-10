"""XP, stat XP and Gold ledgers. Totals are always summed from events."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.types import Stat
from app.repositories.db_schema import GoldEvent, StatXpEvent, XpEvent


class LedgerRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_xp(
        self, user_id: UUID, day: date, amount: int, source: str, ref_id: UUID | None
    ) -> None:
        self.session.add(
            XpEvent(user_id=user_id, day=day, amount=amount, source=source, ref_id=ref_id)
        )

    async def add_stat_xp(
        self, user_id: UUID, day: date, stat: Stat, amount: int, source: str, ref_id: UUID | None
    ) -> None:
        self.session.add(
            StatXpEvent(
                user_id=user_id, day=day, stat=stat, amount=amount, source=source, ref_id=ref_id
            )
        )

    async def add_gold(
        self, user_id: UUID, day: date, amount: int, source: str, ref_id: UUID | None
    ) -> None:
        self.session.add(
            GoldEvent(user_id=user_id, day=day, amount=amount, source=source, ref_id=ref_id)
        )

    async def total_xp(self, user_id: UUID, until: date | None = None) -> int:
        """Total XP, optionally only from game days up to and including `until`."""
        await self.session.flush()
        query = select(func.coalesce(func.sum(XpEvent.amount), 0)).where(XpEvent.user_id == user_id)
        if until is not None:
            query = query.where(XpEvent.day <= until)
        return int(await self.session.scalar(query) or 0)

    async def total_gold(self, user_id: UUID) -> int:
        await self.session.flush()
        total = await self.session.scalar(
            select(func.coalesce(func.sum(GoldEvent.amount), 0)).where(GoldEvent.user_id == user_id)
        )
        return int(total or 0)

    async def stat_xp_totals(self, user_id: UUID, before: date | None = None) -> dict[Stat, int]:
        """Stat XP per stat, optionally only from game days strictly before `before`."""
        await self.session.flush()
        query = (
            select(StatXpEvent.stat, func.sum(StatXpEvent.amount))
            .where(StatXpEvent.user_id == user_id)
            .group_by(StatXpEvent.stat)
        )
        if before is not None:
            query = query.where(StatXpEvent.day < before)
        rows = await self.session.execute(query)
        return {stat: int(amount) for stat, amount in rows}

    async def awarded_for(self, user_id: UUID, source: str, ref_id: UUID) -> tuple[int, int]:
        """(xp, gold) already awarded for one source row, e.g. a Daily Quest."""
        await self.session.flush()
        xp = await self.session.scalar(
            select(func.coalesce(func.sum(XpEvent.amount), 0)).where(
                XpEvent.user_id == user_id, XpEvent.source == source, XpEvent.ref_id == ref_id
            )
        )
        gold = await self.session.scalar(
            select(func.coalesce(func.sum(GoldEvent.amount), 0)).where(
                GoldEvent.user_id == user_id,
                GoldEvent.source == source,
                GoldEvent.ref_id == ref_id,
            )
        )
        return int(xp or 0), int(gold or 0)

    async def stat_awarded_for(self, user_id: UUID, source: str, ref_id: UUID) -> dict[Stat, int]:
        await self.session.flush()
        rows = await self.session.execute(
            select(StatXpEvent.stat, func.sum(StatXpEvent.amount))
            .where(
                StatXpEvent.user_id == user_id,
                StatXpEvent.source == source,
                StatXpEvent.ref_id == ref_id,
            )
            .group_by(StatXpEvent.stat)
        )
        return {stat: int(amount) for stat, amount in rows}

    async def stat_xp_by_day(self, user_id: UUID, stat: Stat, since: date) -> dict[date, int]:
        await self.session.flush()
        rows = await self.session.execute(
            select(StatXpEvent.day, func.sum(StatXpEvent.amount))
            .where(
                StatXpEvent.user_id == user_id,
                StatXpEvent.stat == stat,
                StatXpEvent.day >= since,
            )
            .group_by(StatXpEvent.day)
        )
        return {day: int(amount) for day, amount in rows}

    async def xp_by_day_source(self, user_id: UUID) -> dict[date, dict[str, int]]:
        """XP per game day, split by source (daily_quest, penalty, ...)."""
        await self.session.flush()
        rows = await self.session.execute(
            select(XpEvent.day, XpEvent.source, func.sum(XpEvent.amount))
            .where(XpEvent.user_id == user_id)
            .group_by(XpEvent.day, XpEvent.source)
        )
        out: dict[date, dict[str, int]] = {}
        for day, source, amount in rows:
            out.setdefault(day, {})[source] = int(amount)
        return out

    async def gold_by_day(self, user_id: UUID, since: date) -> dict[date, int]:
        await self.session.flush()
        rows = await self.session.execute(
            select(GoldEvent.day, func.sum(GoldEvent.amount))
            .where(GoldEvent.user_id == user_id, GoldEvent.day >= since)
            .group_by(GoldEvent.day)
        )
        return {day: int(amount) for day, amount in rows}
