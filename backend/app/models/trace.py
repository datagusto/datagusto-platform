"""
Trace and Observation models for multi-tenant architecture.

This module contains all trace and observation-related SQLAlchemy models
following ultra-fine-grained table separation principles. Traces and
observations implement distributed tracing for agent execution logging
and performance tracking.

Models:
    - Trace: Core trace entity (agent execution record)
    - Observation: Execution step within a trace (hierarchical)
    - TraceArchive: Soft delete pattern for traces
    - ObservationArchive: Soft delete pattern for observations
"""

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class Trace(BaseModel):
    """
    Core traces table for agent execution tracking.

    Each trace represents a complete agent execution from start to finish,
    containing overall status, timing, and metadata. Traces contain multiple
    observations that form a hierarchical execution tree.

    Attributes:
        id: Unique identifier for the trace (UUID primary key)
        agent_id: Agent this trace belongs to (required)
        project_id: Project (denormalized from agent, required)
        organization_id: Organization (denormalized from agent, required)
        status: Execution status (pending, running, completed, failed, error)
        started_at: When trace execution began (required)
        ended_at: When trace execution completed (NULL = still running)
        trace_metadata: JSONB containing inputs, outputs, tags, costs, errors (DB column: metadata)
        created_at: Timestamp when trace was created (auto-managed)
        updated_at: Timestamp when trace was last updated (auto-managed)

    Relationships:
        agent: The agent this trace belongs to
        project: The project (via agent)
        organization: The organization (via agent)
        observations: Execution steps within this trace (Observation)
        archive: Archive record if soft-deleted (TraceArchive, one-to-one)

    Example:
        >>> # Create new trace
        >>> trace = Trace(
        ...     agent_id=agent_id,
        ...     project_id=project_id,
        ...     organization_id=org_id,
        ...     status="running",
        ...     started_at=datetime.utcnow(),
        ...     metadata={"input": {"prompt": "..."}, "tags": ["production"]}
        ... )
        >>> session.add(trace)
        >>> await session.commit()
        >>>
        >>> # Query traces for agent
        >>> traces = await session.execute(
        ...     select(Trace)
        ...     .where(Trace.agent_id == agent_id)
        ...     .order_by(Trace.started_at.desc())
        ... )

    Note:
        - status is text field for flexibility (not ENUM)
        - ended_at is NULL while trace is still running
        - metadata stores flexible execution data (JSONB)
        - GIN index on metadata enables fast JSONB queries
        - project_id and organization_id denormalized for query efficiency
    """

    __tablename__ = "traces"

    id = uuid_column(primary_key=True)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent this trace belongs to",
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project (denormalized from agent)",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization (denormalized from agent for RLS)",
    )
    status = Column(
        Text,
        nullable=False,
        default="pending",
        comment="Execution status (pending, running, completed, failed, error)",
    )
    started_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="When trace execution began",
    )
    ended_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When trace execution completed (NULL = still running)",
    )
    trace_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default={},
        comment="JSONB containing inputs, outputs, tags, costs, errors",
    )

    # Relationships
    agent = relationship("Agent", backref="traces")
    project = relationship("Project", backref="traces")
    organization = relationship("Organization", backref="traces")
    observations = relationship(
        "Observation", back_populates="trace", cascade="all, delete-orphan"
    )
    archive = relationship(
        "TraceArchive",
        back_populates="trace",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("traces_agent_id_idx", "agent_id"),
        Index("traces_project_id_idx", "project_id"),
        Index("traces_organization_id_idx", "organization_id"),
        Index("traces_status_idx", "status"),
        Index("traces_started_at_idx", "started_at"),
        Index("traces_ended_at_idx", "ended_at"),
        Index("traces_metadata_gin_idx", "metadata", postgresql_using="gin"),
        Index("traces_agent_started_idx", "agent_id", "started_at"),
        Index("traces_project_started_idx", "project_id", "started_at"),
    )


