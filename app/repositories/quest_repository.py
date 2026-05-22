from sqlmodel import Session, select, func
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
        statement = select(Quest).where(Quest.status == "analyzing")
        return self.session.exec(statement).all()

    def get_quests_count_by_status(self, status: str) -> int:
        statement = select(func.count()).select_from(Quest).where(Quest.status == status)
        return self.session.exec(statement).one()

    def get_total_quests_count(self) -> int:
        statement = select(func.count()).select_from(Quest)
        return self.session.exec(statement).one()

    def get_recurring_templates(self):
        statement = (
            select(Quest.title, Quest.description, Quest.xp, Quest.bits, Quest.user_id)
            .where(Quest.is_recurring == True)
            .distinct()
        )
        return self.session.exec(statement).all()

    def has_pending(self, user_id: int, title: str) -> bool:
        statement = select(Quest).where(
            Quest.user_id == user_id,
            Quest.title == title,
            Quest.status == "pending",
        )
        return self.session.exec(statement).first() is not None