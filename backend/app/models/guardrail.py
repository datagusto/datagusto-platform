"""
Guardrail models for multi-tenant architecture.

This module contains all guardrail-related SQLAlchemy models following
ultra-fine-grained table separation principles. Guardrails are rules and
policies that can be assigned to agents to control their behavior and
ensure safe operation.

Models:
    - Guardrail: Core guardrail entity with JSONB definition
    - GuardrailAgentAssignment: Many-to-many agent-guardrail relationship
    - GuardrailActiveStatus: Active guardrail tracking (presence-based)
    - GuardrailArchive: Soft delete pattern for guardrails

Enums:
    - TriggerType: When guardrail evaluation occurs (on_start, on_end)
    - ActionType: Type of action to execute (block, warn, modify)
"""

from enum import Enum

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class TriggerType(str, Enum):
    """
    Guardrail trigger timing enum.

    Defines when guardrail evaluation should occur during AI agent execution.
    Simplified from previous model to two clear timing points.

    Values:
        on_start: Evaluate before process execution (e.g., before LLM call, before tool execution)
        on_end: Evaluate after process execution (e.g., after LLM response, after tool output)

    Note:
        Previous values (before_execution, after_execution, on_error, on_input, on_output)
        have been deprecated in favor of this simplified timing model.
    """

    ON_START = "on_start"
    ON_END = "on_end"


class ActionType(str, Enum):
    """
    Guardrail action type enum.

    Defines the type of action to execute when a guardrail is triggered.

    Values:
        block: Block the process from continuing (should_proceed=False)
        warn: Issue a warning but allow configuration of whether to proceed
        modify: Modify the data before processing continues (should_proceed=True)

    Note:
        Previous action types (log, notify) have been removed:
        - log: All API calls are now automatically logged to GuardrailEvaluationLog
        - notify: Audit Trail provides sufficient visibility without separate notifications
    """

    BLOCK = "block"
    WARN = "warn"
    MODIFY = "modify"


class Guardrail(BaseModel):
    """
    Core guardrails table for rule and policy management.

    Guardrails define rules that can be assigned to agents to control behavior,
    enforce constraints, and ensure safe operation. Definition logic is stored
    as JSONB for flexibility.

    Attributes:
        id: Unique identifier for the guardrail (UUID primary key)
        project_id: Project this guardrail belongs to (required)
        organization_id: Organization (denormalized from project, required)
        name: Guardrail display name (required)
        definition: JSONB containing trigger conditions and actions (required)
        created_by: User who created the guardrail (required, audit trail)
        created_at: Timestamp when guardrail was created (auto-managed)
        updated_at: Timestamp when guardrail was last updated (auto-managed)

    Relationships:
        project: The project this guardrail belongs to
        organization: The organization (via project)
        creator: User who created the guardrail
        agent_assignments: Agent assignment records (GuardrailAgentAssignment)
        active_status: Active status record (GuardrailActiveStatus, one-to-one)
        archive: Archive record if soft-deleted (GuardrailArchive, one-to-one)

    Example:
        >>> # Create new guardrail
        >>> guardrail = Guardrail(
        ...     project_id=project_id,
        ...     organization_id=org_id,
        ...     name="Block offensive content",
        ...     definition={
        ...         "version": "1.0",
        ...         "trigger": {"type": "on_input", "conditions": [...]},
        ...         "actions": [{"type": "block", "priority": 1}]
        ...     },
        ...     created_by=user_id
        ... )
        >>> session.add(guardrail)
        >>> await session.commit()
        >>>
        >>> # Query guardrails in project
        >>> guardrails = await session.execute(
        ...     select(Guardrail)
        ...     .where(Guardrail.project_id == project_id)
        ...     .order_by(Guardrail.name)
        ... )

    Note:
        - project_id is required (guardrails belong to projects)
        - organization_id is denormalized for efficient RLS
        - definition is validated at application layer (JSON schema)
        - GIN index on definition enables fast JSONB queries
    """

    __tablename__ = "guardrails"

    id = uuid_column(primary_key=True)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project this guardrail belongs to",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization (denormalized from project for RLS)",
    )
    name = Column(Text, nullable=False, comment="Guardrail display name")
    definition = Column(
        JSONB,
        nullable=False,
        comment="JSONB containing trigger conditions and actions",
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the guardrail",
    )

    # Relationships
    project = relationship("Project", backref="guardrails")
    organization = relationship("Organization", backref="guardrails")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_guardrails"
    )
    agent_assignments = relationship(
        "GuardrailAgentAssignment",
        back_populates="guardrail",
        cascade="all, delete-orphan",
    )
    active_status = relationship(
        "GuardrailActiveStatus",
        back_populates="guardrail",
        uselist=False,
        cascade="all, delete-orphan",
    )
    archive = relationship(
        "GuardrailArchive",
        back_populates="guardrail",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("guardrails_project_id_idx", "project_id"),
        Index("guardrails_organization_id_idx", "organization_id"),
        Index("guardrails_name_idx", "name"),
        Index("guardrails_definition_gin_idx", "definition", postgresql_using="gin"),
        Index("guardrails_project_name_idx", "project_id", "name"),
    )


