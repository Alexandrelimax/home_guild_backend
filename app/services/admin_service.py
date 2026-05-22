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
from app.repositories.log_repository import LogRepository


class AdminService:
    def __init__(self, session: Session):
        self.user_repo = UserRepository(session)
        self.quest_repo = QuestRepository(session)
        self.badge_repo = BadgeRepository(session)
        self.log_repo = LogRepository(session)

    def get_analytics(self) -> AdminAnalyticsResponse:
        players = self.user_repo.get_all_players()
        player_ids = [p.id for p in players]

        # 1 query para todos os counts, em vez de 2 por player
        counts = self.quest_repo.get_quest_counts_by_user(player_ids)

        users_metrics = [
            UserMetricsDTO(
                user=UserDTO.model_validate(p),
                total_completed=counts.get((p.id, "approved"), 0),
                active_quests=counts.get((p.id, "pending"), 0),
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
        if not quests:
            return []

        # 1 query para todos os users, em vez de 1 por quest
        users = self.user_repo.get_by_ids(list({q.user_id for q in quests}))
        return [
            QuestWithUserDTO(
                quest=QuestDTO.model_validate(q),
                user=UserDTO.model_validate(users[q.user_id]),
            )
            for q in quests
            if q.user_id in users
        ]

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
        if not templates:
            return 0

        # 1 query para todos os pares já pendentes, em vez de 1 por template
        existing_pending = self.quest_repo.get_pending_recurring_pairs()
        count = 0
        for title, desc, xp, bits, uid in templates:
            if (uid, title) not in existing_pending:
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
                if event_badge_id is not None:
                    self.log_repo.create_log(
                        user_id=uid,
                        message=f"⚡ Novo Evento: {title}!",
                        log_type="event_assigned",
                    )
                count += 1
        return count
