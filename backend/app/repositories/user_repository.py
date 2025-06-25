from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import User as UserModel
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """Repository for database user operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Async database session
        """
        super().__init__(db, UserModel)
    
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
        self.db.flush()  # Get ID without committing
        return db_user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID string
            
        Returns:
            User or None if not found
        """
        # Convert string to UUID for database query
        try:
            uuid_id = UUID(user_id)
            return self.db.query(UserModel).filter(UserModel.id == uuid_id).first()
        except ValueError:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User or None if not found
        """
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    async def update_user(self, user_id, user_data: Dict[str, Any]) -> Optional[UserModel]:
        """
        Update a user.
        
        Args:
            user_id: User ID (string or UUID)
            user_data: User data to update
            
        Returns:
            Updated user or None if not found
        """
        if isinstance(user_id, UUID):
            user_id = str(user_id)
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            setattr(user, key, value)
        
        self.db.flush()
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID string
            
        Returns:
            True if deleted, False if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        return True
    
    def commit(self):
        """Commit the transaction."""
        self.db.commit()
    
    def rollback(self):
        """Rollback the transaction."""
        self.db.rollback()