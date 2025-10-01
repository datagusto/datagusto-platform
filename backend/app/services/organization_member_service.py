"""
Organization member service for managing membership operations.

This service handles organization membership operations including
adding/removing members and listing organization members.
"""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository


class OrganizationMemberService:
    """Service for handling organization membership operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the organization member service.

        Args:
            db: Async database session
        """
        self.db = db
        self.member_repo = OrganizationMemberRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)

    async def is_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is a member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID

        Returns:
            True if user is member, False otherwise
        """
        return await self.member_repo.is_member(organization_id, user_id)

    async def add_member(
        self, organization_id: UUID, user_id: UUID, added_by: UUID
    ) -> Dict[str, Any]:
        """
        Add a user as member of organization.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to add
            added_by: UUID of user adding the member

        Returns:
            Membership information

        Raises:
            HTTPException: If organization or user not found, or already a member
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

        # Check if already a member
        if await self.member_repo.is_member(organization_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization",
            )

        try:
            membership = await self.member_repo.add_member(organization_id, user_id)
            await self.db.commit()

            return {
                "organization_id": str(membership.organization_id),
                "user_id": str(membership.user_id),
                "joined_at": membership.created_at.isoformat()
                if membership.created_at
                else None,
            }

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add member: {str(e)}",
            )

    async def remove_member(self, organization_id: UUID, user_id: UUID) -> bool:
        """
        Remove a user from organization membership.

        Args:
            organization_id: Organization UUID
            user_id: User UUID to remove

        Returns:
            True if removed successfully

        Raises:
            HTTPException: If membership not found
        """
        success = await self.member_repo.remove_member(organization_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found",
            )

        await self.db.commit()
        return True

    async def list_members(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all members of an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of members to return
            offset: Number of members to skip

        Returns:
            List of user dictionaries
        """
        users = await self.member_repo.list_members(organization_id, limit, offset)

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

    async def count_members(self, organization_id: UUID) -> int:
        """
        Count total members in an organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Total member count
        """
        return await self.member_repo.count_members(organization_id)

    async def list_organizations_for_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all organizations a user is member of.

        Args:
            user_id: User UUID
            limit: Maximum number of organizations to return
            offset: Number of organizations to skip

        Returns:
            List of organization dictionaries
        """
        orgs = await self.member_repo.list_organizations_for_user(
            user_id, limit, offset
        )

        result = []
        for org in orgs:
            org_data = await self.org_repo.get_by_id_with_relations(org.id)
            if org_data:
                result.append(
                    {
                        "id": str(org_data.id),
                        "name": org_data.name,
                        "slug": org_data.slug,
                        "description": org_data.description,
                        "logo_url": org_data.logo_url,
                    }
                )

        return result
