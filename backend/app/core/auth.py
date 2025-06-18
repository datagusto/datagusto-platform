from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


class TokenData(BaseModel):
    user_id: Optional[str] = None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from database
    db_repo = UserRepository(db)
    db_user = await db_repo.get_user_by_id(user_id)
    if db_user is None:
        raise credentials_exception
    
    return db_user


def get_current_user_sync(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Synchronous version of get_current_user for compatibility"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from database (synchronous)
    from app.models.user import User as UserModel
    from uuid import UUID
    try:
        uuid_id = UUID(user_id)
        db_user = db.query(UserModel).filter(UserModel.id == uuid_id).first()
    except ValueError:
        raise credentials_exception
    
    if db_user is None:
        raise credentials_exception
    
    return db_user


async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 