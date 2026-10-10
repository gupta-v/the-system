"""Daily Quests, Goal logs and Penalty Quests."""

from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.types import DayKind, DayStatus, Stat
from app.repositories.db_schema import DailyQuest, GoalLog, PenaltyQuest


class QuestRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_day(self, user_id: UUID, day: date) -> DailyQuest | None:
        return await self.session.scalar(
            select(DailyQuest).where(DailyQuest.user_id == user_id, DailyQuest.day == day)
        )

    async def add(self, quest: DailyQuest) -> DailyQuest:
        self.session.add(quest)
        await self.session.flush()
        return quest

    async def get_goal_log(self, user_id: UUID, goal_log_id: UUID) -> GoalLog | None:
        return await self.session.scalar(
            select(GoalLog)
            .join(DailyQuest)
            .where(GoalLog.id == goal_log_id, DailyQuest.user_id == user_id)
        )

    async def range(self, user_id: UUID, start: date, end: date) -> Sequence[DailyQuest]:
        return (
            await self.session.scalars(
                select(DailyQuest)
                .where(DailyQuest.user_id == user_id, DailyQuest.day.between(start, end))
                .order_by(DailyQuest.day)
            )
        ).all()

    async def goals_done(self, user_id: UUID) -> int:
        return (
            await self.session.scalar(
                select(func.count(GoalLog.id))
                .join(DailyQuest)
                .where(DailyQuest.user_id == user_id, GoalLog.completed_at.is_not(None))
            )
        ) or 0

    async def day_results(self, user_id: UUID) -> list[tuple[DayStatus, float, DayKind]]:
        """(status, completion, day kind) per Daily Quest, oldest first."""
        rows = await self.session.execute(
            select(DailyQuest.status, DailyQuest.completion, DailyQuest.day_kind)
            .where(DailyQuest.user_id == user_id)
            .order_by(DailyQuest.day)
        )
        return [(s, c, k) for s, c, k in rows]

    async def failed_days_since(self, user_id: UUID, since: date) -> list[date]:
        rows = await self.session.scalars(
            select(DailyQuest.day).where(
                DailyQuest.user_id == user_id,
                DailyQuest.status == DayStatus.FAILED,
                DailyQuest.day > since,
            )
        )
        return list(rows)

    async def potion_days_since(self, user_id: UUID, since: date) -> list[date]:
        rows = await self.session.scalars(
            select(DailyQuest.day).where(
                DailyQuest.user_id == user_id,
                DailyQuest.potion_used.is_(True),
                DailyQuest.day > since,
            )
        )
        return list(rows)

    async def potion_history(self, user_id: UUID) -> list[tuple[date, DayKind, float, bool, int]]:
        """(day, day kind, completion, potion used, Goal count) per Daily Quest, oldest first."""
        rows = await self.session.execute(
            select(
                DailyQuest.day,
                DailyQuest.day_kind,
                DailyQuest.completion,
                DailyQuest.potion_used,
                func.count(GoalLog.id),
            )
            .outerjoin(GoalLog)
            .where(DailyQuest.user_id == user_id)
            .group_by(DailyQuest.id)
            .order_by(DailyQuest.day)
        )
        return [(d, k, c, u, n) for d, k, c, u, n in rows]

    # Penalty Quests

    async def add_penalty(self, penalty: PenaltyQuest) -> PenaltyQuest:
        self.session.add(penalty)
        await self.session.flush()
        return penalty

    async def get_penalty(self, user_id: UUID, penalty_id: UUID) -> PenaltyQuest | None:
        return await self.session.scalar(
            select(PenaltyQuest).where(
                PenaltyQuest.id == penalty_id, PenaltyQuest.user_id == user_id
            )
        )

    async def open_penalties(self, user_id: UUID) -> Sequence[PenaltyQuest]:
        return (
            await self.session.scalars(
                select(PenaltyQuest)
                .where(PenaltyQuest.user_id == user_id, PenaltyQuest.status == "open")
                .order_by(PenaltyQuest.due)
            )
        ).all()

    async def overdue_penalties(self, user_id: UUID, now: datetime) -> Sequence[PenaltyQuest]:
        return (
            await self.session.scalars(
                select(PenaltyQuest).where(
                    PenaltyQuest.user_id == user_id,
                    PenaltyQuest.status == "open",
                    PenaltyQuest.due <= now,
                )
            )
        ).all()

    async def goal_breakdown(self, user_id: UUID, stat: Stat) -> list[tuple[str, int, int]]:
        """(Goal name, days done, days scheduled) for Goals tagged `stat`, most done first."""
        done = func.sum(case((GoalLog.progress >= GoalLog.target, 1), else_=0))
        rows = await self.session.execute(
            select(GoalLog.name, done, func.count())
            .join(DailyQuest)
            .where(DailyQuest.user_id == user_id, GoalLog.stat == stat)
            .group_by(GoalLog.name)
            .order_by(done.desc(), GoalLog.name)
        )
        return [(name, int(d), int(n)) for name, d, n in rows]
