"""Goals, Regimens and Regimen versions."""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db_schema import Goal, Regimen, RegimenVersion


class RegimenRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Goals

    async def list_goals(self, user_id: UUID, include_archived: bool = False) -> Sequence[Goal]:
        query = select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at)
        if not include_archived:
            query = query.where(Goal.archived.is_(False))
        return (await self.session.scalars(query)).all()

    async def get_goal(self, user_id: UUID, goal_id: UUID) -> Goal | None:
        return await self.session.scalar(
            select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        )

    async def add_goal(self, goal: Goal) -> Goal:
        self.session.add(goal)
        await self.session.flush()
        return goal

    # Regimens

    async def active_regimen(self, user_id: UUID) -> Regimen | None:
        return await self.session.scalar(
            select(Regimen).where(Regimen.user_id == user_id, Regimen.active.is_(True))
        )

    async def deactivate_all(self, user_id: UUID) -> None:
        for regimen in await self.session.scalars(
            select(Regimen).where(Regimen.user_id == user_id, Regimen.active.is_(True))
        ):
            regimen.active = False

    async def add_regimen(self, regimen: Regimen) -> Regimen:
        self.session.add(regimen)
        await self.session.flush()
        return regimen

    async def version_for(self, regimen_id: UUID, day: date) -> RegimenVersion | None:
        """Latest version effective on `day` (ties: newest wins)."""
        return await self.session.scalar(
            select(RegimenVersion)
            .where(RegimenVersion.regimen_id == regimen_id, RegimenVersion.effective_from <= day)
            .order_by(RegimenVersion.effective_from.desc(), RegimenVersion.created_at.desc())
            .limit(1)
        )

    async def versions_from(self, regimen_id: UUID, day: date) -> Sequence[RegimenVersion]:
        return (
            await self.session.scalars(
                select(RegimenVersion).where(
                    RegimenVersion.regimen_id == regimen_id, RegimenVersion.effective_from >= day
                )
            )
        ).all()

    async def add_version(self, version: RegimenVersion) -> RegimenVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def delete_version(self, version: RegimenVersion) -> None:
        await self.session.delete(version)
        await self.session.flush()
