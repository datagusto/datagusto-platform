"""
Organization owner repository for database operations.

This repository handles organization ownership (one owner per organization).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrganizationOwner
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class OrganizationOwnerRepository(BaseRepository[OrganizationOwner]):
    """Repository for organization owner database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, OrganizationOwner)

    async def is_owner(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is the owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is owner, False otherwise
        """
        stmt = select(OrganizationOwner).where(
            OrganizationOwner.organization_id == organization_id,
            OrganizationOwner.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_owner(self, organization_id: UUID) -> User | None:
        """
        Get the owner of an organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Owner User object or None if no owner set
        """
        stmt = (
            select(User)
            .join(OrganizationOwner)
            .where(OrganizationOwner.organization_id == organization_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def set_owner(
        self, organization_id: UUID, user_id: UUID
    ) -> OrganizationOwner:
        """
        Set the owner of an organization (creates or updates).

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            OrganizationOwner record

        Note:
            This will replace the existing owner if one exists
        """
        # Check if owner already exists
        stmt = select(OrganizationOwner).where(
            OrganizationOwner.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        existing_owner = result.scalar_one_or_none()

        if existing_owner:
            # Update existing owner
            existing_owner.user_id = user_id
            await self.db.flush()
            return existing_owner
        else:
            # Create new owner
            owner = OrganizationOwner(
                organization_id=organization_id,
                user_id=user_id,
            )
            self.db.add(owner)
            await self.db.flush()
            return owner

    async def transfer_ownership(
        self, organization_id: UUID, new_owner_user_id: UUID
    ) -> OrganizationOwner:
        """
        Transfer ownership to another user.

        Args:
            organization_id: Organization UUID
            new_owner_user_id: New owner's User UUID

        Returns:
            Updated OrganizationOwner record

        Raises:
            ValueError: If no existing owner found
        """
        stmt = select(OrganizationOwner).where(
            OrganizationOwner.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        owner = result.scalar_one_or_none()

        if not owner:
            raise ValueError(f"No owner found for organization {organization_id}")

        owner.user_id = new_owner_user_id
        await self.db.flush()
        await self.db.refresh(owner)
        return owner


__all__ = ["OrganizationOwnerRepository"]
