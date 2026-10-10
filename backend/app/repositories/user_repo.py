from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db_schema import Profile, User, UserTitle


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def add_user(self, email: str, password_hash: str, display_name: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        self.session.add(Profile(user_id=user.id, display_name=display_name))
        await self.session.flush()
        return user

    async def get_profile(self, user_id: UUID) -> Profile | None:
        return await self.session.get(Profile, user_id)

    async def title_codes(self, user_id: UUID) -> list[str]:
        rows = await self.session.scalars(
            select(UserTitle.title_code)
            .where(UserTitle.user_id == user_id)
            .order_by(UserTitle.earned_at)
        )
        return list(rows)

    async def add_title(self, user_id: UUID, title_code: str) -> None:
        self.session.add(UserTitle(user_id=user_id, title_code=title_code))
        await self.session.flush()
