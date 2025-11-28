"""
Tool Definition models for AI agent tool management.

This module contains SQLAlchemy models for managing AI agent tool definitions
with full revision history tracking. Tool definitions are versioned using a
linked list structure, allowing complete traceability of changes for guardrail
generation and compliance purposes.

Models:
    - ToolDefinition: Core tool definition entity (one per agent)
    - ToolDefinitionRevision: Revision history (linked list structure)
"""

from sqlalchemy import Column, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class ToolDefinition(BaseModel):
    """
    Core tool definitions table for agent tool management.

    Each agent has one ToolDefinition record that tracks the latest revision
    of their tool configuration. The actual tool data is stored in
    ToolDefinitionRevision records, forming a complete revision history.

    Attributes:
        id: Unique identifier for the tool definition (UUID primary key)
        agent_id: Agent this tool definition belongs to (required, unique)
        latest_revision_id: Current active revision (NULL until first revision created)
        created_at: Timestamp when record was created (auto-managed)
        updated_at: Timestamp when record was last updated (auto-managed)

    Relationships:
        agent: The agent this tool definition belongs to
        latest_revision: Current active revision record (ToolDefinitionRevision)
        revisions: All revision records for this agent (ToolDefinitionRevision)

    Example:
        >>> # Create new tool definition for agent
        >>> tool_def = ToolDefinition(
        ...     agent_id=agent_id
        ... )
        >>> session.add(tool_def)
        >>> await session.commit()
        >>>
        >>> # Query tool definition for agent
        >>> tool_def = await session.execute(
        ...     select(ToolDefinition)
        ...     .where(ToolDefinition.agent_id == agent_id)
        ... )

    Note:
        - agent_id is unique (one tool definition per agent)
        - latest_revision_id is NULL until first revision is created
        - CASCADE delete when agent is deleted
        - RESTRICT delete for latest_revision to prevent data loss
    """

    __tablename__ = "tool_definitions"

    id = uuid_column(primary_key=True)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="Agent this tool definition belongs to (unique)",
    )
    latest_revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tool_definition_revisions.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Current active revision (NULL until first revision created)",
    )

    # Relationships
    agent = relationship("Agent", backref="tool_definition")
    latest_revision = relationship(
        "ToolDefinitionRevision",
        foreign_keys=[latest_revision_id],
        uselist=False,
        post_update=True,  # Allows circular reference
    )

    __table_args__ = (
        Index("tool_definitions_agent_id_idx", "agent_id", unique=True),
        Index("tool_definitions_latest_revision_id_idx", "latest_revision_id"),
    )


class ToolDefinitionRevision(BaseModel):
    """
    Tool definition revisions table for version history tracking.

    Each revision represents a snapshot of tool configurations at a specific
    point in time. Revisions form a linked list via previous_revision_id,
    enabling complete history tracking and traceability for guardrail generation.

    Attributes:
        id: Unique identifier for the revision (UUID primary key)
        agent_id: Agent this revision belongs to (required)
        tools_data: JSONB containing tool definitions array (required)
        previous_revision_id: Previous revision in history chain (NULL = first revision)
        created_at: Timestamp when revision was created (auto-managed)
        updated_at: Timestamp when revision was last updated (auto-managed)

    Relationships:
        agent: The agent this revision belongs to
        previous_revision: Previous revision in the chain (for history traversal)
        next_revisions: Next revisions in the chain (backref from previous_revision)

    Example:
        >>> # Create first revision
        >>> revision1 = ToolDefinitionRevision(
        ...     agent_id=agent_id,
        ...     tools_data={"tools": [{"name": "get_weather", ...}]},
        ...     previous_revision_id=None  # First revision
        ... )
        >>> session.add(revision1)
        >>> await session.commit()
        >>>
        >>> # Create second revision (linked to first)
        >>> revision2 = ToolDefinitionRevision(
        ...     agent_id=agent_id,
        ...     tools_data={"tools": [{"name": "get_weather", ...}, {"name": "search", ...}]},
        ...     previous_revision_id=revision1.id  # Link to previous
        ... )
        >>> session.add(revision2)
        >>> await session.commit()
        >>>
        >>> # Traverse history (newest to oldest)
        >>> current = revision2
        >>> while current:
        ...     print(f"Revision {current.id}: {len(current.tools_data['tools'])} tools")
        ...     current = current.previous_revision

    Tools Data JSONB Structure:
        {
            "tools": [
                {
                    "name": "tool_name",
                    "description": "What the tool does",
                    "input_schema": {"type": "object", "properties": {...}},
                    "output_schema": {"type": "object", "properties": {...}},
                    "metadata": {"version": "1.0.0", "tags": [...]}
                },
                ...
            ]
        }

    Note:
        - previous_revision_id is NULL for the first revision
        - Self-referencing foreign key enables linked list structure
        - RESTRICT delete prevents breaking the revision chain
        - CASCADE delete when agent is deleted (orphan revisions removed)
        - GIN index on tools_data enables fast JSONB queries
        - No validation on tools_data (stored as-is for flexibility)
    """

    __tablename__ = "tool_definition_revisions"

    id = uuid_column(primary_key=True)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent this revision belongs to",
    )
    tools_data = Column(
        JSONB,
        nullable=False,
        comment="JSONB containing tool definitions array",
    )
    previous_revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tool_definition_revisions.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Previous revision in history chain (NULL = first revision)",
    )

    # Relationships
    agent = relationship("Agent", backref="tool_definition_revisions")
    previous_revision = relationship(
        "ToolDefinitionRevision",
        remote_side=[id],
        backref="next_revisions",
        foreign_keys=[previous_revision_id],
    )

    __table_args__ = (
        Index("tool_definition_revisions_agent_id_idx", "agent_id"),
        Index(
            "tool_definition_revisions_previous_revision_id_idx",
            "previous_revision_id",
        ),
        Index(
            "tool_definition_revisions_tools_data_gin_idx",
            "tools_data",
            postgresql_using="gin",
        ),
        Index("tool_definition_revisions_created_at_idx", "created_at"),
    )


__all__ = ["ToolDefinition", "ToolDefinitionRevision"]
