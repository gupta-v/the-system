"""Services for one unit of work. Core flows compose these; services never call each other."""

from dataclasses import dataclass

from app.core.unit_of_work import UnitOfWork
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.player_service import PlayerService
from app.services.quest_service import QuestService
from app.services.regimen_service import RegimenService


@dataclass(frozen=True)
class Services:
    auth: AuthService
    player: PlayerService
    quests: QuestService
    regimen: RegimenService
    notifications: NotificationService

    @classmethod
    def of(cls, uow: UnitOfWork) -> "Services":
        s = uow.session
        return cls(
            auth=AuthService(s),
            player=PlayerService(s),
            quests=QuestService(s),
            regimen=RegimenService(s),
            notifications=NotificationService(s),
        )
