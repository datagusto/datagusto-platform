"""
Organization owner service for managing ownership operations.

This service handles organization ownership operations including
transferring ownership and checking ownership status.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_owner_repository import OrganizationOwnerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)


class OrganizationOwnerService:
    """Service for handling organization ownership operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the organization owner service.

        Args:
            db: Async database session
        """
        self.db = db
        self.owner_repo = OrganizationOwnerRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def is_owner(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is the owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is owner, False otherwise
        """
        return await self.owner_repo.is_owner(organization_id, user_id)

    async def get_owner(self, organization_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the owner of an organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Owner user data or None if no owner set

        Raises:
            HTTPException: If organization not found
        """
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        owner = await self.owner_repo.get_owner(organization_id)
        if not owner:
            return None

        # Get user profile if available
        user_data = await self.user_repo.get_by_id_with_relations(owner.id)
        if user_data:
            return {
                "id": str(user_data.id),
                "email": user_data.login_password.email
                if user_data.login_password
                else None,
                "name": user_data.profile.name if user_data.profile else None,
                "avatar_url": user_data.profile.avatar_url
                if user_data.profile
                else None,
            }

        return None

    async def set_owner(self, organization_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Set the owner of an organization.

        This will replace the existing owner if one exists.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to set as owner

        Returns:
            Ownership information

        Raises:
            HTTPException: If organization or user not found
        """
        # Check if organization exists
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Ensure user is a member of the organization
        if not await self.member_repo.is_member(organization_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be a member of the organization to be set as owner",
            )

        try:
            owner = await self.owner_repo.set_owner(organization_id, user_id)
            await self.db.commit()

            return {
                "organization_id": str(owner.organization_id),
                "user_id": str(owner.user_id),
                "set_at": owner.created_at.isoformat() if owner.created_at else None,
            }

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to set owner: {str(e)}",
            )

    async def transfer_ownership(
        self,
        organization_id: UUID,
        new_owner_user_id: UUID,
        current_owner_user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Transfer ownership to another user.

        Args:
            organization_id: Organization UUID
            new_owner_user_id: New owner's User UUID
            current_owner_user_id: Current owner's User UUID (for verification)

        Returns:
            Updated ownership information

        Raises:
            HTTPException: If current user is not owner or transfer fails
        """
        # Verify current user is the owner
        if not await self.owner_repo.is_owner(organization_id, current_owner_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the current owner can transfer ownership",
            )

        # Check if new owner exists
        new_owner = await self.user_repo.get_by_id(new_owner_user_id)
        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New owner user not found",
            )

        # Ensure new owner is a member of the organization
        if not await self.member_repo.is_member(organization_id, new_owner_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New owner must be a member of the organization",
            )

        try:
            owner = await self.owner_repo.transfer_ownership(
                organization_id, new_owner_user_id
            )
            await self.db.commit()

            return {
                "organization_id": str(owner.organization_id),
                "user_id": str(owner.user_id),
                "transferred_at": owner.updated_at.isoformat()
                if owner.updated_at
                else None,
            }

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to transfer ownership: {str(e)}",
            )
