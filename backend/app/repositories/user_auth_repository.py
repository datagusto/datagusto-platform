"""
User authentication repository for database operations.

This repository handles password-based authentication credentials.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import UserLoginPassword
from app.repositories.base_repository import BaseRepository


class UserAuthRepository(BaseRepository[UserLoginPassword]):
    """Repository for user authentication database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, UserLoginPassword)

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserLoginPassword]:
        """
        Get authentication credentials by user ID.

        Args:
            user_id: User UUID

        Returns:
            UserLoginPassword or None if not found
        """
        stmt = select(UserLoginPassword).where(UserLoginPassword.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserLoginPassword]:
        """
        Get authentication credentials by email.

        Args:
            email: User email address

        Returns:
            UserLoginPassword or None if not found
        """
        stmt = select(UserLoginPassword).where(UserLoginPassword.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_password_auth(
        self, user_id: UUID, email: str, hashed_password: str
    ) -> UserLoginPassword:
        """
        Create password authentication for user.

        Args:
            user_id: User UUID
            email: User email address
            hashed_password: Bcrypt hashed password

        Returns:
            Created UserLoginPassword

        Raises:
            IntegrityError: If email already exists or user already has auth
        """
        auth = UserLoginPassword(
            user_id=user_id,
            email=email,
            hashed_password=hashed_password,
            password_algorithm="bcrypt",
        )
        self.db.add(auth)
        await self.db.flush()
        return auth

    async def update_password(
        self, user_id: UUID, new_hashed_password: str
    ) -> Optional[UserLoginPassword]:
        """
        Update user password.

        Args:
            user_id: User UUID
            new_hashed_password: New bcrypt hashed password

        Returns:
            Updated UserLoginPassword or None if not found
        """
        auth = await self.get_by_user_id(user_id)
        if not auth:
            return None

        auth.hashed_password = new_hashed_password
        await self.db.flush()
        return auth

    async def update_email(
        self, user_id: UUID, new_email: str
    ) -> Optional[UserLoginPassword]:
        """
        Update user email.

        Args:
            user_id: User UUID
            new_email: New email address

        Returns:
            Updated UserLoginPassword or None if not found

        Raises:
            IntegrityError: If email already exists
        """
        auth = await self.get_by_user_id(user_id)
        if not auth:
            return None

        auth.email = new_email
        await self.db.flush()
        return auth

    async def delete_password_auth(self, user_id: UUID) -> bool:
        """
        Delete password authentication for user.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        auth = await self.get_by_user_id(user_id)
        if not auth:
            return False

        await self.db.delete(auth)
        return True

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email address to check

        Returns:
            True if exists, False otherwise
        """
        stmt = select(UserLoginPassword.id).where(UserLoginPassword.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None


__all__ = ["UserAuthRepository"]
