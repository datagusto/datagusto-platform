"""
User repository for database operations.

This repository handles operations for the User model and its related tables
(profile, authentication, status). It provides methods for common user
operations in a multi-tenant environment.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.models.user import (
    User,
    UserLoginPassword,
    UserActiveStatus,
    UserSuspension,
    UserArchive,
)
from app.models.organization import OrganizationMember
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user database operations with multi-tenant support."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, User)

    async def get_by_id_with_relations(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID with all related data (profile, login, status).

        Args:
            user_id: User UUID

        Returns:
            User with related data or None if not found
        """
        stmt = (
            select(User)
            .options(
                joinedload(User.profile),
                joinedload(User.login_password),
                joinedload(User.active_status),
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address (queries UserLoginPassword table).

        Args:
            email: User email address

        Returns:
            User or None if not found
        """
        stmt = (
            select(User).join(UserLoginPassword).where(UserLoginPassword.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_with_relations(self, email: str) -> Optional[User]:
        """
        Get user by email with all related data.

        Args:
            email: User email address

        Returns:
            User with related data or None if not found
        """
        stmt = (
            select(User)
            .join(UserLoginPassword)
            .options(
                joinedload(User.profile),
                joinedload(User.login_password),
                joinedload(User.active_status),
            )
            .where(UserLoginPassword.email == email)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def is_active(self, user_id: UUID) -> bool:
        """
        Check if user is active (has entry in user_active_status).

        Args:
            user_id: User UUID

        Returns:
            True if active, False otherwise
        """
        stmt = select(UserActiveStatus).where(UserActiveStatus.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_suspended(self, user_id: UUID) -> bool:
        """
        Check if user is currently suspended (has suspension record).

        Args:
            user_id: User UUID

        Returns:
            True if suspended, False otherwise
        """
        stmt = select(UserSuspension).where(UserSuspension.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_archived(self, user_id: UUID) -> bool:
        """
        Check if user is archived (soft deleted).

        Args:
            user_id: User UUID

        Returns:
            True if archived, False otherwise
        """
        stmt = select(UserArchive).where(UserArchive.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_active_suspension(self, user_id: UUID) -> Optional[UserSuspension]:
        """
        Get user's most recent suspension if any.

        Args:
            user_id: User UUID

        Returns:
            Most recent suspension or None
        """
        stmt = (
            select(UserSuspension)
            .where(UserSuspension.user_id == user_id)
            .order_by(UserSuspension.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[User]:
        """
        List users in an organization with optional filtering.

        Args:
            organization_id: Organization UUID
            include_inactive: Include inactive users (default: False)
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of users
        """
        stmt = (
            select(User)
            .join(OrganizationMember)
            .options(
                joinedload(User.profile),
                joinedload(User.active_status),
            )
            .where(OrganizationMember.organization_id == organization_id)
        )

        # Filter only active users if requested
        if not include_inactive:
            stmt = stmt.join(UserActiveStatus)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()

    async def count_by_organization(
        self, organization_id: UUID, include_inactive: bool = False
    ) -> int:
        """
        Count users in an organization.

        Args:
            organization_id: Organization UUID
            include_inactive: Include inactive users (default: False)

        Returns:
            User count
        """
        stmt = (
            select(User)
            .join(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
        )

        if not include_inactive:
            stmt = stmt.join(UserActiveStatus)

        result = await self.db.execute(stmt)
        return len(result.scalars().all())


__all__ = ["UserRepository"]
