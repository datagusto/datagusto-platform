"""
Permission service for unified authorization checks.

This service provides a unified interface for checking permissions
across the organization hierarchy (owner > admin > member).
"""

from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_admin_repository import OrganizationAdminRepository
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.repositories.organization_owner_repository import OrganizationOwnerRepository


class PermissionLevel(str, Enum):
    """Permission levels in organization hierarchy."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    NONE = "none"


class PermissionService:
    """Service for handling unified permission checks."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the permission service.

        Args:
            db: Async database session
        """
        self.db = db
        self.owner_repo = OrganizationOwnerRepository(db)
        self.admin_repo = OrganizationAdminRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def get_user_permission_level(
        self, organization_id: UUID, user_id: UUID
    ) -> PermissionLevel:
        """
        Get user's permission level in an organization.

        The hierarchy is: owner > admin > member > none

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            User's permission level
        """
        # Check owner first (highest privilege)
        if await self.owner_repo.is_owner(organization_id, user_id):
            return PermissionLevel.OWNER

        # Check admin
        if await self.admin_repo.is_admin(organization_id, user_id):
            return PermissionLevel.ADMIN

        # Check member
        if await self.member_repo.is_member(organization_id, user_id):
            return PermissionLevel.MEMBER

        # No permission
        return PermissionLevel.NONE

    async def is_owner(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is owner, False otherwise
        """
        return await self.owner_repo.is_owner(organization_id, user_id)

    async def is_admin_or_owner(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is admin or owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is admin or owner, False otherwise
        """
        level = await self.get_user_permission_level(organization_id, user_id)
        return level in [PermissionLevel.OWNER, PermissionLevel.ADMIN]

    async def is_member_or_above(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is at least a member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is member, admin, or owner, False otherwise
        """
        level = await self.get_user_permission_level(organization_id, user_id)
        return level != PermissionLevel.NONE

    async def has_permission(
        self,
        organization_id: UUID,
        user_id: UUID,
        required_level: PermissionLevel,
    ) -> bool:
        """
        Check if user has at least the required permission level.

        Args:
            organization_id: Organization UUID
            user_id: User UUID
            required_level: Required permission level

        Returns:
            True if user has required permission or higher, False otherwise
        """
        user_level = await self.get_user_permission_level(organization_id, user_id)

        # Define hierarchy
        hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.MEMBER: 1,
            PermissionLevel.ADMIN: 2,
            PermissionLevel.OWNER: 3,
        }

        return hierarchy[user_level] >= hierarchy[required_level]

    async def get_user_permissions_summary(
        self, organization_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """
        Get comprehensive permission summary for a user in an organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            Dictionary containing all permission flags and level
        """
        is_owner = await self.owner_repo.is_owner(organization_id, user_id)
        is_admin = await self.admin_repo.is_admin(organization_id, user_id)
        is_member = await self.member_repo.is_member(organization_id, user_id)

        # Determine permission level
        if is_owner:
            level = PermissionLevel.OWNER
        elif is_admin:
            level = PermissionLevel.ADMIN
        elif is_member:
            level = PermissionLevel.MEMBER
        else:
            level = PermissionLevel.NONE

        return {
            "organization_id": str(organization_id),
            "user_id": str(user_id),
            "permission_level": level.value,
            "is_owner": is_owner,
            "is_admin": is_admin,
            "is_member": is_member,
            "can_manage_members": is_owner or is_admin,
            "can_manage_admins": is_owner,
            "can_transfer_ownership": is_owner,
            "can_access_organization": is_owner or is_admin or is_member,
        }

    async def require_owner(self, organization_id: UUID, user_id: UUID) -> None:
        """
        Require user to be owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Raises:
            PermissionError: If user is not owner
        """
        if not await self.is_owner(organization_id, user_id):
            raise PermissionError("Owner permission required for this operation")

    async def require_admin_or_owner(
        self, organization_id: UUID, user_id: UUID
    ) -> None:
        """
        Require user to be admin or owner of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Raises:
            PermissionError: If user is not admin or owner
        """
        if not await self.is_admin_or_owner(organization_id, user_id):
            raise PermissionError(
                "Admin or owner permission required for this operation"
            )

    async def require_member_or_above(
        self, organization_id: UUID, user_id: UUID
    ) -> None:
        """
        Require user to be at least a member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Raises:
            PermissionError: If user is not a member
        """
        if not await self.is_member_or_above(organization_id, user_id):
            raise PermissionError("Organization membership required for this operation")
