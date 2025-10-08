"""
Organization management API endpoints.

This module provides endpoints for organization management,
member management, admin management, and ownership transfer.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_async_db
from app.schemas.organization import (
    Organization,
    OrganizationAdminGrant,
    OrganizationArchive,
    OrganizationCreate,
    OrganizationMember,
    OrganizationMemberAdd,
    OrganizationOwnerTransfer,
    OrganizationSuspend,
    OrganizationUpdate,
    PermissionSummary,
)
from app.services.organization_admin_service import OrganizationAdminService
from app.services.organization_member_service import OrganizationMemberService
from app.services.organization_owner_service import OrganizationOwnerService
from app.services.organization_service import OrganizationService
from app.services.permission_service import PermissionService

router = APIRouter()


# Organization CRUD endpoints


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get organization by ID.

    Note: This endpoint allows any authenticated user to read organization details.
    Modification operations (PATCH, DELETE) require appropriate permissions.

    Args:
        organization_id: Organization UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Organization data
    """
    org_service = OrganizationService(db)
    return await org_service.get_organization(organization_id)


@router.post("/", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new organization.

    Args:
        org_data: Organization data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created organization data
    """
    current_user_id = UUID(current_user.get("id"))
    org_service = OrganizationService(db)
    return await org_service.create_organization(
        org_data.model_dump(exclude_unset=True), current_user_id
    )


@router.patch("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: UUID,
    org_data: OrganizationUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update organization information.

    Only organization owners or admins can update organization.

    Args:
        organization_id: Organization UUID
        org_data: Organization data to update
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated organization data
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_admin_or_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners or admins can update organization",
        )

    org_service = OrganizationService(db)
    return await org_service.update_organization(
        organization_id, org_data.model_dump(exclude_unset=True)
    )


# Organization status management


@router.post("/{organization_id}/suspend", response_model=Organization)
async def suspend_organization(
    organization_id: UUID,
    suspend_data: OrganizationSuspend,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Suspend an organization.

    Only organization owners can suspend organization.

    Args:
        organization_id: Organization UUID
        suspend_data: Suspension data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated organization data
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can suspend organization",
        )

    org_service = OrganizationService(db)
    return await org_service.suspend_organization(
        organization_id,
        suspend_data.reason,
        current_user_id,
        suspend_data.suspended_until,
    )


@router.post("/{organization_id}/archive", response_model=Organization)
async def archive_organization(
    organization_id: UUID,
    archive_data: OrganizationArchive,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Archive an organization (soft delete).

    Only organization owners can archive organization.

    Args:
        organization_id: Organization UUID
        archive_data: Archive data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated organization data
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can archive organization",
        )

    org_service = OrganizationService(db)
    return await org_service.archive_organization(
        organization_id, archive_data.reason, current_user_id
    )


# Member management endpoints


@router.get("/{organization_id}/members", response_model=list[OrganizationMember])
async def list_members(
    organization_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    List all members of an organization.

    Args:
        organization_id: Organization UUID
        limit: Maximum number of members to return
        offset: Number of members to skip
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of organization members
    """
    current_user_id = UUID(current_user.get("id"))

    # Check if user is at least a member
    permission_service = PermissionService(db)
    if not await permission_service.is_member_or_above(
        organization_id, current_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of the organization to view members",
        )

    member_service = OrganizationMemberService(db)
    return await member_service.list_members(organization_id, limit, offset)


@router.post("/{organization_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    organization_id: UUID,
    member_data: OrganizationMemberAdd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Add a user as member of organization.

    Only organization owners or admins can add members.

    Args:
        organization_id: Organization UUID
        member_data: Member data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Membership information
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_admin_or_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners or admins can add members",
        )

    member_service = OrganizationMemberService(db)
    return await member_service.add_member(
        organization_id, UUID(member_data.user_id), current_user_id
    )


@router.delete(
    "/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Remove a user from organization membership.

    Only organization owners or admins can remove members.

    Args:
        organization_id: Organization UUID
        user_id: User UUID to remove
        current_user: Current authenticated user
        db: Database session
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_admin_or_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners or admins can remove members",
        )

    member_service = OrganizationMemberService(db)
    await member_service.remove_member(organization_id, user_id)


# Admin management endpoints


@router.get("/{organization_id}/admins", response_model=list[OrganizationMember])
async def list_admins(
    organization_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    List all admins of an organization.

    Args:
        organization_id: Organization UUID
        limit: Maximum number of admins to return
        offset: Number of admins to skip
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of organization admins
    """
    current_user_id = UUID(current_user.get("id"))

    # Check if user is at least a member
    permission_service = PermissionService(db)
    if not await permission_service.is_member_or_above(
        organization_id, current_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of the organization to view admins",
        )

    admin_service = OrganizationAdminService(db)
    return await admin_service.list_admins(organization_id, limit, offset)


@router.post("/{organization_id}/admins", status_code=status.HTTP_201_CREATED)
async def grant_admin(
    organization_id: UUID,
    admin_data: OrganizationAdminGrant,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Grant admin privileges to a user.

    Only organization owners can grant admin privileges.

    Args:
        organization_id: Organization UUID
        admin_data: Admin data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Admin privilege information
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can grant admin privileges",
        )

    admin_service = OrganizationAdminService(db)
    return await admin_service.grant_admin(
        organization_id, UUID(admin_data.user_id), current_user_id
    )


@router.delete(
    "/{organization_id}/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_admin(
    organization_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Revoke admin privileges from a user.

    Only organization owners can revoke admin privileges.

    Args:
        organization_id: Organization UUID
        user_id: User UUID to revoke admin from
        current_user: Current authenticated user
        db: Database session
    """
    current_user_id = UUID(current_user.get("id"))

    # Check permission
    permission_service = PermissionService(db)
    if not await permission_service.is_owner(organization_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can revoke admin privileges",
        )

    admin_service = OrganizationAdminService(db)
    await admin_service.revoke_admin(organization_id, user_id)


# Ownership management endpoints


@router.get("/{organization_id}/owner", response_model=OrganizationMember)
async def get_owner(
    organization_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get the owner of an organization.

    Args:
        organization_id: Organization UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Owner user data
    """
    owner_service = OrganizationOwnerService(db)
    owner = await owner_service.get_owner(organization_id)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization owner not found",
        )
    return owner


@router.post("/{organization_id}/transfer-ownership")
async def transfer_ownership(
    organization_id: UUID,
    transfer_data: OrganizationOwnerTransfer,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """
    Transfer organization ownership to another user.

    Only the current owner can transfer ownership.

    Args:
        organization_id: Organization UUID
        transfer_data: Ownership transfer data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    current_user_id = UUID(current_user.get("id"))

    owner_service = OrganizationOwnerService(db)
    await owner_service.transfer_ownership(
        organization_id, UUID(transfer_data.new_owner_user_id), current_user_id
    )
    return {"message": "Ownership transferred successfully"}


# Permission check endpoint


@router.get(
    "/{organization_id}/permissions/{user_id}", response_model=PermissionSummary
)
async def get_user_permissions(
    organization_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get user's permission summary in an organization.

    Args:
        organization_id: Organization UUID
        user_id: User UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Permission summary
    """
    permission_service = PermissionService(db)
    return await permission_service.get_user_permissions_summary(
        organization_id, user_id
    )
