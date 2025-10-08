"""
Organization member repository for database operations.

This repository handles membership relationships between users and organizations.
"""

from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrganizationMember
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """Repository for organization member database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, OrganizationMember)

    async def is_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is a member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is member, False otherwise
        """
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_member(
        self, organization_id: UUID, user_id: UUID
    ) -> OrganizationMember:
        """
        Add user as member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            Created membership record

        Raises:
            IntegrityError: If user is already a member
        """
        membership = OrganizationMember(
            organization_id=organization_id, user_id=user_id
        )
        self.db.add(membership)
        await self.db.flush()
        return membership

    async def remove_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Remove user from organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if removed, False if not found
        """
        stmt = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        membership = result.scalar_one_or_none()

        if not membership:
            return False

        await self.db.delete(membership)
        return True

    async def list_members(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[User]:
        """
        List all members of an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of members to return
            offset: Number of members to skip

        Returns:
            List of User objects
        """
        stmt = (
            select(User)
            .join(OrganizationMember)
            .where(OrganizationMember.organization_id == organization_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_members(self, organization_id: UUID) -> int:
        """
        Count members in an organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Member count
        """
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def list_organizations_for_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> list:
        """
        List all organizations a user belongs to.

        Args:
            user_id: User UUID
            limit: Maximum number of organizations to return
            offset: Number of organizations to skip

        Returns:
            List of Organization objects
        """
        from app.models.organization import Organization

        stmt = (
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


__all__ = ["OrganizationMemberRepository"]
