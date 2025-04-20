from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
import os

from app.core.database import get_db
from app.schemas.user import UserCreate, User
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=User)
async def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user with Supabase.
    """
    enable_registration = os.getenv("ENABLE_REGISTRATION", "false").lower() == "true"
    
    if not enable_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="New user registration is temporarily disabled."
        )
    
    return await AuthService.register_user(user_in, db)


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> dict[str, str]:
    """
    Login with email and password to get JWT token.
    """
    return await AuthService.login_user(form_data.username, form_data.password) 