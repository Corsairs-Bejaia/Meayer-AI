from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    INTERNAL_API_KEY: str = "shared-secret-with-nestjs-backend"
    OPENAI_API_KEY: str = ""
    LOG_LEVEL: str = "info"
    SERVICE_NAME: str = "ai-service"
    VERSION: str = "0.1.0"

    # Storage Configuration
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"

    # Agent Configuration
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.7
    ENABLE_GPT4O_FALLBACK: bool = True
    MAX_SELF_CORRECTION_RETRIES: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
