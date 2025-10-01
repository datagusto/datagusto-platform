"""
User management API endpoints.

This module provides endpoints for user profile management,
password changes, and user administration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
from uuid import UUID

from app.core.database import get_async_db
from app.core.auth import get_current_user
from app.schemas.user import (
    User,
    UserProfileUpdate,
    UserPasswordChange,
    UserEmailChange,
    UserSuspend,
    UserArchive,
)
from app.services.user_service import UserService
from app.services.permission_service import PermissionService

router = APIRouter()


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get user by ID.

    Args:
        user_id: User UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        User data

    Raises:
        HTTPException: If user not found or access denied
    """
    user_service = UserService(db)
    return await user_service.get_user(user_id)


@router.patch("/{user_id}/profile", response_model=User)
async def update_profile(
    user_id: UUID,
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update user profile.

    Users can only update their own profile.

    Args:
        user_id: User UUID
        profile_data: Profile data to update
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    current_user_id = UUID(current_user.get("id"))
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    user_service = UserService(db)
    return await user_service.update_profile(
        user_id, profile_data.model_dump(exclude_unset=True)
    )


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: UUID,
    password_data: UserPasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """
    Change user password.

    Users can only change their own password.

    Args:
        user_id: User UUID
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found, access denied, or old password incorrect
    """
    current_user_id = UUID(current_user.get("id"))
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password",
        )

    user_service = UserService(db)
    await user_service.change_password(
        user_id, password_data.old_password, password_data.new_password
    )
    return {"message": "Password changed successfully"}


@router.post("/{user_id}/change-email")
async def change_email(
    user_id: UUID,
    email_data: UserEmailChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """
    Change user email address.

    Users can only change their own email.

    Args:
        user_id: User UUID
        email_data: Email change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found, access denied, or email already in use
    """
    current_user_id = UUID(current_user.get("id"))
    if current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own email",
        )

    user_service = UserService(db)
    await user_service.change_email(user_id, email_data.new_email)
    return {"message": "Email changed successfully"}


@router.post("/{user_id}/suspend", response_model=User)
async def suspend_user(
    user_id: UUID,
    suspend_data: UserSuspend,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Suspend a user account.

    Only organization owners or admins can suspend users.

    Args:
        user_id: User UUID to suspend
        suspend_data: Suspension data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    current_user_id = UUID(current_user.get("id"))
    org_id = current_user.get("organization_id")

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_admin_or_owner(UUID(org_id), current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners or admins can suspend users",
        )

    user_service = UserService(db)
    return await user_service.suspend_user(
        user_id,
        suspend_data.reason,
        current_user_id,
        suspend_data.suspended_until,
    )


@router.post("/{user_id}/archive", response_model=User)
async def archive_user(
    user_id: UUID,
    archive_data: UserArchive,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Archive a user account (soft delete).

    Only organization owners can archive users.

    Args:
        user_id: User UUID to archive
        archive_data: Archive data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    current_user_id = UUID(current_user.get("id"))
    org_id = current_user.get("organization_id")

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(UUID(org_id), current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can archive users",
        )

    user_service = UserService(db)
    return await user_service.archive_user(
        user_id, archive_data.reason, current_user_id
    )


@router.post("/{user_id}/unarchive", response_model=User)
async def unarchive_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Unarchive a user account (restore from soft delete).

    Only organization owners can unarchive users.

    Args:
        user_id: User UUID to unarchive
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If user not found or access denied
    """
    current_user_id = UUID(current_user.get("id"))
    org_id = current_user.get("organization_id")

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(UUID(org_id), current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can unarchive users",
        )

    user_service = UserService(db)
    return await user_service.unarchive_user(user_id)


@router.get("/", response_model=List[User])
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    List users in the current organization.

    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of users

    Raises:
        HTTPException: If organization context not found
    """
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    user_service = UserService(db)
    return await user_service.list_users_in_organization(UUID(org_id), limit, offset)
