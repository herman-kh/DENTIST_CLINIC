import base64
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    JWT_ALGORITHM: str

    AUTH_SERVICE_URL: str
    TOKEN_URL: str

    EMAIL_KEY: str
    FROM_EMAIL: str

    AUTH_SERVICE_EXTERNAL: str
    MIN_HOURS_BEFORE_APPOINTMENT: int

    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_APPOINTMENT_CREATED_TOPIC: str
    KAFKA_GROUP_ID: str
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

settings = Settings()