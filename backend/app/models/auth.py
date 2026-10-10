from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.types import DisplayName, Password


class RegisterIn(BaseModel):
    email: EmailStr
    password: Password
    display_name: DisplayName | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: Password


class SessionOut(BaseModel):
    user_id: UUID
    display_name: str
    awakened: bool  # False -> UI routes to onboarding
