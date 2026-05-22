from sqlmodel import Session
from app.models.entities import Quest, Badge
from app.models.schema import (
    AdminAnalyticsResponse,
    UserMetricsDTO,
    UserDTO,
    QuestWithUserDTO,
    QuestDTO,
    QuestCreateRequest,
    EventCreateRequest,
)
from app.repositories.user_repository import UserRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.badge_repository import BadgeRepository


class AdminService:
    def __init__(self, session: Session):
        self.user_repo = UserRepository(session)
        self.quest_repo = QuestRepository(session)
        self.badge_repo = BadgeRepository(session)

    def get_analytics(self) -> AdminAnalyticsResponse:
        players = self.user_repo.get_all_players()
        users_metrics = [
            UserMetricsDTO(
                user=UserDTO.model_validate(p),
                total_completed=len(self.quest_repo.get_user_quests(p.id, status="approved")),
                active_quests=len(self.quest_repo.get_user_quests(p.id, status="pending")),
            )
            for p in players
        ]
        system_metrics = {
            "pending_analysis": self.quest_repo.get_quests_count_by_status("analyzing"),
            "total_approved": self.quest_repo.get_quests_count_by_status("approved"),
            "total_rejected": self.quest_repo.get_quests_count_by_status("rejected"),
            "total_players": len(players),
        }
        return AdminAnalyticsResponse(users_metrics=users_metrics, system_metrics=system_metrics)

    def get_analyzing_quests(self) -> list[QuestWithUserDTO]:
        quests = self.quest_repo.get_analyzing_quests()
        result = []
        for q in quests:
            player = self.user_repo.get_by_id(q.user_id)
            if player:
                result.append(QuestWithUserDTO(
                    quest=QuestDTO.model_validate(q),
                    user=UserDTO.model_validate(player),
                ))
        return result

    def create_quests(self, data: QuestCreateRequest) -> int:
        return self._distribute_quests(
            user_ids=data.target_user_ids,
            title=data.title,
            description=data.description,
            xp=data.xp,
            bits=data.bits,
            is_recurring=data.is_recurring,
        )

    def create_event(self, data: EventCreateRequest) -> int:
        event_badge = Badge(
            title=data.badge_title,
            description=data.badge_description,
            icon=data.badge_icon,
            card_image=data.badge_card_image,
            rarity=data.badge_rarity,
        )
        self.badge_repo.save(event_badge)

        return self._distribute_quests(
            user_ids=data.target_user_ids,
            title=data.title,
            description=data.description,
            xp=data.xp,
            bits=data.bits,
            event_badge_id=event_badge.id,
        )

    def reset_daily_quests(self) -> int:
        templates = self.quest_repo.get_recurring_templates()
        count = 0
        for title, desc, xp, bits, uid in templates:
            if not self.quest_repo.has_pending(uid, title):
                self.quest_repo.save(Quest(
                    title=title,
                    description=desc,
                    xp=xp,
                    bits=bits,
                    user_id=uid,
                    status="pending",
                    is_recurring=True,
                ))
                count += 1
        return count

    def _distribute_quests(
        self,
        user_ids: list[int],
        title: str,
        description: str | None,
        xp: int,
        bits: int,
        is_recurring: bool = False,
        event_badge_id: int | None = None,
    ) -> int:
        count = 0
        for uid in user_ids:
            if self.user_repo.get_by_id(uid):
                self.quest_repo.save(Quest(
                    title=title,
                    description=description,
                    xp=xp,
                    bits=bits,
                    user_id=uid,
                    status="pending",
                    is_recurring=is_recurring,
                    event_badge_id=event_badge_id,
                ))
                count += 1
        return count
