from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_Name: str = "Simple AI Chatbot"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    MAX_HISTORY_MESSAGES: int = 10
    SUMMARY_TRIGGER_MESSAGES: int = 12
    RECENT_MESSAGES_AFTER_SUMMARY: int = 6

    OPENAI_TIMEOUT_SECONDS: int = 20
    OPENAI_MAX_RETRIES: int = 2

    PENDING_CONFLICT_TTL_HOURS: int = 24

    DATABASE_URL: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    # URL of the separate auth gateway service
    AUTH_GATEWAY_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


settings = Settings()
