"""
Agent Pydantic schemas for request/response validation.

This module defines all Pydantic models for Agent-related API operations,
including API key management with security considerations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    """
    Base Agent schema with common fields.

    Attributes:
        name: Agent display name (required)
    """

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")


class AgentCreate(AgentBase):
    """
    Schema for creating a new agent.

    Example:
        >>> agent_data = AgentCreate(name="Production API Agent")

    Note:
        - project_id will come from URL path or body
        - organization_id will be derived from project
        - created_by will be set from authenticated user
        - Agent is automatically activated upon creation
    """

    project_id: UUID = Field(..., description="Project this agent belongs to")


class AgentUpdate(BaseModel):
    """
    Schema for updating an existing agent.

    All fields are optional for partial updates.

    Example:
        >>> update_data = AgentUpdate(name="Updated Agent Name")
    """

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Agent name"
    )


class AgentResponse(AgentBase):
    """
    Schema for agent response data.

    Attributes:
        id: Agent UUID
        project_id: Project this agent belongs to
        organization_id: Organization (denormalized from project)
        name: Agent display name
        created_by: User who created the agent
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Whether agent is active
        is_archived: Whether agent is archived
        api_key_count: Number of API keys for this agent

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "project_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "organization_id": "123e4567-e89b-12d3-a456-426614174002",
        ...     "name": "Production API Agent",
        ...     "created_by": "123e4567-e89b-12d3-a456-426614174003",
        ...     "created_at": "2025-09-30T12:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:00Z",
        ...     "is_active": True,
        ...     "is_archived": False,
        ...     "api_key_count": 2
        ... }
    """

    id: UUID
    project_id: UUID
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(default=False, description="Computed from active_status")
    is_archived: bool = Field(default=False, description="Computed from archive")
    api_key_count: int = Field(default=0, description="Number of API keys (computed)")

    model_config = ConfigDict(from_attributes=True)


class AgentAPIKeyCreate(BaseModel):
    """
    Schema for creating a new API key.

    Example:
        >>> key_data = AgentAPIKeyCreate(
        ...     name="Production Key",
        ...     expires_in_days=90
        ... )

    Note:
        - agent_id will come from URL path parameter
        - created_by will be set from authenticated user
        - Plain text key is returned only once at creation
    """

    name: str | None = Field(
        None, max_length=255, description="Optional friendly name for the key"
    )
    expires_in_days: int | None = Field(
        None, gt=0, le=365, description="Days until key expires (NULL = never expires)"
    )


class AgentAPIKeyResponse(BaseModel):
    """
    Schema for API key response (masked for security).

    IMPORTANT: This schema never includes the full key or hash.
    The plain text key is only returned once via AgentAPIKeyCreateResponse.

    Attributes:
        id: API key UUID
        agent_id: Agent this key belongs to
        key_prefix: First 12-16 characters for identification (e.g., "agt_live_1a2b3c4")
        name: Optional friendly name
        last_used_at: When key was last used (NULL = never used)
        expires_at: When key expires (NULL = never expires)
        created_by: User who created the key
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_expired: Whether key has expired (computed)

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "agent_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "key_prefix": "agt_live_1a2b3c4",
        ...     "name": "Production Key",
        ...     "last_used_at": "2025-09-30T12:00:00Z",
        ...     "expires_at": None,
        ...     "created_by": "123e4567-e89b-12d3-a456-426614174002",
        ...     "created_at": "2025-09-30T11:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:00Z",
        ...     "is_expired": False
        ... }
    """

    id: UUID
    agent_id: UUID
    key_prefix: str = Field(..., description="First 12-16 chars of key")
    name: str | None = None
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    is_expired: bool = Field(default=False, description="Computed: expires_at < now()")

    model_config = ConfigDict(from_attributes=True)


class AgentAPIKeyCreateResponse(AgentAPIKeyResponse):
    """
    Schema for API key creation response with plain text key.

    SECURITY WARNING: This includes the plain text API key.
    This response is only sent once at creation time.
    The key cannot be retrieved again after creation.

    Attributes:
        api_key: Full plain text API key (e.g., "agt_live_1a2b3c4d5e6f7g8h...")

    Example:
        >>> {
        ...     "api_key": "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p",
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "key_prefix": "agt_live_1a2b3c4",
        ...     ...
        ... }

    Note:
        - Store this key securely - it cannot be retrieved again
        - key_prefix can be used to identify the key in the UI
        - Full key is needed for API authentication
    """

    api_key: str = Field(..., description="Full API key (shown only once at creation)")


class AgentArchiveRequest(BaseModel):
    """
    Schema for archiving an agent.

    Example:
        >>> archive_request = AgentArchiveRequest(
        ...     reason="Agent no longer needed"
        ... )
    """

    reason: str | None = Field(None, description="Reason for archiving")


class AgentListResponse(BaseModel):
    """
    Schema for paginated agent list response.

    Attributes:
        items: List of agents
        total: Total number of agents
        page: Current page number
        page_size: Number of items per page
    """

    items: list[AgentResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentAPIKeyCreate",
    "AgentAPIKeyResponse",
    "AgentAPIKeyCreateResponse",
    "AgentArchiveRequest",
    "AgentListResponse",
]
