import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "DataGusto Platform API"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    ENABLE_REGISTRATION: bool = os.getenv("ENABLE_REGISTRATION", "false").lower() == "true"
    
    @field_validator("DATABASE_URL")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Required environment variable is empty")
        return v


settings = Settings() 