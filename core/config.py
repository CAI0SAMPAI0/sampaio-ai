from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str

    # jwt
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_days: int = 365
    refresh_token_expire_days: int = 7

    # AI
    groq_api_key: str

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
    ]

    debug: bool = False


settings = Settings()
