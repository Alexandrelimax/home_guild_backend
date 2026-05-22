from collections import defaultdict
from sqlmodel import Session, select, func, col
from app.repositories.base_repository import BaseRepository
from app.models.entities import Quest

class QuestRepository(BaseRepository[Quest]):
    def __init__(self, session: Session):
        super().__init__(session, Quest)

    def get_user_quests(self, user_id: int, status: str = None):
        statement = select(Quest).where(Quest.user_id == user_id)
        if status:
            statement = statement.where(Quest.status == status)
        return self.session.exec(statement).all()

    def get_analyzing_quests(self):
        return self.session.exec(select(Quest).where(Quest.status == "analyzing")).all()

    def get_quests_count_by_status(self, status: str) -> int:
        statement = select(func.count()).select_from(Quest).where(Quest.status == status)
        return self.session.exec(statement).one()

    def get_total_quests_count(self) -> int:
        return self.session.exec(select(func.count()).select_from(Quest)).one()

    def get_quest_counts_by_user(self, user_ids: list[int]) -> dict[tuple[int, str], int]:
        """Retorna {(user_id, status): count} para os status 'approved' e 'pending'."""
        statement = (
            select(Quest.user_id, Quest.status, func.count())
            .where(col(Quest.user_id).in_(user_ids))
            .where(col(Quest.status).in_(["approved", "pending"]))
            .group_by(Quest.user_id, Quest.status)
        )
        return {(uid, status): count for uid, status, count in self.session.exec(statement).all()}

    def get_recurring_templates(self):
        statement = (
            select(Quest.title, Quest.description, Quest.xp, Quest.bits, Quest.user_id)
            .where(Quest.is_recurring == True)
            .distinct()
        )
        return self.session.exec(statement).all()

    def get_pending_recurring_pairs(self) -> set[tuple[int, str]]:
        """Retorna pares (user_id, title) de quests recorrentes já pendentes."""
        statement = (
            select(Quest.user_id, Quest.title)
            .where(Quest.is_recurring == True, Quest.status == "pending")
        )
        return set(self.session.exec(statement).all())

    def get_event_quests_by_user(self, user_id: int) -> list[Quest]:
        statement = (
            select(Quest)
            .where(Quest.user_id == user_id)
            .where(Quest.event_badge_id.is_not(None))
            .order_by(Quest.updated_at.desc())
        )
        return self.session.exec(statement).all()