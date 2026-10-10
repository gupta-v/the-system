"""All SQLAlchemy table models: the single source of the DB schema (architecture/overview.md §4).

Ledgers (xp_events, stat_xp_events, gold_events) are the source of truth; level, stats and
gold are derived from them.
"""

from datetime import UTC, date, datetime, time
from enum import Enum as PyEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    TypeDecorator,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.engine import Dialect
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.engine.types import DayKind, DayStatus, Difficulty, GoalKind, Stat
from app.utils.time import utcnow


class UtcDateTime(TypeDecorator[datetime]):
    """Stores naive UTC, returns aware UTC (SQLite has no timezone support)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime; use app.utils.time.utcnow()")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class Base(AsyncAttrs, DeclarativeBase):
    type_annotation_map = {datetime: UtcDateTime, UUID: Uuid}


def _enum(enum_cls: type[PyEnum]) -> Enum:
    # Store enum values ("awakened"), not names; plain strings keep SQLite/Postgres alike.
    return Enum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [m.value for m in e],
        length=16,
    )


# --- Identity -------------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    reset_hour: Mapped[int] = mapped_column(Integer, default=4)
    difficulty: Mapped[Difficulty] = mapped_column(_enum(Difficulty), default=Difficulty.AWAKENED)
    difficulty_changed_on: Mapped[date | None] = mapped_column(Date)  # change allowed once a week
    day_start: Mapped[time] = mapped_column(Time, default=time(7, 0))
    check_ins: Mapped[str] = mapped_column(String(16), default="both")  # morning|evening|both
    # Hunter profile (Account). All optional; used later for body-metric analytics.
    sex: Mapped[str | None] = mapped_column(String(16))  # male|female|other
    birth_date: Mapped[date | None] = mapped_column(Date)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    equipped_title: Mapped[str | None] = mapped_column(String(64))
    awakened_on: Mapped[date | None] = mapped_column(Date)  # first game day; None = not onboarded
    last_evaluated_day: Mapped[date | None] = mapped_column(Date)


class UserTitle(Base):
    __tablename__ = "user_titles"
    __table_args__ = (UniqueConstraint("user_id", "title_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title_code: Mapped[str] = mapped_column(String(64))  # see app/config/titles.py
    earned_at: Mapped[datetime] = mapped_column(default=utcnow)


# --- Goals & Regimen (docs/design/regimen.md §8) ---------------------------------------------


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    stat: Mapped[Stat] = mapped_column(_enum(Stat))
    kind: Mapped[GoalKind] = mapped_column(_enum(GoalKind))
    target: Mapped[float] = mapped_column(Float, default=1.0)  # A-Rank target if scales_with_rank
    f_target: Mapped[float | None] = mapped_column(Float)  # custom F-Rank target (optional)
    unit: Mapped[str | None] = mapped_column(String(16))
    scales_with_rank: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    sets: Mapped[int | None] = mapped_column(Integer)  # optional: done in this many taps
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Regimen(Base):
    __tablename__ = "regimens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    path: Mapped[str] = mapped_column(String(16))  # interview preset
    daily_minutes: Mapped[int] = mapped_column(Integer, default=30)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    versions: Mapped[list["RegimenVersion"]] = relationship(
        back_populates="regimen", order_by="RegimenVersion.effective_from", lazy="raise"
    )


class RegimenVersion(Base):
    """A Regimen edit takes effect from a week's Monday, so past weeks keep their plan."""

    __tablename__ = "regimen_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    regimen_id: Mapped[UUID] = mapped_column(ForeignKey("regimens.id", ondelete="CASCADE"))
    effective_from: Mapped[date] = mapped_column(Date, index=True)
    day_kinds: Mapped[list[str]] = mapped_column(JSON)  # DayKind per weekday, Monday first
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    regimen: Mapped[Regimen] = relationship(back_populates="versions", lazy="raise")
    day_types: Mapped[list["DayType"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="DayType.sort",
        lazy="selectin",
    )
    week: Mapped[list["WeekScheduleEntry"]] = relationship(
        cascade="all, delete-orphan",
        order_by="[WeekScheduleEntry.weekday, WeekScheduleEntry.slot]",
        lazy="selectin",
    )


class DayType(Base):
    """A Routine (UI name): a named set of Goals. Up to 2 per weekday."""

    __tablename__ = "day_types"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    regimen_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("regimen_versions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(64))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped[RegimenVersion] = relationship(back_populates="day_types", lazy="raise")
    goals: Mapped[list["DayTypeGoal"]] = relationship(
        cascade="all, delete-orphan", order_by="DayTypeGoal.sort", lazy="selectin"
    )


class DayTypeGoal(Base):
    __tablename__ = "day_type_goals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    day_type_id: Mapped[UUID] = mapped_column(ForeignKey("day_types.id", ondelete="CASCADE"))
    goal_id: Mapped[UUID] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"))
    target_override: Mapped[float | None] = mapped_column(Float)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    goal: Mapped[Goal] = relationship(lazy="selectin")


class WeekScheduleEntry(Base):
    __tablename__ = "week_schedule"
    __table_args__ = (UniqueConstraint("regimen_version_id", "weekday", "slot"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    regimen_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("regimen_versions.id", ondelete="CASCADE")
    )
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday
    slot: Mapped[int] = mapped_column(Integer, default=0)  # 0 = first Routine (names the quest)
    day_type_id: Mapped[UUID] = mapped_column(ForeignKey("day_types.id", ondelete="CASCADE"))

    day_type: Mapped[DayType] = relationship(lazy="selectin")


# --- Daily Quests ---------------------------------------------------------------------------


class DailyQuest(Base):
    __tablename__ = "daily_quests"
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(80))  # Day Type name at generation time
    day_kind: Mapped[DayKind] = mapped_column(_enum(DayKind))
    status: Mapped[DayStatus] = mapped_column(_enum(DayStatus), default=DayStatus.OPEN)
    completion: Mapped[float] = mapped_column(Float, default=0.0)
    potion_used: Mapped[bool] = mapped_column(Boolean, default=False)
    seen_at: Mapped[datetime | None] = mapped_column()  # first open -> "[Daily Quest has arrived.]"
    evaluated_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    goal_logs: Mapped[list["GoalLog"]] = relationship(
        back_populates="daily_quest",
        cascade="all, delete-orphan",
        order_by="GoalLog.sort",
        lazy="selectin",
    )


class GoalLog(Base):
    """One Goal inside a Daily Quest. Snapshots target/weight so later Goal edits keep history."""

    __tablename__ = "goal_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    daily_quest_id: Mapped[UUID] = mapped_column(
        ForeignKey("daily_quests.id", ondelete="CASCADE"), index=True
    )
    goal_id: Mapped[UUID | None] = mapped_column(ForeignKey("goals.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(80))
    stat: Mapped[Stat] = mapped_column(_enum(Stat))
    kind: Mapped[GoalKind] = mapped_column(_enum(GoalKind))
    target: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(16))
    weight: Mapped[float] = mapped_column(Float)
    sets: Mapped[int | None] = mapped_column(Integer)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column()

    daily_quest: Mapped[DailyQuest] = relationship(back_populates="goal_logs", lazy="raise")


class PenaltyQuest(Base):
    __tablename__ = "penalty_quests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    daily_quest_id: Mapped[UUID] = mapped_column(ForeignKey("daily_quests.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(255))
    due: Mapped[datetime] = mapped_column()
    status: Mapped[str] = mapped_column(String(16), default="open")  # open|cleared|expired
    cleared_at: Mapped[datetime | None] = mapped_column()


# --- Ledgers --------------------------------------------------------------------------------


class XpEvent(Base):
    __tablename__ = "xp_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)  # game day the XP belongs to
    amount: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32))  # daily_quest|penalty|...
    ref_id: Mapped[UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class StatXpEvent(Base):
    __tablename__ = "stat_xp_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)
    stat: Mapped[Stat] = mapped_column(_enum(Stat))
    amount: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32))
    ref_id: Mapped[UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class GoldEvent(Base):
    __tablename__ = "gold_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)
    amount: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32))
    ref_id: Mapped[UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


# --- System notices -------------------------------------------------------------------------


class SystemNotice(Base):
    """Notices raised outside a direct Player action (day close, penalties), held until shown."""

    __tablename__ = "system_notices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(String(255))
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column()
