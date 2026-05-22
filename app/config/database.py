from sqlmodel import Session, create_engine, SQLModel
from app.config.settings import settings

# A URL virá do seu settings.py (ex: postgresql://user:pass@localhost:5432/db)
engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session