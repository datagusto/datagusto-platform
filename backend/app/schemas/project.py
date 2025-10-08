"""
Project Pydantic schemas for request/response validation.

This module defines all Pydantic models for Project-related API operations,
following the same ultra-fine-grained separation principles as database models.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """
    Base Project schema with common fields.

    Attributes:
        name: Project display name (required)
    """

    name: str = Field(..., min_length=1, max_length=255, description="Project name")


class ProjectCreate(ProjectBase):
    """
    Schema for creating a new project.

    Example:
        >>> project_data = ProjectCreate(name="Q4 Marketing Campaign")

    Note:
        - organization_id will be derived from authenticated user's context
        - created_by will be set automatically from authenticated user
        - Creator automatically becomes owner and member
    """

    pass


class ProjectUpdate(BaseModel):
    """
    Schema for updating an existing project.

    All fields are optional for partial updates.

    Example:
        >>> update_data = ProjectUpdate(name="Updated Project Name")
    """

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Project name"
    )


class ProjectResponse(ProjectBase):
    """
    Schema for project response data.

    Attributes:
        id: Project UUID
        organization_id: Organization this project belongs to
        name: Project display name
        created_by: User who created the project
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Whether project is active (computed from active_status)
        is_archived: Whether project is archived (computed from archive)

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "organization_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "name": "Q4 Marketing Campaign",
        ...     "created_by": "123e4567-e89b-12d3-a456-426614174002",
        ...     "created_at": "2025-09-30T12:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:00Z",
        ...     "is_active": True,
        ...     "is_archived": False
        ... }
    """

    id: UUID
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(
        default=False, description="Computed from active_status relationship"
    )
    is_archived: bool = Field(
        default=False, description="Computed from archive relationship"
    )

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberBase(BaseModel):
    """Base schema for project members."""

    user_id: UUID = Field(..., description="User ID to add as member")


class ProjectMemberCreate(ProjectMemberBase):
    """
    Schema for adding a member to a project.

    Example:
        >>> member_data = ProjectMemberCreate(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000"
        ... )

    Note:
        - User must be a member of the project's organization
        - project_id will come from URL path parameter
    """

    pass


class ProjectMemberResponse(ProjectMemberBase):
    """
    Schema for project member response.

    Attributes:
        id: Membership record ID
        project_id: Project UUID
        user_id: Member user UUID
        created_at: When user joined (semantically "joined_at")
        updated_at: Last update timestamp
    """

    id: int
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectOwnerResponse(BaseModel):
    """
    Schema for project owner response.

    Attributes:
        project_id: Project UUID
        user_id: Owner user UUID
        created_at: When ownership was established
        updated_at: Last update timestamp
    """

    project_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectOwnerUpdate(BaseModel):
    """
    Schema for transferring project ownership.

    Example:
        >>> owner_update = ProjectOwnerUpdate(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000"
        ... )

    Note:
        - New owner must be organization member
        - Will be automatically added as project member if not already
    """

    user_id: UUID = Field(..., description="New owner user ID")


class ProjectArchiveRequest(BaseModel):
    """
    Schema for archiving a project.

    Example:
        >>> archive_request = ProjectArchiveRequest(
        ...     reason="Project completed"
        ... )
    """

    reason: str | None = Field(None, description="Reason for archiving")


class ProjectMemberListResponse(BaseModel):
    """
    Schema for paginated project member list response.

    Attributes:
        items: List of members
        total: Total number of members
        page: Current page number
        page_size: Number of items per page
    """

    items: list[ProjectMemberResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ProjectListResponse(BaseModel):
    """
    Schema for paginated project list response.

    Attributes:
        items: List of projects
        total: Total number of projects
        page: Current page number
        page_size: Number of items per page
    """

    items: list[ProjectResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectMemberBase",
    "ProjectMemberCreate",
    "ProjectMemberResponse",
    "ProjectMemberListResponse",
    "ProjectOwnerResponse",
    "ProjectOwnerUpdate",
    "ProjectArchiveRequest",
    "ProjectListResponse",
]
