from typing import Optional
from sqlmodel import Session, select
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