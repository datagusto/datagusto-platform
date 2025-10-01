"""
Trace and Observation Pydantic schemas for request/response validation.

This module defines all Pydantic models for Trace and Observation-related
API operations, supporting hierarchical observation trees.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TraceBase(BaseModel):
    """
    Base Trace schema with common fields.

    Attributes:
        status: Execution status (pending, running, completed, failed, error)
        trace_metadata: JSONB metadata (inputs, outputs, tags, costs, errors)
    """

    status: str = Field(
        default="pending",
        description="Execution status",
        pattern="^(pending|running|completed|failed|error)$",
    )
    trace_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="JSONB metadata (inputs, outputs, tags, costs)",
        alias="metadata",
    )


class TraceCreate(TraceBase):
    """
    Schema for creating a new trace.

    Example:
        >>> trace_data = TraceCreate(
        ...     agent_id="123e4567-e89b-12d3-a456-426614174000",
        ...     status="running",
        ...     metadata={
        ...         "input": {"prompt": "Hello, world!"},
        ...         "tags": ["production"]
        ...     }
        ... )

    Note:
        - agent_id required
        - project_id and organization_id will be derived from agent
        - started_at will be set automatically to now()
        - ended_at is NULL until trace completes
    """

    agent_id: UUID = Field(..., description="Agent this trace belongs to")
    started_at: Optional[datetime] = Field(
        None, description="When trace started (defaults to now())"
    )


class TraceUpdate(BaseModel):
    """
    Schema for updating an existing trace.

    All fields are optional for partial updates.

    Example:
        >>> update_data = TraceUpdate(
        ...     status="completed",
        ...     ended_at=datetime.utcnow(),
        ...     metadata={"output": {...}, "cost": {...}}
        ... )
    """

    status: Optional[str] = Field(
        None,
        description="Execution status",
        pattern="^(pending|running|completed|failed|error)$",
    )
    ended_at: Optional[datetime] = Field(
        None, description="When trace completed (NULL = still running)"
    )
    trace_metadata: Optional[dict[str, Any]] = Field(
        None, description="JSONB metadata", alias="metadata"
    )


class TraceResponse(TraceBase):
    """
    Schema for trace response data.

    Attributes:
        id: Trace UUID
        agent_id: Agent this trace belongs to
        project_id: Project (denormalized from agent)
        organization_id: Organization (denormalized from agent)
        status: Execution status
        started_at: When trace began
        ended_at: When trace completed (NULL = still running)
        trace_metadata: JSONB metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        observation_count: Number of observations in this trace
        duration_ms: Duration in milliseconds (computed from started_at/ended_at)

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "agent_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "project_id": "123e4567-e89b-12d3-a456-426614174002",
        ...     "organization_id": "123e4567-e89b-12d3-a456-426614174003",
        ...     "status": "completed",
        ...     "started_at": "2025-09-30T12:00:00Z",
        ...     "ended_at": "2025-09-30T12:00:05Z",
        ...     "metadata": {...},
        ...     "created_at": "2025-09-30T12:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:05Z",
        ...     "observation_count": 15,
        ...     "duration_ms": 5000
        ... }
    """

    id: UUID
    agent_id: UUID
    project_id: UUID
    organization_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    observation_count: int = Field(
        default=0, description="Number of observations (computed)"
    )
    duration_ms: Optional[int] = Field(
        None, description="Duration in milliseconds (computed)"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ObservationBase(BaseModel):
    """
    Base Observation schema with common fields.

    Attributes:
        type: Observation type (llm, tool, retriever, agent, embedding, custom)
        name: Display name for the observation
        status: Execution status
        observation_metadata: JSONB metadata (tokens, cost, latency, etc.)
    """

    type: str = Field(
        ...,
        description="Observation type",
        pattern="^(llm|tool|retriever|agent|embedding|reranker|custom)$",
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Display name"
    )
    status: str = Field(
        default="pending",
        description="Execution status",
        pattern="^(pending|running|completed|failed|error)$",
    )
    observation_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="JSONB metadata (tokens, cost, latency)",
        alias="metadata",
    )


class ObservationCreate(ObservationBase):
    """
    Schema for creating a new observation.

    Example:
        >>> obs_data = ObservationCreate(
        ...     trace_id="123e4567-e89b-12d3-a456-426614174000",
        ...     parent_observation_id=None,  # Root observation
        ...     type="agent",
        ...     name="Agent Execution",
        ...     status="running",
        ...     metadata={"input": {...}}
        ... )

    Note:
        - trace_id required
        - parent_observation_id is NULL for root observations
        - started_at defaults to now()
        - ended_at is NULL until observation completes
    """

    trace_id: UUID = Field(..., description="Trace this observation belongs to")
    parent_observation_id: Optional[UUID] = Field(
        None, description="Parent observation for hierarchy (NULL = root)"
    )
    started_at: Optional[datetime] = Field(
        None, description="When observation started (defaults to now())"
    )


class ObservationUpdate(BaseModel):
    """
    Schema for updating an existing observation.

    All fields are optional for partial updates.

    Example:
        >>> update_data = ObservationUpdate(
        ...     status="completed",
        ...     ended_at=datetime.utcnow(),
        ...     metadata={"output": {...}, "tokens": {...}}
        ... )
    """

    status: Optional[str] = Field(
        None,
        description="Execution status",
        pattern="^(pending|running|completed|failed|error)$",
    )
    ended_at: Optional[datetime] = Field(
        None, description="When observation completed (NULL = still running)"
    )
    observation_metadata: Optional[dict[str, Any]] = Field(
        None, description="JSONB metadata", alias="metadata"
    )


class ObservationResponse(ObservationBase):
    """
    Schema for observation response data.

    Attributes:
        id: Observation UUID
        trace_id: Trace this observation belongs to
        parent_observation_id: Parent observation (NULL = root)
        type: Observation type
        name: Display name
        status: Execution status
        started_at: When observation began
        ended_at: When observation completed (NULL = still running)
        observation_metadata: JSONB metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        child_count: Number of child observations
        duration_ms: Duration in milliseconds (computed)

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "trace_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "parent_observation_id": None,
        ...     "type": "llm",
        ...     "name": "GPT-4 Call",
        ...     "status": "completed",
        ...     "started_at": "2025-09-30T12:00:00Z",
        ...     "ended_at": "2025-09-30T12:00:02Z",
        ...     "metadata": {...},
        ...     "created_at": "2025-09-30T12:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:02Z",
        ...     "child_count": 0,
        ...     "duration_ms": 2000
        ... }
    """

    id: UUID
    trace_id: UUID
    parent_observation_id: Optional[UUID] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    child_count: int = Field(default=0, description="Number of child observations")
    duration_ms: Optional[int] = Field(
        None, description="Duration in milliseconds (computed)"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ObservationTreeResponse(ObservationResponse):
    """
    Schema for observation with nested children (tree structure).

    Attributes:
        children: List of child observations (recursive)

    Example:
        >>> {
        ...     "id": "...",
        ...     "name": "Agent Execution",
        ...     "children": [
        ...         {
        ...             "id": "...",
        ...             "name": "LLM Call",
        ...             "children": []
        ...         },
        ...         {
        ...             "id": "...",
        ...             "name": "Tool Execution",
        ...             "children": [...]
        ...         }
        ...     ]
        ... }
    """

    children: list["ObservationTreeResponse"] = Field(
        default_factory=list, description="Child observations (recursive)"
    )


class TraceListResponse(BaseModel):
    """
    Schema for paginated trace list response.

    Attributes:
        items: List of traces
        total: Total number of traces
        page: Current page number
        page_size: Number of items per page
    """

    items: list[TraceResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ObservationListResponse(BaseModel):
    """
    Schema for paginated observation list response.

    Attributes:
        items: List of observations
        total: Total number of observations
        page: Current page number
        page_size: Number of items per page
    """

    items: list[ObservationResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "TraceBase",
    "TraceCreate",
    "TraceUpdate",
    "TraceResponse",
    "ObservationBase",
    "ObservationCreate",
    "ObservationUpdate",
    "ObservationResponse",
    "ObservationTreeResponse",
    "TraceListResponse",
    "ObservationListResponse",
]