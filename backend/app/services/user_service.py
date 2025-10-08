"""
User service for managing user operations.

This service handles user-related operations including profile management,
authentication updates, and status changes.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.user_auth_repository import UserAuthRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_status_repository import UserStatusRepository


class UserService:
    """Service for handling user operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the user service.

        Args:
            db: Async database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.auth_repo = UserAuthRepository(db)
        self.status_repo = UserStatusRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def get_user(self, user_id: UUID) -> dict[str, Any] | None:
        """
        Get user by ID with all related data.

        Args:
            user_id: User UUID

        Returns:
            Dictionary containing user data or None if not found

        Raises:
            HTTPException: If user not found

        Note:
            Does not include organization_id as users can belong to multiple organizations.
            Use get_user_organizations() to fetch organization memberships.
        """
        user = await self.user_repo.get_by_id_with_relations(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "id": str(user.id),
            "email": user.login_password.email if user.login_password else None,
            "name": user.profile.name if user.profile else None,
            "bio": user.profile.bio if user.profile else None,
            "avatar_url": user.profile.avatar_url if user.profile else None,
            "is_active": await self.status_repo.is_active(user.id),
            "is_archived": await self.status_repo.is_archived(user.id),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            Dictionary containing user data or None if not found
        """
        user = await self.user_repo.get_by_email_with_relations(email)
        if not user:
            return None

        return await self.get_user(user.id)

    async def get_user_organizations(self, user_id: UUID) -> list[dict[str, Any]]:
        """
        Get all organizations that user belongs to.

        Args:
            user_id: User UUID

        Returns:
            List of organization dictionaries with membership info

        Raises:
            HTTPException: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get all organizations for user (no limit)
        organizations = await self.member_repo.list_organizations_for_user(
            user_id=user_id, limit=None
        )

        result = []
        for org in organizations:
            # Check if user is owner
            from app.repositories.organization_owner_repository import (
                OrganizationOwnerRepository,
            )

            owner_repo = OrganizationOwnerRepository(self.db)
            is_owner = await owner_repo.is_owner(
                organization_id=org.id, user_id=user_id
            )

            result.append(
                {
                    "id": str(org.id),
                    "name": org.name,
                    "role": "owner" if is_owner else "member",
                    "joined_at": None,  # TODO: Add joined_at from membership record
                }
            )

        return result

    async def update_profile(
        self, user_id: UUID, profile_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update user profile information.

        Args:
            user_id: User UUID
            profile_data: Profile data to update (name, bio, avatar_url)

        Returns:
            Updated user data

        Raises:
            HTTPException: If user not found or update fails
        """
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update or create profile
        profile = await self.profile_repo.get_by_user_id(user_id)
        if profile:
            await self.profile_repo.update_profile(user_id, profile_data)
        else:
            await self.profile_repo.create_profile(user_id, profile_data)

        await self.db.commit()
        return await self.get_user(user_id)

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User UUID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            HTTPException: If old password is incorrect or update fails
        """
        # Get user authentication
        auth = await self.auth_repo.get_by_user_id(user_id)
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User authentication not found",
            )

        # Verify old password
        if not verify_password(old_password, auth.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )

        # Update password
        new_hashed_password = get_password_hash(new_password)
        await self.auth_repo.update_password(user_id, new_hashed_password)
        await self.db.commit()
        return True

    async def change_email(self, user_id: UUID, new_email: str) -> bool:
        """
        Change user email address.

        Args:
            user_id: User UUID
            new_email: New email address

        Returns:
            True if email changed successfully

        Raises:
            HTTPException: If email already exists or update fails
        """
        # Check if new email already exists
        if await self.auth_repo.email_exists(new_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )

        # Update email
        auth = await self.auth_repo.update_email(user_id, new_email)
        if not auth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User authentication not found",
            )

        await self.db.commit()
        return True

    async def archive_user(
        self, user_id: UUID, reason: str, archived_by: UUID
    ) -> dict[str, Any]:
        """
        Archive a user account (soft delete).

        Args:
            user_id: User UUID to archive
            reason: Reason for archiving
            archived_by: UUID of user performing archiving

        Returns:
            Updated user data

        Raises:
            HTTPException: If user not found or already archived
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Deactivate user first
        await self.status_repo.deactivate(user_id)

        # Archive user
        await self.status_repo.archive(user_id, reason, archived_by)
        await self.db.commit()
        return await self.get_user(user_id)

    async def unarchive_user(self, user_id: UUID) -> dict[str, Any]:
        """
        Unarchive a user account (restore from soft delete).

        Args:
            user_id: User UUID to unarchive

        Returns:
            Updated user data

        Raises:
            HTTPException: If user not found or not archived
        """
        if not await self.status_repo.is_archived(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not archived",
            )

        # Unarchive user
        await self.status_repo.unarchive(user_id)

        # Reactivate user
        await self.status_repo.activate(user_id)

        await self.db.commit()
        return await self.get_user(user_id)

    async def list_users_in_organization(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        List all users in an organization.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of user dictionaries
        """
        users = await self.user_repo.list_by_organization(
            organization_id, limit, offset
        )

        result = []
        for user in users:
            user_data = await self.get_user(user.id)
            result.append(user_data)

        return result

    async def search_users_by_name(
        self, name_pattern: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        Search users by name pattern.

        Args:
            name_pattern: Name search pattern
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of matching user dictionaries
        """
        profiles = await self.profile_repo.search_by_name(name_pattern, limit, offset)

        result = []
        for profile in profiles:
            user_data = await self.get_user(profile.user_id)
            result.append(user_data)

        return result
