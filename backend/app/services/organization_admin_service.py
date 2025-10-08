"""
Organization admin service for managing admin privilege operations.

This service handles organization admin privilege operations including
granting/revoking admin rights and listing admins.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_admin_repository import OrganizationAdminRepository
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository


class OrganizationAdminService:
    """Service for handling organization admin privilege operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the organization admin service.

        Args:
            db: Async database session
        """
        self.db = db
        self.admin_repo = OrganizationAdminRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def is_admin(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is an admin of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is admin, False otherwise
        """
        return await self.admin_repo.is_admin(organization_id, user_id)

    async def grant_admin(
        self, organization_id: UUID, user_id: UUID, granted_by: UUID
    ) -> dict[str, Any]:
        """
        Grant admin privileges to a user.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to grant admin to
            granted_by: UUID of user granting the privilege

        Returns:
            Admin privilege information

        Raises:
            HTTPException: If organization or user not found, or already an admin
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

        # Check if user is a member of the organization
        if not await self.member_repo.is_member(organization_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be a member of the organization to be granted admin privileges",
            )

        # Check if already an admin
        if await self.admin_repo.is_admin(organization_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin of this organization",
            )

        try:
            admin = await self.admin_repo.grant_admin(
                organization_id, user_id, granted_by
            )
            await self.db.commit()

            return {
                "organization_id": str(admin.organization_id),
                "user_id": str(admin.user_id),
                "granted_by": str(admin.granted_by),
                "granted_at": admin.created_at.isoformat()
                if admin.created_at
                else None,
            }

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to grant admin privileges: {str(e)}",
            )

    async def revoke_admin(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Revoke admin privileges from a user.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to revoke admin from

        Returns:
            True if revoked successfully

        Raises:
            HTTPException: If admin privilege not found
        """
        success = await self.admin_repo.revoke_admin(organization_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin privilege not found",
            )

        await self.db.commit()
        return True

    async def list_admins(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List all admins of an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of admins to return
            offset: Number of admins to skip

        Returns:
            List of user dictionaries
        """
        users = await self.admin_repo.list_admins(organization_id, limit, offset)

        result = []
        for user in users:
            # Get user profile if available
            user_data = await self.user_repo.get_by_id_with_relations(user.id)
            if user_data:
                result.append(
                    {
                        "id": str(user_data.id),
                        "email": user_data.login_password.email
                        if user_data.login_password
                        else None,
                        "name": user_data.profile.name if user_data.profile else None,
                        "avatar_url": user_data.profile.avatar_url
                        if user_data.profile
                        else None,
                    }
                )

        return result
