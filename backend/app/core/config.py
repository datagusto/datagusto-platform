"""
Application configuration using Pydantic Settings.

This module provides type-safe configuration management for the application.
All environment variables are defined here with validation and defaults.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic Settings for type-safe configuration management.
    Automatically loads from .env file if present.
    """

    # =========================================================================
    # Application Configuration
    # =========================================================================
    PROJECT_NAME: str = "DataGusto Platform API"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ENABLE_REGISTRATION: str = "true"

    # =========================================================================
    # Database Configuration
    # =========================================================================
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # Test database name
    TEST_POSTGRES_DB: str = "datagusto_test"

    # =========================================================================
    # JWT Configuration
    # =========================================================================
    JWT_SECRET_KEY: str = "development-secret-key-change-in-production-min-32-chars"
    JWT_REFRESH_SECRET_KEY: str = (
        "development-refresh-secret-key-change-in-production-min-32-chars"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # =========================================================================
    # LLM Configuration (for guardrail evaluation)
    # =========================================================================
    LLM_PROVIDER: str = ""
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_ENDPOINT: str = ""

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def check_jwt_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("JWT_REFRESH_SECRET_KEY")
    @classmethod
    def check_jwt_refresh_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_REFRESH_SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError(
                "JWT_REFRESH_SECRET_KEY must be at least 32 characters long"
            )
        return v

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def async_database_url(self) -> str:
        """
        Build async database URL for application use (asyncpg driver).

        Returns:
            Async PostgreSQL connection string
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """
        Build sync database URL for Alembic migrations (psycopg2 driver).

        Returns:
            Sync PostgreSQL connection string
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def test_async_database_url(self) -> str:
        """
        Build async test database URL (asyncpg driver).

        Returns:
            Async PostgreSQL test connection string
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
        )

    @property
    def test_sync_database_url(self) -> str:
        """
        Build sync test database URL for Alembic (psycopg2 driver).

        Returns:
            Sync PostgreSQL test connection string
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
        )


# Create global settings instance
settings = Settings()