class Observation(BaseModel):
    """
    Core observations table for trace execution steps.

    Observations represent individual steps within a trace execution (LLM calls,
    tool executions, retrievals, etc.). They form a hierarchical tree structure
    via parent_observation_id for nested operations.

    Attributes:
        id: Unique identifier for the observation (UUID primary key)
        trace_id: Trace this observation belongs to (required)
        parent_observation_id: Parent observation for hierarchy (NULL = root)
        type: Observation type (llm, tool, retriever, agent, embedding, custom)
        name: Display name for the observation (required)
        status: Execution status (pending, running, completed, failed, error)
        started_at: When observation began (required)
        ended_at: When observation completed (NULL = still running)
        observation_metadata: JSONB containing step-specific data (DB column: metadata)
        created_at: Timestamp when observation was created (auto-managed)
        updated_at: Timestamp when observation was last updated (auto-managed)

    Relationships:
        trace: The trace this observation belongs to
        parent_observation: Parent observation (for hierarchy)
        child_observations: Child observations (for hierarchy)
        archive: Archive record if soft-deleted (ObservationArchive, one-to-one)

    Example:
        >>> # Create root observation
        >>> obs1 = Observation(
        ...     trace_id=trace_id,
        ...     parent_observation_id=None,  # Root observation
        ...     type="agent",
        ...     name="Agent Execution",
        ...     status="running",
        ...     started_at=datetime.utcnow(),
        ...     metadata={"input": {...}}
        ... )
        >>> session.add(obs1)
        >>> await session.commit()
        >>>
        >>> # Create child observation
        >>> obs2 = Observation(
        ...     trace_id=trace_id,
        ...     parent_observation_id=obs1.id,  # Child of obs1
        ...     type="llm",
        ...     name="LLM Call: GPT-4",
        ...     status="running",
        ...     started_at=datetime.utcnow(),
        ...     metadata={"model": {"provider": "openai", "name": "gpt-4"}}
        ... )
        >>> session.add(obs2)
        >>> await session.commit()

    Note:
        - parent_observation_id is NULL for root observations
        - type is text field for flexibility (not ENUM)
        - Self-referencing foreign key enables tree structure
        - CASCADE delete when parent observation is deleted
        - GIN index on metadata enables fast JSONB queries
    """

    __tablename__ = "observations"

    id = uuid_column(primary_key=True)
    trace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        comment="Trace this observation belongs to",
    )
    parent_observation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=True,
        comment="Parent observation for hierarchy (NULL = root)",
    )
    type = Column(
        Text,
        nullable=False,
        comment="Observation type (llm, tool, retriever, agent, embedding, custom)",
    )
    name = Column(Text, nullable=False, comment="Display name for the observation")
    status = Column(
        Text,
        nullable=False,
        default="pending",
        comment="Execution status (pending, running, completed, failed, error)",
    )
    started_at = Column(
        TIMESTAMP(timezone=True), nullable=False, comment="When observation began"
    )
    ended_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When observation completed (NULL = still running)",
    )
    observation_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default={},
        comment="JSONB containing step-specific data (tokens, cost, latency)",
    )

    # Relationships
    trace = relationship("Trace", back_populates="observations")
    parent_observation = relationship(
        "Observation",
        remote_side=[id],
        backref="child_observations",
        foreign_keys=[parent_observation_id],
    )
    archive = relationship(
        "ObservationArchive",
        back_populates="observation",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("observations_trace_id_idx", "trace_id"),
        Index("observations_parent_observation_id_idx", "parent_observation_id"),
        Index("observations_type_idx", "type"),
        Index("observations_status_idx", "status"),
        Index("observations_started_at_idx", "started_at"),
        Index("observations_metadata_gin_idx", "metadata", postgresql_using="gin"),
        Index("observations_trace_parent_idx", "trace_id", "parent_observation_id"),
        Index("observations_trace_started_idx", "trace_id", "started_at"),
    )


class TraceArchive(BaseModel):
    """
    Trace archives (soft delete pattern).

    Attributes:
        trace_id: FK to traces (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving, optional)
        created_at: When trace was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        trace: The archived trace
        archiver: User who performed the archiving (optional)

    Example:
        >>> # Archive trace
        >>> archive = TraceArchive(
        ...     trace_id=trace_id,
        ...     reason="Trace older than retention period",
        ...     archived_by=user_id
        ... )
        >>> session.add(archive)
        >>> await session.commit()

    Note:
        - Soft delete: trace record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - archived_by can be NULL (automated archival)
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "trace_archives"

    trace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("traces.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived trace ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="User who performed the archiving (NULL for automated)",
    )

    # Relationships
    trace = relationship("Trace", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


class ObservationArchive(BaseModel):
    """
    Observation archives (soft delete pattern).

    Attributes:
        observation_id: FK to observations (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving, optional)
        created_at: When observation was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        observation: The archived observation
        archiver: User who performed the archiving (optional)

    Example:
        >>> # Archive observation
        >>> archive = ObservationArchive(
        ...     observation_id=observation_id,
        ...     reason="Observation older than retention period",
        ...     archived_by=None  # Automated archival
        ... )
        >>> session.add(archive)
        >>> await session.commit()

    Note:
        - Soft delete: observation record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - archived_by can be NULL (automated archival)
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "observation_archives"

    observation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("observations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived observation ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="User who performed the archiving (NULL for automated)",
    )

    # Relationships
    observation = relationship("Observation", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


__all__ = [
    "Trace",
    "Observation",
    "TraceArchive",
    "ObservationArchive",
]
