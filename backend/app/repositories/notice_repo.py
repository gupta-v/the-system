from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db_schema import SystemNotice


class NoticeRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, user_id: UUID, type_: str, message: str, data: dict[str, Any]) -> None:
        self.session.add(SystemNotice(user_id=user_id, type=type_, message=message, data=data))

    async def pop_pending(self, user_id: UUID, now: datetime) -> Sequence[SystemNotice]:
        await self.session.flush()
        rows = (
            await self.session.scalars(
                select(SystemNotice)
                .where(SystemNotice.user_id == user_id, SystemNotice.delivered_at.is_(None))
                .order_by(SystemNotice.id)
            )
        ).all()
        for row in rows:
            row.delivered_at = now
        return rows
