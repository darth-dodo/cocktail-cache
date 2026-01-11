"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
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
    CREWAI_TRACING: bool = False  # Opt-in for external telemetry (sends data to CrewAI)

    # Performance Settings
    PARALLEL_CREWS: bool = True  # Enable parallel Recipe + Bottle execution

    # Session Settings
    SESSION_TTL_SECONDS: int = 3600  # Session expiry time (default: 1 hour)
    SESSION_CLEANUP_INTERVAL_SECONDS: int = 300  # Cleanup interval (default: 5 minutes)

    @model_validator(mode="after")
    def validate_api_key_for_production(self) -> "Settings":
        """Validate ANTHROPIC_API_KEY is set in production environments."""
        if self.APP_ENV == "production" and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required in production environment. "
                "Set the ANTHROPIC_API_KEY environment variable."
            )
        return self

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
