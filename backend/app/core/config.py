import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "DataGusto Platform API"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )
    ENABLE_REGISTRATION: bool = (
        os.getenv("ENABLE_REGISTRATION", "false").lower() == "true"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def check_database_url_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def check_jwt_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_SECRET_KEY is required in production")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("JWT_REFRESH_SECRET_KEY")
    @classmethod
    def check_jwt_refresh_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError("JWT_REFRESH_SECRET_KEY is required in production")
        if len(v) < 32:
            raise ValueError(
                "JWT_REFRESH_SECRET_KEY must be at least 32 characters long"
            )
        return v


settings = Settings()
