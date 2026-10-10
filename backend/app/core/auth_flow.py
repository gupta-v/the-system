from app.core.context import Services
from app.core.unit_of_work import UnitOfWork
from app.models.auth import LoginIn, RegisterIn, SessionOut


async def register(uow: UnitOfWork, data: RegisterIn) -> SessionOut:
    async with uow:
        svc = Services.of(uow)
        user = await svc.auth.register(data.email, data.password, data.display_name)
        profile = await svc.player.profile(user.id)
        return SessionOut(user_id=user.id, display_name=profile.display_name, awakened=False)


async def login(uow: UnitOfWork, data: LoginIn) -> SessionOut:
    async with uow:
        svc = Services.of(uow)
        user = await svc.auth.authenticate(data.email, data.password)
        profile = await svc.player.profile(user.id)
        return SessionOut(
            user_id=user.id,
            display_name=profile.display_name,
            awakened=profile.awakened_on is not None,
        )
