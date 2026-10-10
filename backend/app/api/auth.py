from fastapi import APIRouter, Response, status

from app.api.deps import Uow
from app.config.settings import get_settings
from app.core import auth_flow
from app.models.auth import LoginIn, RegisterIn, SessionOut
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, session: SessionOut) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.cookie_name,
        create_access_token(session.user_id),
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterIn, uow: Uow, response: Response) -> SessionOut:
    session = await auth_flow.register(uow, data)
    _set_session_cookie(response, session)
    return session


@router.post("/login")
async def login(data: LoginIn, uow: Uow, response: Response) -> SessionOut:
    session = await auth_flow.login(uow, data)
    _set_session_cookie(response, session)
    return session


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(get_settings().cookie_name)
