from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_now, get_uow
from app.core.unit_of_work import UnitOfWork
from app.main import create_app
from app.repositories.db_schema import Base
from app.repositories.session import make_session_factory

# Monday. Game day starts at 04:00 UTC (reset hour 4, timezone UTC).
MONDAY_9AM = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


@dataclass
class Clock:
    now: datetime = MONDAY_9AM

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
async def client(clock: Clock) -> AsyncIterator[AsyncClient]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = make_session_factory(engine)

    app = create_app()
    app.dependency_overrides[get_uow] = lambda: UnitOfWork(factory)
    app.dependency_overrides[get_now] = lambda: clock.now
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await engine.dispose()


@pytest.fixture
async def player(client: AsyncClient) -> AsyncClient:
    """Registered + logged-in client (cookie set), not yet Awakened."""
    r = await client.post(
        "/auth/register", json={"email": "jinwoo@example.com", "password": "arise-arise"}
    )
    assert r.status_code == 201, r.text
    return client


@pytest.fixture
async def awakened(player: AsyncClient) -> AsyncClient:
    r = await player.post("/awakening", json={"timezone": "UTC", "extras": ["water"]})
    assert r.status_code == 200, r.text
    return player
