"""
User status repository for database operations.

This repository handles user status (active, suspended, archived).
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import UserActiveStatus, UserSuspension, UserArchive


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

    # Suspension Methods
    async def suspend(
        self,
        user_id: UUID,
        reason: str,
        suspended_by: UUID,
        suspended_until: Optional[datetime] = None,
    ) -> UserSuspension:
        """
        Suspend user.

        Args:
            user_id: User UUID to suspend
            reason: Reason for suspension
            suspended_by: UUID of user performing suspension
            suspended_until: Optional end date for temporary suspension

        Returns:
            Created UserSuspension
        """
        suspension = UserSuspension(
            user_id=user_id,
            reason=reason,
            suspended_by=suspended_by,
            suspended_until=suspended_until,
        )
        self.db.add(suspension)
        await self.db.flush()
        return suspension

    async def lift_suspension(
        self, suspension_id: int, lifted_by: UUID
    ) -> Optional[UserSuspension]:
        """
        Lift (remove) a suspension by deleting the suspension record.

        Args:
            suspension_id: Suspension ID
            lifted_by: UUID of user lifting the suspension

        Returns:
            Deleted UserSuspension or None if not found
        """
        stmt = select(UserSuspension).where(UserSuspension.id == suspension_id)
        result = await self.db.execute(stmt)
        suspension = result.scalar_one_or_none()

        if not suspension:
            return None

        # Delete suspension record to lift suspension
        await self.db.delete(suspension)
        await self.db.flush()
        return suspension

    async def get_active_suspension(self, user_id: UUID) -> Optional[UserSuspension]:
        """
        Get user's most recent suspension (if any).

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

    async def is_suspended(self, user_id: UUID) -> bool:
        """
        Check if user is currently suspended.

        Args:
            user_id: User UUID

        Returns:
            True if suspended, False otherwise
        """
        suspension = await self.get_active_suspension(user_id)
        return suspension is not None

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
