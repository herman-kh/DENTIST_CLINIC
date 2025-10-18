import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    JWT_ALGORITHM: str

    AUTH_SERVICE_URL: str
    TOKEN_URL: str

    AUTH_SERVICE_EXTERNAL: str
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

settings = Settings()