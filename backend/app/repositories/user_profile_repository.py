"""
User profile repository for database operations.

This repository handles user profile data (name, bio, avatar, etc.).
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import UserProfile
from app.repositories.base_repository import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for user profile database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, UserProfile)

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Get profile by user ID.

        Args:
            user_id: User UUID

        Returns:
            UserProfile or None if not found
        """
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_profile(
        self, user_id: UUID, profile_data: Dict[str, Any]
    ) -> UserProfile:
        """
        Create a new user profile.

        Args:
            user_id: User UUID
            profile_data: Profile data (name, bio, etc.)

        Returns:
            Created UserProfile

        Raises:
            IntegrityError: If profile already exists for user
        """
        profile = UserProfile(user_id=user_id, **profile_data)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def update_profile(
        self, user_id: UUID, update_data: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """
        Update user profile.

        Args:
            user_id: User UUID
            update_data: Data to update

        Returns:
            Updated UserProfile or None if not found
        """
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None

        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.flush()
        return profile

    async def delete_profile(self, user_id: UUID) -> bool:
        """
        Delete user profile.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return False

        await self.db.delete(profile)
        return True

    async def search_by_name(
        self, name_pattern: str, limit: int = 100, offset: int = 0
    ) -> list[UserProfile]:
        """
        Search profiles by name pattern.

        Args:
            name_pattern: Name search pattern (SQL LIKE pattern)
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip

        Returns:
            List of matching UserProfiles
        """
        stmt = (
            select(UserProfile)
            .where(UserProfile.name.ilike(f"%{name_pattern}%"))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


__all__ = ["UserProfileRepository"]
