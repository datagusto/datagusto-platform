from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.user import User as UserModel


class UserRepository:
    """Repository for database user operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserModel:
        """
        Create a new user in the database.
        
        Args:
            user_data: User data
            
        Returns:
            Created user
        """
        db_user = UserModel(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User or None if not found
        """
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User or None if not found
        """
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[UserModel]:
        """
        Update a user.
        
        Args:
            user_id: User ID
            user_data: User data to update
            
        Returns:
            Updated user or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True 