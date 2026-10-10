"""FastAPI app: routers, CORS and error handling.

Run: uv run uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.router import api_router
from app.config.settings import get_settings
from app.utils.errors import DomainError

logger = logging.getLogger("the_system")


def _error(status_code: int, message: str) -> JSONResponse:
    # Same shape as FastAPI's own errors ({"detail": ...}) so the client handles one format.
    return JSONResponse(status_code=status_code, content={"detail": message})


async def _domain_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return _error(exc.status_code, exc.message)


async def _integrity_error(request: Request, exc: Exception) -> JSONResponse:
    # Usually a race on a unique constraint (e.g. two first opens of the same day).
    logger.warning("integrity error on %s %s: %s", request.method, request.url.path, exc)
    return _error(409, "[Conflict. Try again.]")


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return _error(500, "[The System has encountered an error.]")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(IntegrityError, _integrity_error)
    app.add_exception_handler(Exception, _unhandled_error)
    app.include_router(api_router)
    return app


app = create_app()
