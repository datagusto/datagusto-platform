from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
import os

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.user import UserCreate, User
from app.services.auth_service import AuthService
from app.core.security import decode_refresh_token, create_access_token
from datetime import timedelta

router = APIRouter()


@router.post("/register", response_model=User)
async def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user.
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    Login with email and password to get JWT token.
    """
    return await AuthService.login_user(form_data.username, form_data.password, db)


from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest) -> dict[str, str]:
    """
    Refresh access token using refresh token.
    """
    try:
        # Decode refresh token
        payload = decode_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user = Depends(get_current_user)) -> Any:
    """
    Get current user information.
    """
    return current_user 