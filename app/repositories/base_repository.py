from typing import Generic, Type, TypeVar, Optional, Sequence
from sqlmodel import Session, select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        return self.session.get(self.model, id)

    def list_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        return self.session.exec(select(self.model).offset(offset).limit(limit)).all()

    def save(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.commit()