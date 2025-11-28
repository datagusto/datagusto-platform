"""
Tool Definition schemas for request/response validation.

This module contains Pydantic schemas for tool definition registration endpoints.
No validation is performed on tool data to allow maximum flexibility for clients.
"""

from typing import Any

from pydantic import BaseModel, Field


class ToolRegistrationRequest(BaseModel):
    """
    Request schema for tool definition registration.

    The tools list accepts any JSON structure without validation,
    allowing clients to send tool definitions in any format they prefer.

    Attributes:
        tools: List of tool definitions (no validation performed)

    Example:
        >>> request = ToolRegistrationRequest(
        ...     tools=[
        ...         {
        ...             "name": "get_weather",
        ...             "description": "Get current weather",
        ...             "input_schema": {"type": "object", "properties": {...}},
        ...             "output_schema": {"type": "object", "properties": {...}}
        ...         }
        ...     ]
        ... )
    """

    tools: list[dict[str, Any]] = Field(
        ...,
        description="List of tool definitions (flexible structure, no validation)",
    )


class ToolRegistrationResponse(BaseModel):
    """
    Response schema for tool definition registration.

    Returns information about the created revision including IDs,
    tool count, and timestamps for audit purposes.

    Attributes:
        tool_definition_id: UUID of the ToolDefinition record
        revision_id: UUID of the newly created ToolDefinitionRevision
        agent_id: UUID of the agent this belongs to
        tools_count: Number of tools in the revision
        previous_revision_id: UUID of the previous revision (None if first)
        created_at: ISO timestamp of when the revision was created

    Example:
        >>> response = ToolRegistrationResponse(
        ...     tool_definition_id="uuid-here",
        ...     revision_id="uuid-here",
        ...     agent_id="uuid-here",
        ...     tools_count=3,
        ...     previous_revision_id="uuid-here",
        ...     created_at="2025-11-18T16:20:00Z"
        ... )
    """

    tool_definition_id: str = Field(
        ..., description="UUID of the ToolDefinition record"
    )
    revision_id: str = Field(
        ..., description="UUID of the newly created ToolDefinitionRevision"
    )
    agent_id: str = Field(..., description="UUID of the agent this belongs to")
    tools_count: int = Field(..., description="Number of tools in the revision")
    previous_revision_id: str | None = Field(
        None, description="UUID of the previous revision (None if first)"
    )
    created_at: str = Field(
        ..., description="ISO timestamp of when the revision was created"
    )


__all__ = ["ToolRegistrationRequest", "ToolRegistrationResponse"]
