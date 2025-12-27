"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars not defined in Settings
    )

    # API Keys
    ANTHROPIC_API_KEY: str = ""

    # Application Settings
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CrewAI Settings
    CREWAI_TRACING: bool = False  # Enable CrewAI flow tracing

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV == "production"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.APP_ENV == "test"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
