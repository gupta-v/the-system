"""Regimen: Goals, Day Types, week schedule, versioned edits and Daily Quest planning.

Day Types are shown as Routines. Quest generation for a date (regimen.md §8): the weekday's
day kind, plus its Routines (max 2) -> their Goals merged; the first Routine names the quest.
Rank scaling is applied by quest_service when the Daily Quest is created.
"""

from collections.abc import Sequence
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.presets import (
    DAY_TYPE_NAMES,
    DEFAULT_ROUTINE_GOALS,
    DEFAULT_ROUTINE_NAME,
    GOAL_LIBRARY,
    PATHS,
    REST_DAY_NAME,
)
from app.engine.types import DayKind, GoalKind
from app.models.plan import DayPlan, PlannedGoal
from app.models.regimen import (
    AwakeningIn,
    DayTypeGoalIn,
    DayTypeGoalOut,
    DayTypeIn,
    DayTypeOut,
    EditScope,
    GoalIn,
    GoalPatch,
    RegimenIn,
    RegimenOut,
)
from app.repositories.db_schema import (
    DayType,
    DayTypeGoal,
    Goal,
    Regimen,
    RegimenVersion,
    WeekScheduleEntry,
)
from app.repositories.regimen_repo import RegimenRepo
from app.utils.errors import InvalidAction, NotFound


def week_start(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())


def _planned(goal: Goal, target_override: float | None = None) -> PlannedGoal:
    return PlannedGoal(
        goal_id=goal.id,
        name=goal.name,
        stat=goal.stat,
        kind=goal.kind,
        target=target_override or goal.target,
        f_target=goal.f_target,
        scales_with_rank=goal.scales_with_rank,
        unit=goal.unit,
        weight=goal.weight,
        sets=goal.sets,
    )


def _goal_out(goal: Goal, target_override: float | None) -> DayTypeGoalOut:
    return DayTypeGoalOut(
        goal_id=goal.id,
        name=goal.name,
        stat=goal.stat,
        target=goal.target,
        unit=goal.unit,
        target_override=target_override,
    )


def _snapshot(version: RegimenVersion) -> RegimenIn:
    """A version as an edit payload, used to carry the old plan past a "this week" edit."""
    return RegimenIn(
        day_types=[
            DayTypeIn(
                name=dt.name,
                goals=[
                    DayTypeGoalIn(goal_id=g.goal_id, target_override=g.target_override)
                    for g in dt.goals
                ],
            )
            for dt in version.day_types
        ],
        day_kinds=[DayKind(k) for k in version.day_kinds],
        week=_week_names(version),
    )


def _week_names(version: RegimenVersion) -> list[list[str]]:
    """Routine names per weekday (`version.week` is ordered by weekday, slot)."""
    by_id = {dt.id: dt.name for dt in version.day_types}
    week: list[list[str]] = [[] for _ in range(7)]
    for entry in version.week:
        week[entry.weekday].append(by_id[entry.day_type_id])
    return week


