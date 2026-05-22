from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql://admin:admin@localhost:5432/postgres")
    DEBUG: bool = Field(default=False)

    JWT_SECRET: str  # obrigatório — sem default para nunca subir com segredo exposto
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()