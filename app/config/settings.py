from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Banco de Dados
    DATABASE_URL: str = Field(
        default="postgresql://admin:admin@localhost:5432/postgres"
    )
    
    # Segurança (Importante para o AuthService)
    JWT_SECRET: str = Field(default="SUA_CHAVE_SUPER_SECRETA_ESTILO_GAMER")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 horas

    # CORS
    # Usar list[str] é ótimo, o Pydantic converte "url1,url2" do .env automaticamente
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora campos extras no .env que não estão na classe
    )

settings = Settings()