class RegimenService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RegimenRepo(session)

    # Goals

    async def list_goals(self, user_id: UUID, include_archived: bool) -> Sequence[Goal]:
        return await self.repo.list_goals(user_id, include_archived)

    async def get_goal(self, user_id: UUID, goal_id: UUID) -> Goal:
        goal = await self.repo.get_goal(user_id, goal_id)
        if goal is None:
            raise NotFound("[Goal not found.]")
        return goal

    async def create_goal(self, user_id: UUID, data: GoalIn) -> Goal:
        return await self.repo.add_goal(Goal(user_id=user_id, **data.model_dump()))

    async def update_goal(self, user_id: UUID, goal_id: UUID, patch: GoalPatch) -> Goal:
        goal = await self.get_goal(user_id, goal_id)
        changes = patch.model_dump(exclude_unset=True)
        if goal.kind is GoalKind.CHECK and changes.get("target", 1.0) != 1.0:
            raise InvalidAction("[Check Goals have target 1.]")
        for field, value in changes.items():
            if value is None and field not in ("f_target", "unit", "sets"):
                continue  # null only clears optional fields
            setattr(goal, field, value)
        if goal.f_target is not None and goal.f_target > goal.target:
            raise InvalidAction("[F-Rank target must not exceed the A-Rank target.]")
        return goal

    async def archive_goal(self, user_id: UUID, goal_id: UUID) -> None:
        """Archived Goals drop out of future Daily Quests; logged history keeps them."""
        (await self.get_goal(user_id, goal_id)).archived = True

    # Regimen

    async def create_from_awakening(self, user_id: UUID, answers: AwakeningIn, today: date) -> None:
        layout = PATHS[answers.path]
        extras = list(dict.fromkeys([*DEFAULT_ROUTINE_GOALS, *answers.extras]))
        # Standard days run the Default Routine, so only Training and Recovery layouts are used.
        kinds = (DayKind.TRAINING, DayKind.RECOVERY)
        codes = {code for kind in kinds for code in layout[kind]} | set(extras)
        goals: dict[str, Goal] = {}
        for code in sorted(codes):
            preset = GOAL_LIBRARY[code]
            goals[code] = await self.repo.add_goal(
                Goal(
                    user_id=user_id,
                    name=preset.name,
                    stat=preset.stat,
                    kind=preset.kind,
                    target=preset.target,
                    unit=preset.unit,
                    scales_with_rank=preset.scales_with_rank,
                )
            )

        def kind_for(weekday: int) -> DayKind:
            if weekday in answers.training_days:
                return DayKind.TRAINING
            if weekday in answers.recovery_days:
                return DayKind.RECOVERY
            return DayKind.STANDARD

        routines = [
            DayTypeIn(
                name=DAY_TYPE_NAMES[kind],
                # Extras live in the Default Routine, so drop them here to avoid doubles.
                goals=[
                    DayTypeGoalIn(goal_id=goals[code].id)
                    for code in layout[kind]
                    if code not in extras
                ],
            )
            for kind in kinds
        ]
        routines.append(
            DayTypeIn(
                name=DEFAULT_ROUTINE_NAME,
                goals=[DayTypeGoalIn(goal_id=goals[code].id) for code in extras],
            )
        )
        spec = RegimenIn(
            day_types=routines,
            day_kinds=[kind_for(d) for d in range(7)],
            week=[
                []
                if kind_for(d) is DayKind.STANDARD
                else [DAY_TYPE_NAMES[kind_for(d)], DEFAULT_ROUTINE_NAME]
                for d in range(7)
            ],
        )
        await self.repo.deactivate_all(user_id)
        regimen = await self.repo.add_regimen(
            Regimen(
                user_id=user_id,
                name="Regimen",
                path=answers.path,
                daily_minutes=answers.daily_minutes,
            )
        )
        await self._add_version(user_id, regimen.id, week_start(today), spec)

    async def _active(self, user_id: UUID) -> Regimen:
        regimen = await self.repo.active_regimen(user_id)
        if regimen is None:
            raise NotFound("[No active Regimen. Complete your Awakening first.]")
        return regimen

    async def _add_version(
        self, user_id: UUID, regimen_id: UUID, effective_from: date, spec: RegimenIn
    ) -> RegimenVersion:
        goal_ids = {g.goal_id for dt in spec.day_types for g in dt.goals}
        goals = {g.id: g for g in await self.repo.list_goals(user_id) if g.id in goal_ids}
        missing = goal_ids - goals.keys()
        if missing:
            raise InvalidAction(f"[Unknown or archived Goals: {sorted(map(str, missing))}]")

        day_types = {
            dt.name: DayType(
                name=dt.name,
                sort=sort,
                goals=[
                    DayTypeGoal(goal=goals[g.goal_id], target_override=g.target_override, sort=i)
                    for i, g in enumerate(dt.goals)
                ],
            )
            for sort, dt in enumerate(spec.day_types)
        }
        version = RegimenVersion(
            regimen_id=regimen_id,
            effective_from=effective_from,
            day_kinds=list(spec.day_kinds),
            day_types=list(day_types.values()),
            week=[
                WeekScheduleEntry(weekday=d, slot=slot, day_type=day_types[name])
                for d, names in enumerate(spec.week)
                for slot, name in enumerate(names)
            ],
        )
        return await self.repo.add_version(version)

    async def replace(self, user_id: UUID, spec: RegimenIn, today: date) -> None:
        """Edit the Regimen from this week on. "this_week" restores the old plan next Monday."""
        regimen = await self._active(user_id)
        monday = week_start(today)
        next_monday = monday + timedelta(days=7)
        if spec.scope is EditScope.THIS_WEEK:
            later = await self.repo.versions_from(regimen.id, next_monday)
            current = await self.repo.version_for(regimen.id, monday)
            if not later and current is not None:
                await self._add_version(user_id, regimen.id, next_monday, _snapshot(current))
            replaced = [
                v
                for v in await self.repo.versions_from(regimen.id, monday)
                if v.effective_from == monday
            ]
        else:
            replaced = list(await self.repo.versions_from(regimen.id, monday))
        for version in replaced:
            await self.repo.delete_version(version)
        await self._add_version(user_id, regimen.id, monday, spec)

    async def view(self, user_id: UUID, today: date) -> RegimenOut:
        regimen = await self._active(user_id)
        version = await self.repo.version_for(regimen.id, today)
        if version is None:
            raise NotFound("[No Regimen in effect.]")
        return RegimenOut(
            id=regimen.id,
            name=regimen.name,
            path=regimen.path,
            daily_minutes=regimen.daily_minutes,
            effective_from=version.effective_from,
            day_types=[
                DayTypeOut(
                    name=dt.name,
                    goals=[_goal_out(g.goal, g.target_override) for g in dt.goals],
                )
                for dt in version.day_types
            ],
            day_kinds=[DayKind(k) for k in version.day_kinds],
            week=_week_names(version),
        )

    async def plan_for(self, user_id: UUID, day: date) -> DayPlan:
        regimen = await self._active(user_id)
        version = await self.repo.version_for(regimen.id, day)
        if version is None:
            return DayPlan(title=DAY_TYPE_NAMES[DayKind.STANDARD], day_kind=DayKind.STANDARD)
        kind = DayKind(version.day_kinds[day.weekday()])
        routines = [e.day_type for e in version.week if e.weekday == day.weekday()]
        title = routines[0].name if routines else DAY_TYPE_NAMES[kind]
        if kind is DayKind.STANDARD:
            routines = [dt for dt in version.day_types if dt.name == DEFAULT_ROUTINE_NAME]
        if not routines:
            title = REST_DAY_NAME if kind is DayKind.RECOVERY else title
            return DayPlan(title=title, day_kind=kind)
        pairs = [(g.goal, g.target_override) for r in routines for g in r.goals]
        goals: list[PlannedGoal] = []
        seen: set[UUID] = set()
        for goal, override in pairs:
            if goal.archived or goal.id in seen:
                continue
            seen.add(goal.id)
            goals.append(_planned(goal, override))
        return DayPlan(title=title, day_kind=kind, goals=goals)
