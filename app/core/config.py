from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_Name: str = "Simple AI Chatbot"
    APP_VERSION:str = "0.1.0"
    ENVIRONMENT:str = "development"

    OPENAI_API_KEY: str
    OPENAI_MODEL:str = "gpt-40-mini"

    MAX_HISTORY_MESSAGES: int = 10
    SUMMARY_TRIGGER_MESSAGES: int = 12
    RECENT_MESSAGES_AFTER_SUMMARY: int = 6

    class Config:
        env_file = ".env"

settings = Settings()