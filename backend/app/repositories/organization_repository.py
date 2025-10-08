"""
Organization repository for database operations.

This repository handles operations for the Organization model and its related
tables (status, members, admins, owners).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.organization import (
    Organization,
    OrganizationActiveStatus,
    OrganizationArchive,
    OrganizationSuspension,
)
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for organization database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Organization)

    async def get_by_id_with_relations(
        self, organization_id: UUID
    ) -> Organization | None:
        """
        Get organization by ID with all related data.

        Args:
            organization_id: Organization UUID

        Returns:
            Organization with related data or None if not found
        """
        stmt = (
            select(Organization)
            .options(
                joinedload(Organization.active_status),
                joinedload(Organization.owner),
            )
            .where(Organization.id == organization_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    # Active Status Methods
    async def activate(self, organization_id: UUID) -> OrganizationActiveStatus:
        """
        Activate organization (create active status record).

        Args:
            organization_id: Organization UUID

        Returns:
            Created OrganizationActiveStatus

        Raises:
            IntegrityError: If organization is already active
        """
        status = OrganizationActiveStatus(organization_id=organization_id)
        self.db.add(status)
        await self.db.flush()
        return status

    async def deactivate(self, organization_id: UUID) -> bool:
        """
        Deactivate organization (delete active status record).

        Args:
            organization_id: Organization UUID

        Returns:
            True if deactivated, False if not found
        """
        stmt = select(OrganizationActiveStatus).where(
            OrganizationActiveStatus.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        if not status:
            return False

        await self.db.delete(status)
        return True

    async def is_active(self, organization_id: UUID) -> bool:
        """
        Check if organization is active.

        Args:
            organization_id: Organization UUID

        Returns:
            True if active, False otherwise
        """
        stmt = select(OrganizationActiveStatus).where(
            OrganizationActiveStatus.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Suspension Methods
    async def suspend(
        self,
        organization_id: UUID,
        reason: str,
        suspended_by: UUID,
        suspended_until: datetime | None = None,
    ) -> OrganizationSuspension:
        """
        Suspend organization.

        Args:
            organization_id: Organization UUID to suspend
            reason: Reason for suspension
            suspended_by: UUID of user performing suspension
            suspended_until: Optional end date for temporary suspension

        Returns:
            Created OrganizationSuspension
        """
        suspension = OrganizationSuspension(
            organization_id=organization_id,
            reason=reason,
            suspended_by=suspended_by,
            suspended_until=suspended_until,
        )
        self.db.add(suspension)
        await self.db.flush()
        return suspension

    async def lift_suspension(
        self, suspension_id: int, lifted_by: UUID
    ) -> OrganizationSuspension | None:
        """
        Lift (remove) a suspension by deleting the suspension record.

        Args:
            suspension_id: Suspension ID
            lifted_by: UUID of user lifting the suspension

        Returns:
            Deleted OrganizationSuspension or None if not found
        """
        stmt = select(OrganizationSuspension).where(
            OrganizationSuspension.id == suspension_id
        )
        result = await self.db.execute(stmt)
        suspension = result.scalar_one_or_none()

        if not suspension:
            return None

        # Delete suspension record to lift suspension
        await self.db.delete(suspension)
        await self.db.flush()
        return suspension

    async def get_active_suspension(
        self, organization_id: UUID
    ) -> OrganizationSuspension | None:
        """
        Get organization's most recent suspension (if any).

        Args:
            organization_id: Organization UUID

        Returns:
            Most recent suspension or None
        """
        stmt = (
            select(OrganizationSuspension)
            .where(OrganizationSuspension.organization_id == organization_id)
            .order_by(OrganizationSuspension.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_suspended(self, organization_id: UUID) -> bool:
        """
        Check if organization is currently suspended.

        Args:
            organization_id: Organization UUID

        Returns:
            True if suspended, False otherwise
        """
        suspension = await self.get_active_suspension(organization_id)
        return suspension is not None

    # Archive Methods
    async def archive(
        self, organization_id: UUID, reason: str, archived_by: UUID
    ) -> OrganizationArchive:
        """
        Archive organization (soft delete).

        Args:
            organization_id: Organization UUID to archive
            reason: Reason for archiving
            archived_by: UUID of user performing archiving

        Returns:
            Created OrganizationArchive

        Raises:
            IntegrityError: If organization is already archived
        """
        archive = OrganizationArchive(
            organization_id=organization_id,
            reason=reason,
            archived_by=archived_by,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def unarchive(self, organization_id: UUID) -> bool:
        """
        Unarchive organization (restore from soft delete).

        Args:
            organization_id: Organization UUID

        Returns:
            True if unarchived, False if not found
        """
        stmt = select(OrganizationArchive).where(
            OrganizationArchive.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        archive = result.scalar_one_or_none()

        if not archive:
            return False

        await self.db.delete(archive)
        return True

    async def is_archived(self, organization_id: UUID) -> bool:
        """
        Check if organization is archived (soft deleted).

        Args:
            organization_id: Organization UUID

        Returns:
            True if archived, False otherwise
        """
        stmt = select(OrganizationArchive).where(
            OrganizationArchive.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_name(self, name: str) -> Organization | None:
        """
        Get organization by name.

        Args:
            name: Organization name

        Returns:
            Organization or None if not found

        Note:
            Organization names are not unique, returns first match
        """
        stmt = select(Organization).where(Organization.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(
        self, limit: int = 100, offset: int = 0
    ) -> list[Organization]:
        """
        List all active organizations.

        Args:
            limit: Maximum number of organizations to return
            offset: Number of organizations to skip

        Returns:
            List of active organizations
        """
        stmt = (
            select(Organization)
            .join(OrganizationActiveStatus)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


__all__ = ["OrganizationRepository"]
