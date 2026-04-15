"""Configuration du serveur FastAPI via variables d'environnement."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Serveur
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    SECRET_KEY: str = "change_me_in_production"

    # Base de données
    DATABASE_URL: str = "sqlite:///./server/db/gaming.db"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://127.0.0.1"]

    # Client
    API_BASE_URL: str = "http://localhost:8000/api"


settings = Settings()
