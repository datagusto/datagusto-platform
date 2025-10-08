"""
Organization admin repository for database operations.

This repository handles admin privilege relationships within organizations.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrganizationAdmin
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class OrganizationAdminRepository(BaseRepository[OrganizationAdmin]):
    """Repository for organization admin database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, OrganizationAdmin)

    async def is_admin(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is an admin of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is admin, False otherwise
        """
        stmt = select(OrganizationAdmin).where(
            and_(
                OrganizationAdmin.organization_id == organization_id,
                OrganizationAdmin.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def grant_admin(
        self, organization_id: UUID, user_id: UUID, granted_by: UUID
    ) -> OrganizationAdmin:
        """
        Grant admin privileges to user.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to grant admin to
            granted_by: User UUID who granted the privilege

        Returns:
            Created admin record

        Raises:
            IntegrityError: If user is already an admin
        """
        admin = OrganizationAdmin(
            organization_id=organization_id,
            user_id=user_id,
            granted_by=granted_by,
        )
        self.db.add(admin)
        await self.db.flush()
        return admin

    async def revoke_admin(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Revoke admin privileges from user.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if revoked, False if not found
        """
        stmt = select(OrganizationAdmin).where(
            and_(
                OrganizationAdmin.organization_id == organization_id,
                OrganizationAdmin.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            return False

        await self.db.delete(admin)
        return True

    async def list_admins(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[User]:
        """
        List all admins of an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of admins to return
            offset: Number of admins to skip

        Returns:
            List of User objects
        """
        stmt = (
            select(User)
            .join(OrganizationAdmin)
            .where(OrganizationAdmin.organization_id == organization_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


__all__ = ["OrganizationAdminRepository"]
