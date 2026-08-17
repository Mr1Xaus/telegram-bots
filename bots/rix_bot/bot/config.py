import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    bot_token: str
    postgres_url: str = "sqlite+aiosqlite:///rix.db"
    redis_url: str = "redis://localhost:6379/0"
    owner_id: int = 0
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
