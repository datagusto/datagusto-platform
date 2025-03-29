from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.supabase_repository import SupabaseUserRepository
from app.repositories.user_repository import UserRepository
from app.repositories.agent_repository import AgentRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key")


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
        # Verify token with Supabase
        supabase_repo = SupabaseUserRepository()
        user_response = await supabase_repo.get_user(token)
        user_id = user_response.user.id
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


async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_agent_from_api_key(
    api_key: str = Depends(api_key_header), 
    db: Session = Depends(get_db)
):
    """
    Dependency to get the agent from an API key.
    
    Args:
        api_key: API key from header
        db: Database session
        
    Returns:
        The agent if the API key is valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "APIKey"},
    )
    
    try:
        agent_repo = AgentRepository(db)
        agent = await agent_repo.get_agent_by_api_key(api_key)
        
        if agent is None:
            raise credentials_exception
            
        if agent.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent is not active"
            )
            
        return agent
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise credentials_exception 