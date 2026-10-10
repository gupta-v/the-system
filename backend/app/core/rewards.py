"""Keep the XP/Gold/stat ledgers in step with a Daily Quest's progress.

The ledger for a Daily Quest always equals `evaluate_day` of its current Goal progress: every
change writes only the difference. So XP shows up the moment a Goal is logged, lowering progress
takes XP back, and day close just finalises the status.
"""

from dataclasses import dataclass

from app.core.context import Services
from app.engine.types import DayKind, Stat
from app.models.notice import Notice
from app.repositories.db_schema import DailyQuest, Profile
from app.services import notification_service as notify
from app.services.player_service import DAILY_QUEST_SOURCE


@dataclass(frozen=True)
class RewardSync:
    xp: int
    gold: int
    notices: list[Notice]


async def sync_quest_rewards(svc: Services, profile: Profile, quest: DailyQuest) -> RewardSync:
    user_id = profile.user_id
    was_complete = quest.completion >= 1.0
    # Clearing a Recovery Day earns a Recovery Potion: note the balance to report a change.
    tracks_potion = quest.day_kind is DayKind.RECOVERY and not quest.potion_used
    potions_before = await svc.quests.potions(user_id, profile.difficulty) if tracks_potion else 0
    result = svc.quests.evaluate(quest, profile.difficulty)
    quest.completion = result.completion

    prev_xp, prev_gold, prev_stats = await svc.player.awarded_for(
        user_id, DAILY_QUEST_SOURCE, quest.id
    )
    stat_delta = {
        stat: result.stat_xp.get(stat, 0) - prev_stats.get(stat, 0)
        for stat in Stat
        if result.stat_xp.get(stat, 0) != prev_stats.get(stat, 0)
    }
    award = await svc.player.award(
        user_id,
        quest.day,
        xp=result.xp - prev_xp,
        gold=result.gold - prev_gold,
        stat_xp=stat_delta,
        source=DAILY_QUEST_SOURCE,
        ref_id=quest.id,
    )

    notices: list[Notice] = []
    completed_now = not was_complete and result.completion >= 1.0 and quest.goal_logs
    if completed_now and quest.day_kind is not DayKind.RECOVERY:
        notices.append(notify.quest_complete(result.xp, result.gold))
    if tracks_potion and completed_now:
        held = await svc.quests.potions(user_id, profile.difficulty)
        notices.append(
            notify.potion_acquired(held) if held > potions_before else notify.potion_bag_full(held)
        )
    if award.after.level > award.before.level:
        notices.append(notify.level_up(award.before.level, award.after.level))
        if award.after.rank != award.before.rank:
            notices.append(notify.rank_up(award.after.rank))
    return RewardSync(xp=result.xp - prev_xp, gold=result.gold - prev_gold, notices=notices)
