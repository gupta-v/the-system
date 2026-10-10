import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db_schema import User
from app.repositories.user_repo import UserRepo
from app.utils.errors import Conflict, Unauthorized
from app.utils.security import hash_password, verify_password

# Verified against when the email is unknown, so response time doesn't reveal which emails exist.
_DUMMY_HASH = hash_password("not-a-real-password")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepo(session)

    async def register(self, email: str, password: str, display_name: str | None) -> User:
        email = email.lower()
        if await self.users.get_by_email(email):
            raise Conflict("[This Hunter is already registered.]")
        # argon2 is CPU-bound by design; keep it off the event loop.
        password_hash = await asyncio.to_thread(hash_password, password)
        return await self.users.add_user(email, password_hash, display_name or email.split("@")[0])

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email.lower())
        ok = await asyncio.to_thread(
            verify_password, user.password_hash if user else _DUMMY_HASH, password
        )
        if user is None or not ok:
            raise Unauthorized("[Invalid credentials.]")
        return user
