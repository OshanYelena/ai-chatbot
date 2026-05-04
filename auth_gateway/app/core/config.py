from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Auth Gateway"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (auth gateway has its own DB)
    DATABASE_URL: str

    # Password hashing rounds
    BCRYPT_ROUNDS: int = 12

    class Config:
        env_file = ".env"


settings = Settings()
