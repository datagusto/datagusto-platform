from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import uuid

from app.schemas.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    @staticmethod
    async def register_user(user_in: UserCreate, db: Session):
        """
        Register a new user in the local database.
        """
        try:
            # Initialize repository
            db_repo = UserRepository(db)
            
            # Check if user already exists
            existing_user = await db_repo.get_user_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user in local database
            db_user_data = {
                "id": uuid.uuid4(),  # Use UUID object for database
                "email": user_in.email,
                "name": user_in.name,
                "hashed_password": get_password_hash(user_in.password),
                "is_active": True,
                "email_confirmed": True  # For simplicity, auto-confirm email
            }
            
            user = await db_repo.create_user(db_user_data)
            
            return user
        except HTTPException:
            raise
        except Exception as e:
            # Rollback local database transaction
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(email: str, password: str, db: Session):
        """
        Login with email and password to get JWT token.
        """
        # Initialize repository
        db_repo = UserRepository(db)
        
        # Get user from database
        user = await db_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        } 