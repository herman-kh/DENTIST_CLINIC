import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_URL: str
    
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_APPOINTMENT_CREATED_TOPIC: str
    KAFKA_GROUP_ID: str

    EMAIL_KEY: str
    FROM_EMAIL: str
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

settings = Settings()