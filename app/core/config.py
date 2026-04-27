from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_Name: str = "Simple AI Chatbot"
    APP_VERSION:str = "0.1.0"
    ENVIRONMENT:str = "development"

    class Config:
        env_file = ".env"

settings = Settings()