from sqlmodel import Session, select, desc
from app.repositories.base_repository import BaseRepository
from app.models.entities import Log

class LogRepository(BaseRepository[Log]):
    def __init__(self, session: Session):
        super().__init__(session, Log)
        
    def create_log(self, user_id: int, message: str, log_type: str):
        new_log = Log(user_id=user_id, message=message, type=log_type)
        return self.save(new_log) # Usa o boilerplate do Base

    def get_latest_by_user(self, user_id: int, limit: int = 20):
        # Lógica específica de ordenação que o Base não conhece
        statement = select(Log).where(Log.user_id == user_id).order_by(desc(Log.created_at)).limit(limit)
        return self.session.exec(statement).all()