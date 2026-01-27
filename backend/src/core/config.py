"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://tracker:tracker_dev_password@localhost:5432/tunisia_tracker"
    database_sync_url: str = "postgresql://tracker:tracker_dev_password@localhost:5432/tunisia_tracker"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    api_key_salt: str = "dev-api-key-salt-change-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Application
    debug: bool = False
    app_name: str = "Tunisia Price Tracker"
    api_v1_prefix: str = "/api/v1"

    # Scraping
    default_rate_limit_ms: int = 1000
    max_concurrent_browsers: int = 3
    browser_headless: bool = True
    scrape_timeout_seconds: int = 60

    # Search
    default_search_limit: int = 20
    min_search_score: float = 0.3


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
