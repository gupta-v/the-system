"""Shared FastAPI dependencies. Override `get_uow` / `get_now` in tests."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends

from app.config.settings import get_settings
from app.core.unit_of_work import UnitOfWork
from app.repositories.session import get_session_factory
from app.utils.errors import Unauthorized
from app.utils.security import decode_access_token
from app.utils.time import utcnow


def get_uow() -> UnitOfWork:
    return UnitOfWork(get_session_factory())


def get_now() -> datetime:
    return utcnow()


def get_current_user_id(
    session: Annotated[str | None, Cookie(alias=get_settings().cookie_name)] = None,
) -> UUID:
    user_id = decode_access_token(session) if session else None
    if user_id is None:
        raise Unauthorized("[Not logged in.]")
    return user_id


Uow = Annotated[UnitOfWork, Depends(get_uow)]
Now = Annotated[datetime, Depends(get_now)]
CurrentUser = Annotated[UUID, Depends(get_current_user_id)]
