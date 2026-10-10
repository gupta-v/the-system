"""System notices in the System's voice (docs/design/lore-glossary.md §3)."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.titles import Title
from app.engine.types import HunterRank
from app.models.notice import Notice, NoticeType
from app.repositories.notice_repo import NoticeRepo
from app.utils.time import utcnow


def quest_arrived(title: str, goal_count: int) -> Notice:
    noun = "Goal" if goal_count == 1 else "Goals"
    return Notice(
        type=NoticeType.QUEST_ARRIVED,
        message=f"[Daily Quest: {title} has arrived. {goal_count} {noun}.]",
        data={"title": title, "goals": goal_count},
    )


def penalty_warning() -> Notice:
    return Notice(
        type=NoticeType.WARNING,
        message="[WARNING: Failure to complete the Daily Quest will result in an appropriate "
        "penalty.]",
    )


def recovery_day() -> Notice:
    return Notice(type=NoticeType.RECOVERY, message="[Recovery Day. Restore your strength.]")


def potion_acquired(held: int) -> Notice:
    return Notice(
        type=NoticeType.REWARD,
        message="[Reward: Recovery Potion acquired.]",
        data={"potions": held},
    )


def potion_bag_full(held: int) -> Notice:
    return Notice(
        type=NoticeType.REWARD,
        message="[Recovery Day cleared. Potion bag is full.]",
        data={"potions": held},
    )


def potion_used(left: int) -> Notice:
    return Notice(
        type=NoticeType.RECOVERY,
        message="[Recovery Potion used. Full Recovery.]",
        data={"potions": left},
    )


def quest_complete(xp: int, gold: int) -> Notice:
    return Notice(
        type=NoticeType.QUEST_COMPLETE,
        message=f"[Quest Complete. Rewards: +{xp} XP, +{gold} Gold.]",
        data={"xp": xp, "gold": gold},
    )


def level_up(old: int, new: int) -> Notice:
    return Notice(type=NoticeType.LEVEL_UP, message="[Level Up!]", data={"from": old, "to": new})


def rank_up(rank: HunterRank) -> Notice:
    return Notice(
        type=NoticeType.RANK_UP,
        message=f"[Hunter Rank: {rank}. The Daily Quest has been adjusted.]",
        data={"rank": rank},
    )


def penalty(description: str, xp_lost: int, penalty_id: UUID) -> Notice:
    return Notice(
        type=NoticeType.PENALTY,
        message=f"[You have entered the Penalty Zone.] [Penalty Quest: {description}]",
        data={"penalty_quest_id": penalty_id, "xp_lost": xp_lost},
    )


def penalty_cleared() -> Notice:
    return Notice(type=NoticeType.PENALTY_CLEARED, message="[Penalty Quest cleared. You survived.]")


def penalty_expired(count: int) -> Notice:
    return Notice(
        type=NoticeType.PENALTY_EXPIRED,
        message="[Penalty Quest failed. The System remembers.]",
        data={"count": count},
    )


def title_acquired(title: Title, gold: int) -> Notice:
    return Notice(
        type=NoticeType.TITLE_ACQUIRED,
        message=f"[Title acquired: {title.name}]",
        data={"code": title.code, "gold": gold},
    )


class NotificationService:
    """Stores notices raised outside a direct request (day close) until the UI fetches them."""

    def __init__(self, session: AsyncSession) -> None:
        self.notices = NoticeRepo(session)

    async def hold(self, user_id: UUID, notices: Sequence[Notice]) -> None:
        for n in notices:
            await self.notices.add(user_id, n.type, n.message, n.model_dump(mode="json")["data"])

    async def pop(self, user_id: UUID) -> list[Notice]:
        rows = await self.notices.pop_pending(user_id, utcnow())
        return [Notice(type=NoticeType(r.type), message=r.message, data=r.data) for r in rows]
