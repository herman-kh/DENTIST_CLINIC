import base64
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    EMAIL_KEY : str
    FROM_EMAIL : str
    REDIS_URL: str
    SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str

    GOOGLE_CLIENT_SECRET: str
    GOOGLE_CLIENT_ID: str

    REDIRECT_URL:str

    JWT_ALGORITHM : str
    JWT_EXPIRE_MINUTES: int
    JWT_REFRESH_DAYS: int
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

settings = Settings()