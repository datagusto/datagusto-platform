"""
Organization schemas for API request/response validation.

These schemas align with the ultra-fine-grained data model for organizations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""

    name: str = Field(..., min_length=1, description="Organization name")


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, description="Organization name")


class OrganizationSuspend(BaseModel):
    """Schema for suspending an organization."""

    reason: str = Field(..., description="Reason for suspension")
    suspended_until: Optional[datetime] = Field(
        None, description="Suspension end date (permanent if not provided)"
    )


class OrganizationArchive(BaseModel):
    """Schema for archiving an organization."""

    reason: str = Field(..., description="Reason for archiving")


class Organization(BaseModel):
    """Schema for organization response."""

    id: str = Field(..., description="Organization UUID")
    name: str = Field(..., description="Organization name")
    is_active: bool = Field(..., description="Whether organization is active")
    is_suspended: bool = Field(..., description="Whether organization is suspended")
    is_archived: bool = Field(..., description="Whether organization is archived")
    created_at: Optional[str] = Field(
        None, description="Organization creation timestamp"
    )
    updated_at: Optional[str] = Field(None, description="Organization update timestamp")

    class Config:
        from_attributes = True


class OrganizationList(BaseModel):
    """Schema for list of organizations."""

    organizations: list[Organization] = Field(..., description="List of organizations")
    total: int = Field(..., description="Total number of organizations")
    limit: int = Field(..., description="Number of organizations per page")
    offset: int = Field(..., description="Number of organizations skipped")


class OrganizationMemberAdd(BaseModel):
    """Schema for adding a member to organization."""

    user_id: str = Field(..., description="User UUID to add as member")


class OrganizationMember(BaseModel):
    """Schema for organization member response."""

    id: str = Field(..., description="User UUID")
    email: Optional[str] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")

    class Config:
        from_attributes = True


class OrganizationMemberList(BaseModel):
    """Schema for list of organization members."""

    members: list[OrganizationMember] = Field(..., description="List of members")
    total: int = Field(..., description="Total number of members")
    limit: int = Field(..., description="Number of members per page")
    offset: int = Field(..., description="Number of members skipped")


class OrganizationAdminGrant(BaseModel):
    """Schema for granting admin privileges."""

    user_id: str = Field(..., description="User UUID to grant admin privileges to")


class OrganizationOwnerTransfer(BaseModel):
    """Schema for transferring organization ownership."""

    new_owner_user_id: str = Field(..., description="New owner's User UUID")


class PermissionSummary(BaseModel):
    """Schema for user permission summary in an organization."""

    organization_id: str = Field(..., description="Organization UUID")
    user_id: str = Field(..., description="User UUID")
    permission_level: str = Field(
        ..., description="Permission level (owner/admin/member/none)"
    )
    is_owner: bool = Field(..., description="Whether user is owner")
    is_admin: bool = Field(..., description="Whether user is admin")
    is_member: bool = Field(..., description="Whether user is member")
    can_manage_members: bool = Field(..., description="Whether user can manage members")
    can_manage_admins: bool = Field(..., description="Whether user can manage admins")
    can_transfer_ownership: bool = Field(
        ..., description="Whether user can transfer ownership"
    )
    can_access_organization: bool = Field(
        ..., description="Whether user can access organization"
    )

    class Config:
        from_attributes = True
