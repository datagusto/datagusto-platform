import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "TodoApp API"
    API_V1_STR: str = "/api"
    
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    @field_validator("SUPABASE_URL", "SUPABASE_KEY", "DATABASE_URL")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Required environment variable is empty")
        return v


settings = Settings() 