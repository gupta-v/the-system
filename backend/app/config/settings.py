"""Runtime settings, read from environment variables or backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo-root `database/`: local data files (SQLite .db, CSV/JSON exports, seeds). Git-ignored.
DATA_DIR = Path(__file__).resolve().parents[3] / "database"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SYSTEM_", extra="ignore")

    app_name: str = "The System"
    data_dir: Path = DATA_DIR
    database_url: str = f"sqlite+aiosqlite:///{(DATA_DIR / 'the_system.db').as_posix()}"
    jwt_secret: str = "change-me-in-env"
    jwt_expire_minutes: int = 60 * 24 * 14
    cookie_name: str = "system_session"
    cookie_secure: bool = False  # True behind HTTPS
    cors_origins: list[str] = ["http://localhost:5173"]
    # Testing only: a plan edit also rebuilds today's open Daily Quest. Normally edits apply from
    # the next day. Enable with SYSTEM_REISSUE_TODAY_ON_PLAN_EDIT=true in backend/.env.
    reissue_today_on_plan_edit: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
