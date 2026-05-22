from typing import Optional
from sqlmodel import Session, select, col
from app.repositories.base_repository import BaseRepository
from app.models.entities import User

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(self.model).where(self.model.email == email)
        return self.session.exec(statement).first()

    def get_all_players(self) -> list[User]:
        statement = select(self.model).where(self.model.role == "user")
        return self.session.exec(statement).all()

    def get_by_ids(self, user_ids: list[int]) -> dict[int, User]:
        """Busca múltiplos usuários de uma vez, retorna dict {id: User}."""
        statement = select(self.model).where(col(self.model.id).in_(user_ids))
        return {u.id: u for u in self.session.exec(statement).all()}