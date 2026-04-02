"""
Application configuration using Pydantic Settings.
All environment variables are loaded and validated here.
"""
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database — declare BEFORE REDIS_URL so validators can access via info.data
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "comadmin"
    POSTGRES_PASSWORD: str = "comadmin"
    POSTGRES_DB: str = "com_management"

    # Redis — declare AFTER DB so assemble_db_uri works
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = ""  # override via env or leave empty to auto-assemble

    # Project
    PROJECT_NAME: str = "Com Management API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production

    SQLALCHEMY_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_uri(cls, v: str, info) -> str:
        if v:
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v
        d = info.data
        return (
            f"postgresql+asyncpg://{d.get('POSTGRES_USER', '')}:{d.get('POSTGRES_PASSWORD', '')}"
            f"@{d.get('POSTGRES_SERVER', 'localhost')}:{d.get('POSTGRES_PORT', 5432)}/{d.get('POSTGRES_DB', 'com_management')}"
        )

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_uri(cls, v: str, info) -> str:
        if v:
            return v
        d = info.data
        host = d.get('REDIS_HOST', 'localhost')
        port = d.get('REDIS_PORT', 6379)
        return f"redis://{host}:{port}/0"

    # Auth / JWT
    SECRET_KEY: str = "change-me-in-production-use-32-char-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        env = info.data.get('ENVIRONMENT', 'development')
        if env == 'production' and len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        if v == "change-me-in-production-use-32-char-minimum" and env != "development":
            raise ValueError("You MUST change SECRET_KEY before deploying to production")
        if len(v) < 32:
            raise ValueError(f"SECRET_KEY must be at least 32 characters (got {len(v)})")
        return v

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
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS origins value: {v!r}")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # console | json


settings = Settings()
