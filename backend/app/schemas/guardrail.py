"""
Guardrail Pydantic schemas for request/response validation.

This module defines all Pydantic models for Guardrail-related API operations,
including JSONB definition validation.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ===== Guardrail Definition Models =====


class GuardrailCondition(BaseModel):
    """Individual condition in a guardrail trigger"""

    field: str = Field(description="Field path to evaluate (e.g., 'input.query')")
    operator: Literal[
        "contains",
        "equals",
        "regex",  # String operators
        "gt",
        "lt",
        "gte",
        "lte",  # Numeric operators
        "size_gt",
        "size_lt",
        "size_gte",
        "size_lte",  # Size operators
        "llm_judge",  # LLM-based evaluation
    ] = Field(description="Comparison operator")
    value: Any = Field(description="Value to compare against")


class GuardrailTrigger(BaseModel):
    """Trigger conditions for a guardrail"""

    type: Literal["on_start", "on_end"] = Field(
        description="When to evaluate: before (on_start) or after (on_end) execution"
    )
    logic: Literal["and", "or"] = Field(
        default="and",
        description="How to combine conditions: all must match (and) or any can match (or)",
    )
    conditions: list[GuardrailCondition] = Field(
        description="List of conditions to evaluate"
    )


class GuardrailActionConfig(BaseModel):
    """Configuration for guardrail actions (flexible schema)"""

    model_config = ConfigDict(extra="allow")  # Allow additional fields

    message: str | None = Field(None, description="Message to display (for block/warn)")
    allow_proceed: bool | None = Field(
        None, description="Allow proceeding after warning"
    )
    drop_field: str | None = Field(None, description="Field to drop (for modify)")
    drop_item: dict[str, Any] | None = Field(
        None, description="Item to drop (for modify)"
    )


class GuardrailAction(BaseModel):
    """Action to take when guardrail is triggered"""

    type: Literal["block", "warn", "modify"] = Field(
        description="Action type: block execution, warn user, or modify data"
    )
    priority: int = Field(default=1, description="Execution priority (1 = highest)")
    config: GuardrailActionConfig = Field(description="Action-specific configuration")


class GuardrailMetadata(BaseModel):
    """Metadata for a guardrail"""

    description: str = Field(description="Human-readable description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Severity level of this guardrail"
    )


class GuardrailDefinition(BaseModel):
    """Complete guardrail definition with trigger and actions"""

    version: str = Field(default="1.0", description="Definition version")
    schema_version: str = Field(default="1", description="Schema version")
    trigger: GuardrailTrigger = Field(description="Trigger conditions")
    actions: list[GuardrailAction] = Field(description="Actions to execute")
    metadata: GuardrailMetadata | None = Field(
        default=None, description="Metadata (optional)"
    )


# ===== Guardrail CRUD Schemas =====


class GuardrailBase(BaseModel):
    """
    Base Guardrail schema with common fields.

    Attributes:
        name: Guardrail display name (required)
        definition: Strongly-typed guardrail definition with trigger conditions and actions

    Definition structure (now validated with Pydantic):
        - version: Definition version (default: "1.0")
        - schema_version: Schema version (default: "1")
        - trigger: GuardrailTrigger
          - type: "on_start" or "on_end"
          - logic: "and" or "or"
          - conditions: List of GuardrailCondition
        - actions: List of GuardrailAction
          - type: "block", "warn", or "modify"
          - priority: Execution order (1 = highest)
          - config: GuardrailActionConfig
        - metadata: GuardrailMetadata
          - description: Human-readable description
          - tags: List of tags
          - severity: "low", "medium", "high", or "critical"

    Trigger logic:
        - "and": All conditions must match for trigger
        - "or": At least one condition must match for trigger

    Supported operators:
        - String: contains, equals, regex
        - Numeric: gt, lt, gte, lte
        - Size: size_gt, size_lt, size_gte, size_lte (for strings/arrays)
        - LLM: llm_judge (natural language criteria)

    Action types:
        - block: Block process execution
        - warn: Issue warning (with allow_proceed option)
        - modify: Modify data (drop_field or drop_item)
    """

    name: str = Field(..., min_length=1, max_length=255, description="Guardrail name")
    definition: GuardrailDefinition = Field(
        ...,
        description="Guardrail definition with trigger conditions and actions",
    )


class GuardrailCreate(GuardrailBase):
    """
    Schema for creating a new guardrail.

    Example:
        >>> guardrail_data = GuardrailCreate(
        ...     name="Block Offensive Content",
        ...     definition={
        ...         "version": "1.0",
        ...         "schema_version": "1",
        ...         "trigger": {
        ...             "type": "on_start",
        ...             "logic": "or",
        ...             "conditions": [
        ...                 {"field": "input.content", "operator": "contains", "value": "spam"},
        ...                 {"field": "input.content", "operator": "llm_judge",
        ...                  "value": "この内容は攻撃的または不適切な表現を含んでいますか？"}
        ...             ]
        ...         },
        ...         "actions": [
        ...             {"type": "block", "priority": 1,
        ...              "config": {"message": "Content blocked due to policy violation"}}
        ...         ],
        ...         "metadata": {
        ...             "description": "Block offensive or spam content",
        ...             "tags": ["content-moderation"],
        ...             "severity": "high"
        ...         }
        ...     }
        ... )

    Note:
        - project_id will come from URL path or body
        - organization_id will be derived from project
        - created_by will be set from authenticated user
        - trigger.logic must be "and" or "or"
        - trigger.type must be "on_start" or "on_end"
        - All conditions will be combined using the specified logic
    """

    project_id: UUID = Field(..., description="Project this guardrail belongs to")


class GuardrailUpdate(BaseModel):
    """
    Schema for updating an existing guardrail.

    All fields are optional for partial updates.

    Example:
        >>> update_data = GuardrailUpdate(
        ...     name="Updated Guardrail Name",
        ...     definition=GuardrailDefinition(...)
        ... )
    """

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Guardrail name"
    )
    definition: GuardrailDefinition | None = Field(
        None, description="Guardrail definition"
    )


class GuardrailResponse(GuardrailBase):
    """
    Schema for guardrail response data.

    Attributes:
        id: Guardrail UUID
        project_id: Project this guardrail belongs to
        organization_id: Organization (denormalized from project)
        name: Guardrail display name
        definition: JSONB definition
        created_by: User who created the guardrail
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_active: Whether guardrail is active
        is_archived: Whether guardrail is archived
        assigned_agent_count: Number of agents with this guardrail assigned

    Example:
        >>> {
        ...     "id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "project_id": "123e4567-e89b-12d3-a456-426614174001",
        ...     "organization_id": "123e4567-e89b-12d3-a456-426614174002",
        ...     "name": "Block Offensive Content",
        ...     "definition": {...},
        ...     "created_by": "123e4567-e89b-12d3-a456-426614174003",
        ...     "created_at": "2025-09-30T12:00:00Z",
        ...     "updated_at": "2025-09-30T12:00:00Z",
        ...     "is_active": True,
        ...     "is_archived": False,
        ...     "assigned_agent_count": 3
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
    assigned_agent_count: int = Field(
        default=0, description="Number of assigned agents (computed)"
    )

    model_config = ConfigDict(from_attributes=True)


class GuardrailAgentAssignmentCreate(BaseModel):
    """
    Schema for assigning a guardrail to an agent.

    Example:
        >>> assignment_data = GuardrailAgentAssignmentCreate(
        ...     agent_id="123e4567-e89b-12d3-a456-426614174000"
        ... )

    Note:
        - guardrail_id will come from URL path parameter
        - project_id will be derived from guardrail
        - assigned_by will be set from authenticated user
        - Both guardrail and agent must be in same project
    """

    agent_id: UUID = Field(..., description="Agent ID to assign this guardrail to")


class GuardrailAgentAssignmentResponse(BaseModel):
    """
    Schema for guardrail-agent assignment response.

    Attributes:
        id: Assignment record UUID
        project_id: Project (denormalized for RLS)
        guardrail_id: Guardrail UUID
        agent_id: Agent UUID
        assigned_by: User who made the assignment
        created_at: When assignment was created (semantically "assigned_at")
        updated_at: Last update timestamp
    """

    id: UUID
    project_id: UUID
    guardrail_id: UUID
    agent_id: UUID
    assigned_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuardrailArchiveRequest(BaseModel):
    """
    Schema for archiving a guardrail.

    Example:
        >>> archive_request = GuardrailArchiveRequest(
        ...     reason="Guardrail no longer needed"
        ... )
    """

    reason: str | None = Field(None, description="Reason for archiving")


class GuardrailListResponse(BaseModel):
    """
    Schema for paginated guardrail list response.

    Attributes:
        items: List of guardrails
        total: Total number of guardrails
        page: Current page number
        page_size: Number of items per page
    """

    items: list[GuardrailResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    # Guardrail Definition Models
    "GuardrailCondition",
    "GuardrailTrigger",
    "GuardrailActionConfig",
    "GuardrailAction",
    "GuardrailMetadata",
    "GuardrailDefinition",
    # Guardrail CRUD Schemas
    "GuardrailBase",
    "GuardrailCreate",
    "GuardrailUpdate",
    "GuardrailResponse",
    "GuardrailAgentAssignmentCreate",
    "GuardrailAgentAssignmentResponse",
    "GuardrailArchiveRequest",
    "GuardrailListResponse",
]
