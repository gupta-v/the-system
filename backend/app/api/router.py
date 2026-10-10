"""Single entry point for all API routers. main.py includes only `api_router`."""

from fastapi import APIRouter

from app.api import auth, days, player, progress, regimen
from app.core import rules_flow
from app.models.rules import RulesOut

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(player.router)
api_router.include_router(progress.router)
api_router.include_router(days.router)
api_router.include_router(regimen.router)


@api_router.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/rules", tags=["meta"])
async def rules() -> RulesOut:
    """The System's rules (difficulty, ranks, streaks), from config. Public."""
    return rules_flow.get_rules()
