"""
User status repository for database operations.

This repository handles user status (active, suspended, archived).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserActiveStatus, UserArchive


class UserStatusRepository:
    """Repository for user status database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    # Active Status Methods
    async def activate(self, user_id: UUID) -> UserActiveStatus:
        """
        Activate user (create active status record).

        Args:
            user_id: User UUID

        Returns:
            Created UserActiveStatus

        Raises:
            IntegrityError: If user is already active
        """
        status = UserActiveStatus(user_id=user_id)
        self.db.add(status)
        await self.db.flush()
        return status

    async def deactivate(self, user_id: UUID) -> bool:
        """
        Deactivate user (delete active status record).

        Args:
            user_id: User UUID

        Returns:
            True if deactivated, False if not found
        """
        stmt = select(UserActiveStatus).where(UserActiveStatus.user_id == user_id)
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        if not status:
            return False

        await self.db.delete(status)
        return True

    async def is_active(self, user_id: UUID) -> bool:
        """
        Check if user is active.

        Args:
            user_id: User UUID

        Returns:
            True if active, False otherwise
        """
        stmt = select(UserActiveStatus).where(UserActiveStatus.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Archive Methods
    async def archive(
        self, user_id: UUID, reason: str, archived_by: UUID
    ) -> UserArchive:
        """
        Archive user (soft delete).

        Args:
            user_id: User UUID to archive
            reason: Reason for archiving
            archived_by: UUID of user performing archiving

        Returns:
            Created UserArchive

        Raises:
            IntegrityError: If user is already archived
        """
        archive = UserArchive(
            user_id=user_id,
            reason=reason,
            archived_by=archived_by,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def unarchive(self, user_id: UUID) -> bool:
        """
        Unarchive user (restore from soft delete).

        Args:
            user_id: User UUID

        Returns:
            True if unarchived, False if not found
        """
        stmt = select(UserArchive).where(UserArchive.user_id == user_id)
        result = await self.db.execute(stmt)
        archive = result.scalar_one_or_none()

        if not archive:
            return False

        await self.db.delete(archive)
        return True

    async def is_archived(self, user_id: UUID) -> bool:
        """
        Check if user is archived.

        Args:
            user_id: User UUID

        Returns:
            True if archived, False otherwise
        """
        stmt = select(UserArchive).where(UserArchive.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None


__all__ = ["UserStatusRepository"]
