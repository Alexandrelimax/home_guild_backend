from typing import Generic, Type, TypeVar, Optional, Sequence, List
from sqlmodel import Session, select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: any) -> Optional[T]:
        "Busca um tipo T por ID, usando uma implementação genérica para qualquer modelo"
        return self.session.get(self.model, id)

    def list_all(self) -> Sequence[T]:
        "Busca uma lista de todos os registros do tipo T"
        return self.session.exec(select(self.model)).all()

    def save(self, entity: T) -> T:
        "Salva uma entidade do tipo T, fazendo commit e refresh"
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        "Deleta uma entidade do tipo T, fazendo commit"
        self.session.delete(entity)
        self.session.commit()