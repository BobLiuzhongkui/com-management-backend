"""
Application configuration using Pydantic Settings.
All environment variables are loaded and validated here.
"""
from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Project
    PROJECT_NAME: str = "Com Management API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "comadmin"
    POSTGRES_PASSWORD: str = "comadmin"
    POSTGRES_DB: str = "com_management"
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_uri(cls, v: str | None, info) -> str:
        if isinstance(v, str):
            return v
        d = info.data
        return (
            f"postgresql://{d.get('POSTGRES_USER')}:{d.get('POSTGRES_PASSWORD')}"
            f"@{d.get('POSTGRES_SERVER')}:{d.get('POSTGRES_PORT')}/{d.get('POSTGRES_DB')}"
        )

    # Redis
    REDIS_URL: RedisDsn | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_uri(cls, v: str | None, info) -> str:
        if isinstance(v, str):
            return v
        d = info.data
        return f"redis://{d.get('REDIS_HOST')}:{d.get('REDIS_PORT')}/0"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v  # type: ignore[return-value]
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # console, json


settings = Settings()
