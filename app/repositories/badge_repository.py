from sqlmodel import Session, select
from app.models.entities import Badge, UserBadgeLink
from app.repositories.base_repository import BaseRepository

class BadgeRepository(BaseRepository[Badge]):
    def __init__(self, session: Session):
        super().__init__(session, Badge)

    def add_to_user(self, user_id: int, badge_id: int):
        link = UserBadgeLink(user_id=user_id, badge_id=badge_id)
        self.session.add(link)
        self.session.commit()
        return link