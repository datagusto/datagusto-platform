"""
Guardrail Pydantic schemas for request/response validation.

This module defines all Pydantic models for Guardrail-related API operations,
including JSONB definition validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GuardrailBase(BaseModel):
    """
    Base Guardrail schema with common fields.

    Attributes:
        name: Guardrail display name (required)
        definition: JSONB definition containing trigger conditions and actions

    Definition structure:
        {
            "version": "1.0",
            "schema_version": "1",
            "trigger": {
                "type": "on_start" | "on_end",
                "logic": "and" | "or",
                "conditions": [
                    {
                        "field": "input.query",
                        "operator": "contains" | "equals" | "regex" | "gt" | "lt" | "gte" | "lte" |
                                   "size_gt" | "size_lt" | "size_gte" | "size_lte" | "llm_judge",
                        "value": <any>
                    }
                ]
            },
            "actions": [
                {
                    "type": "block" | "warn" | "modify",
                    "priority": <int>,
                    "config": {...}
                }
            ],
            "metadata": {
                "description": "...",
                "tags": [...],
                "severity": "low" | "medium" | "high" | "critical"
            }
        }

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
    definition: dict[str, Any] = Field(
        ...,
        description="JSONB definition (trigger conditions + actions)",
        examples=[
            {
                "version": "1.0",
                "schema_version": "1",
                "trigger": {
                    "type": "on_start",
                    "logic": "and",
                    "conditions": [
                        {
                            "field": "input.query",
                            "operator": "contains",
                            "value": "危険",
                        }
                    ],
                },
                "actions": [
                    {
                        "type": "block",
                        "priority": 1,
                        "config": {"message": "危険なキーワードが含まれています"},
                    }
                ],
                "metadata": {
                    "description": "危険ワードチェック",
                    "tags": ["safety"],
                    "severity": "high",
                },
            }
        ],
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
        ...     definition={"version": "1.0", ...}
        ... )
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Guardrail name"
    )
    definition: Optional[dict[str, Any]] = Field(
        None, description="JSONB definition"
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

    reason: Optional[str] = Field(None, description="Reason for archiving")


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
    "GuardrailBase",
    "GuardrailCreate",
    "GuardrailUpdate",
    "GuardrailResponse",
    "GuardrailAgentAssignmentCreate",
    "GuardrailAgentAssignmentResponse",
    "GuardrailArchiveRequest",
    "GuardrailListResponse",
]