class GuardrailAgentAssignment(BaseModel):
    """
    Guardrail to Agent assignments (many-to-many relationship).

    This junction table tracks which guardrails are assigned to which agents,
    with audit information about who made the assignment and when.

    Attributes:
        id: Unique assignment record ID (UUID primary key)
        project_id: Project (denormalized for RLS, required)
        guardrail_id: FK to guardrails (required)
        agent_id: FK to agents (required)
        assigned_by: User who made the assignment (audit trail)
        created_at: When assignment was created (inherited, semantically "assigned_at")
        updated_at: When assignment record was last updated

    Relationships:
        project: The project (for RLS)
        guardrail: The guardrail
        agent: The agent
        assigner: User who made the assignment

    Example:
        >>> # Assign guardrail to agent
        >>> assignment = GuardrailAgentAssignment(
        ...     project_id=project_id,
        ...     guardrail_id=guardrail_id,
        ...     agent_id=agent_id,
        ...     assigned_by=user_id
        ... )
        >>> session.add(assignment)
        >>> await session.commit()
        >>>
        >>> # List all guardrails for an agent
        >>> result = await session.execute(
        ...     select(Guardrail)
        ...     .join(GuardrailAgentAssignment)
        ...     .where(GuardrailAgentAssignment.agent_id == agent_id)
        ... )
        >>> guardrails = result.scalars().all()

    Note:
        - Unique constraint on (guardrail_id, agent_id) prevents duplicates
        - project_id denormalized for efficient RLS queries
        - created_at semantically represents "assigned_at"
        - CASCADE delete when guardrail or agent is deleted
    """

    __tablename__ = "guardrail_agent_assignments"

    id = uuid_column(primary_key=True)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project (denormalized for RLS)",
    )
    guardrail_id = Column(
        UUID(as_uuid=True),
        ForeignKey("guardrails.id", ondelete="CASCADE"),
        nullable=False,
        comment="Guardrail ID",
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent ID",
    )
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who made the assignment",
    )

    # Relationships
    project = relationship("Project")
    guardrail = relationship("Guardrail", back_populates="agent_assignments")
    agent = relationship("Agent", backref="guardrail_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint(
            "guardrail_id", "agent_id", name="guardrail_agent_assignments_unique"
        ),
        Index("guardrail_agent_assignments_project_id_idx", "project_id"),
        Index("guardrail_agent_assignments_guardrail_id_idx", "guardrail_id"),
        Index("guardrail_agent_assignments_agent_id_idx", "agent_id"),
        Index("guardrail_agent_assignments_assigned_by_idx", "assigned_by"),
    )


class GuardrailActiveStatus(BaseModel):
    """
    Active guardrails tracking using presence-based state management.

    Attributes:
        guardrail_id: FK to guardrails (primary key)
        created_at: When the guardrail was activated (inherited, semantically "activated_at")

    Relationships:
        guardrail: The guardrail this status belongs to

    Example:
        >>> # Activate guardrail
        >>> status = GuardrailActiveStatus(guardrail_id=guardrail_id)
        >>> session.add(status)
        >>> await session.commit()
        >>>
        >>> # Check if active
        >>> result = await session.execute(
        ...     select(GuardrailActiveStatus)
        ...     .where(GuardrailActiveStatus.guardrail_id == guardrail_id)
        ... )
        >>> is_active = result.scalar_one_or_none() is not None

    Note:
        - No updated_at needed for status table (state is binary)
        - Activation timestamp is stored in created_at
        - To deactivate, simply delete the record
    """

    __tablename__ = "guardrail_active_status"

    guardrail_id = Column(
        UUID(as_uuid=True),
        ForeignKey("guardrails.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Guardrail ID (also primary key)",
    )

    # Override BaseModel to remove updated_at
    updated_at = None

    # Relationship
    guardrail = relationship("Guardrail", back_populates="active_status")


class GuardrailArchive(BaseModel):
    """
    Guardrail archives (soft delete pattern).

    Attributes:
        guardrail_id: FK to guardrails (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving)
        created_at: When guardrail was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        guardrail: The archived guardrail
        archiver: User who performed the archiving

    Example:
        >>> # Archive guardrail
        >>> archive = GuardrailArchive(
        ...     guardrail_id=guardrail_id,
        ...     reason="Guardrail rule deprecated",
        ...     archived_by=user_id
        ... )
        >>> session.add(archive)
        >>> await session.commit()

    Note:
        - Soft delete: guardrail record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "guardrail_archives"

    guardrail_id = Column(
        UUID(as_uuid=True),
        ForeignKey("guardrails.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived guardrail ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the archiving",
    )

    # Relationships
    guardrail = relationship("Guardrail", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


__all__ = [
    "TriggerType",
    "ActionType",
    "Guardrail",
    "GuardrailAgentAssignment",
    "GuardrailActiveStatus",
    "GuardrailArchive",
]
