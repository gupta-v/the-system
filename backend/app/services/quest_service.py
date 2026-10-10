"""Daily Quests: generation, Goal logging, evaluation, Recovery Potions, Penalty Quests."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.game import (
    DIFFICULTY_RULES,
    PENALTY_QUESTS,
    POTION_USE_WINDOW_DAYS,
    STRIKE_WINDOW_DAYS,
)
from app.engine.day import DayResult, GoalProgress, evaluate_day
from app.engine.penalties import active_strikes
from app.engine.potions import PotionDay, can_use_potion, potion_walk
from app.engine.scaling import scaled_target
from app.engine.streak import current_streak
from app.engine.types import DayKind, DayStatus, Difficulty, GoalKind, HunterRank, Stat
from app.models.plan import DayPlan, PlannedGoal
from app.models.player import StatGoalOut
from app.repositories.db_schema import DailyQuest, GoalLog, PenaltyQuest
from app.repositories.quest_repo import QuestRepo
from app.utils.errors import InvalidAction, NotFound


class QuestService:
    def __init__(self, session: AsyncSession) -> None:
        self.quests = QuestRepo(session)

    # Daily Quests

    async def get(self, user_id: UUID, day: date) -> DailyQuest | None:
        return await self.quests.get_by_day(user_id, day)

    @staticmethod
    def _new_log(goal: PlannedGoal, rank: HunterRank, sort: int) -> GoalLog:
        target = goal.target
        if goal.scales_with_rank and goal.kind is GoalKind.NUMERIC:
            target = scaled_target(goal.target, rank, goal.f_target)
        return GoalLog(
            goal_id=goal.goal_id,
            name=goal.name,
            stat=goal.stat,
            kind=goal.kind,
            target=target,
            unit=goal.unit,
            weight=goal.weight,
            sets=goal.sets,
            sort=sort,
            progress=0.0,  # set now: a reissued quest is evaluated before the row is flushed
        )

    async def create(self, user_id: UUID, day: date, plan: DayPlan, rank: HunterRank) -> DailyQuest:
        quest = DailyQuest(
            user_id=user_id,
            day=day,
            title=plan.title,
            day_kind=plan.day_kind,
            status=DayStatus.OPEN,
            goal_logs=[self._new_log(g, rank, i) for i, g in enumerate(plan.goals)],
        )
        return await self.quests.add(quest)

    def reissue(self, quest: DailyQuest, plan: DayPlan, rank: HunterRank) -> None:
        """Rebuild an open Daily Quest from an edited plan. Goals that stay keep their progress."""
        kept = {log.goal_id: log for log in quest.goal_logs}
        logs = []
        for sort, goal in enumerate(plan.goals):
            log = kept.get(goal.goal_id) or self._new_log(goal, rank, sort)
            log.sort = sort
            log.sets = goal.sets  # picks up a Sets change; progress is kept
            logs.append(log)
        quest.title = plan.title
        quest.day_kind = plan.day_kind
        quest.goal_logs = logs

    async def open_goal_log(self, user_id: UUID, goal_log_id: UUID, today: date) -> GoalLog:
        log = await self.quests.get_goal_log(user_id, goal_log_id)
        if log is None:
            raise NotFound("[Goal not found.]")
        quest = await self.quests.get_by_day(user_id, today)
        if quest is None or quest.id != log.daily_quest_id or quest.status is not DayStatus.OPEN:
            raise InvalidAction("[This Daily Quest has ended.]")
        return log

    @staticmethod
    def set_progress(log: GoalLog, progress: float, now: datetime) -> None:
        if log.sets:
            # Snap to whole sets: k / sets of the target.
            done = min(max(round(progress / log.target * log.sets), 0), log.sets)
            progress = log.target if done == log.sets else round(log.target * done / log.sets, 4)
        elif log.kind is GoalKind.CHECK:
            progress = 1.0 if progress >= 1 else 0.0
        log.progress = progress
        log.completed_at = now if progress >= log.target else None

    @staticmethod
    def evaluate(quest: DailyQuest, difficulty: Difficulty) -> DayResult:
        goals = [
            GoalProgress(
                stat=log.stat,
                kind=log.kind,
                progress=log.progress,
                target=log.target,
                weight=log.weight,
            )
            for log in quest.goal_logs
        ]
        if not quest.potion_used:
            return evaluate_day(goals, difficulty, quest.day_kind)
        # A Recovery Potion only shields a Training day from failing: XP is paid in full and the
        # day is recorded as Recovery (no fail, no streak change).
        return replace(evaluate_day(goals, difficulty, DayKind.TRAINING), status=DayStatus.RECOVERY)

    @staticmethod
    def close(quest: DailyQuest, result: DayResult, now: datetime) -> None:
        quest.status = result.status
        quest.completion = result.completion
        quest.evaluated_at = now

    async def history(self, user_id: UUID, start: date, end: date) -> Sequence[DailyQuest]:
        if end < start:
            raise InvalidAction("[`from` must not be after `to`.]")
        if (end - start).days > 366:
            raise InvalidAction("[History range is limited to one year.]")
        return await self.quests.range(user_id, start, end)

    # Streaks and strikes

    async def streak(self, user_id: UUID) -> int:
        return current_streak(await self.day_statuses(user_id))

    async def day_statuses(self, user_id: UUID) -> list[DayStatus]:
        """Every Daily Quest's status, oldest first; today counts as CLEARED once fully cleared."""
        return [
            DayStatus.CLEARED
            if status is DayStatus.OPEN and completion >= 1 and kind is DayKind.TRAINING
            else status
            for status, completion, kind in await self.quests.day_results(user_id)
        ]

    async def potions_used(self, user_id: UUID) -> int:
        return len(await self.quests.potion_days_since(user_id, date.min))

    async def goals_done(self, user_id: UUID) -> int:
        return await self.quests.goals_done(user_id)

    async def strikes(self, user_id: UUID, today: date) -> int:
        since = today - timedelta(days=STRIKE_WINDOW_DAYS)
        return active_strikes(await self.quests.failed_days_since(user_id, since), today)

    # Recovery Potions

    async def potions(self, user_id: UUID, difficulty: Difficulty) -> int:
        """Recovery Potions held (earned on cleared Recovery Days, capped by difficulty)."""
        return (await self._potion_walk(user_id, difficulty))[0]

    async def potion_earned_days(self, user_id: UUID, difficulty: Difficulty) -> set[date]:
        """Game days whose cleared Recovery Day actually earned a Potion (bag not full)."""
        return (await self._potion_walk(user_id, difficulty))[1]

    async def _potion_walk(self, user_id: UUID, difficulty: Difficulty) -> tuple[int, set[date]]:
        history = await self.quests.potion_history(user_id)
        held, earned = potion_walk(
            (
                PotionDay(kind=k, completion=c, potion_used=u, has_goals=n > 0)
                for _, k, c, u, n in history
            ),
            DIFFICULTY_RULES[difficulty].max_potions,
        )
        return held, {h[0] for h, e in zip(history, earned, strict=True) if e}

    async def use_potion(self, quest: DailyQuest, difficulty: Difficulty) -> int:
        """Turn today into a Recovery Day. Returns Potions left."""
        if quest.status is not DayStatus.OPEN:
            raise InvalidAction("[This Daily Quest has ended.]")
        if quest.day_kind is DayKind.RECOVERY:
            raise InvalidAction("[Today is already a Recovery Day.]")
        if quest.day_kind is DayKind.STANDARD:
            raise InvalidAction("[Standard days can't fail. Keep your Potion for a Training day.]")
        if quest.goal_logs and quest.completion >= 1:
            raise InvalidAction("[Daily Quest already cleared. Keep your Potion.]")
        left = await self.potions(quest.user_id, difficulty)
        if left == 0:
            raise InvalidAction("[No Recovery Potions. Clear a Recovery Day to earn one.]")
        limit = DIFFICULTY_RULES[difficulty].max_potions
        since = quest.day - timedelta(days=POTION_USE_WINDOW_DAYS)
        if not can_use_potion(
            await self.quests.potion_days_since(quest.user_id, since), quest.day, limit
        ):
            raise InvalidAction(
                f"[Potion limit reached: {limit} per {POTION_USE_WINDOW_DAYS} days.]"
            )
        quest.day_kind = DayKind.RECOVERY
        quest.potion_used = True
        return left - 1

    # Penalty Quests

    async def issue_penalty(
        self, quest: DailyQuest, difficulty: Difficulty, due: datetime
    ) -> PenaltyQuest:
        return await self.quests.add_penalty(
            PenaltyQuest(
                user_id=quest.user_id,
                daily_quest_id=quest.id,
                description=PENALTY_QUESTS[difficulty],
                due=due,
            )
        )

    async def open_penalties(self, user_id: UUID) -> Sequence[PenaltyQuest]:
        return await self.quests.open_penalties(user_id)

    async def clear_penalty(self, user_id: UUID, penalty_id: UUID, now: datetime) -> None:
        penalty = await self.quests.get_penalty(user_id, penalty_id)
        if penalty is None:
            raise NotFound("[Penalty Quest not found.]")
        if penalty.status != "open" or penalty.due <= now:
            raise InvalidAction("[This Penalty Quest has ended.]")
        penalty.status = "cleared"
        penalty.cleared_at = now

    async def expire_penalties(self, user_id: UUID, now: datetime) -> int:
        overdue = await self.quests.overdue_penalties(user_id, now)
        for penalty in overdue:
            penalty.status = "expired"
        return len(overdue)

    async def goal_breakdown(self, user_id: UUID, stat: Stat) -> list[StatGoalOut]:
        return [
            StatGoalOut(name=name, done_days=done, total_days=total)
            for name, done, total in await self.quests.goal_breakdown(user_id, stat)
        ]
