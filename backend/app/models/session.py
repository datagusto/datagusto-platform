"""
Session models for tracking agent conversation sessions and alignment history.

This module contains session-related SQLAlchemy models for managing agent
conversation sessions and their alignment history. Sessions track the lifecycle
of agent interactions, while alignment history records the evolution of
alignment results over time.

Models:
    - Session: Core session entity for agent conversation tracking
    - SessionAlignmentHistory: Alignment history records for each session
"""

from sqlalchemy import Column, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class Session(BaseModel):
    """
    Session model for tracking agent conversation sessions.

    Sessions represent individual conversation contexts for agents, tracking
    the lifecycle of agent interactions including alignment state and history.

    Attributes:
        id: Unique identifier for the session (UUID primary key)
        agent_id: Agent this session belongs to (required)
        project_id: Project (denormalized from agent for RLS, required)
        organization_id: Organization (denormalized from agent for RLS, required)
        status: Session lifecycle status (active, completed, expired)
        created_at: Timestamp when session was created (auto-managed)
        updated_at: Timestamp when session was last updated (auto-managed)

    Relationships:
        agent: The agent this session belongs to
        project: The project (via agent)
        organization: The organization (via agent)
        alignment_history: Alignment history records for this session

    Example:
        >>> # Create new session
        >>> session = Session(
        ...     agent_id=agent_id,
        ...     project_id=project_id,
        ...     organization_id=org_id,
        ...     status="active"
        ... )
        >>> db_session.add(session)
        >>> await db_session.commit()
        >>>
        >>> # Query active sessions for agent
        >>> sessions = await db_session.execute(
        ...     select(Session)
        ...     .where(
        ...         Session.agent_id == agent_id,
        ...         Session.status == "active"
        ...     )
        ...     .order_by(Session.created_at.desc())
        ... )

    Note:
        - agent_id is required (sessions belong to agents)
        - project_id and organization_id are denormalized for efficient RLS
        - status uses TEXT for flexibility (not ENUM)
        - Common status values: "active", "completed", "expired"
    """

    __tablename__ = "sessions"

    id = uuid_column(primary_key=True)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent this session belongs to",
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project (denormalized from agent for RLS)",
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
        default="active",
        comment="Session lifecycle status (active, completed, expired)",
    )

    # Relationships
    agent = relationship("Agent", backref="sessions")
    project = relationship("Project", backref="sessions")
    organization = relationship("Organization", backref="sessions")
    alignment_history = relationship(
        "SessionAlignmentHistory",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionAlignmentHistory.created_at.desc()",
    )

    __table_args__ = (
        Index("sessions_agent_id_idx", "agent_id"),
        Index("sessions_project_id_idx", "project_id"),
        Index("sessions_organization_id_idx", "organization_id"),
        Index("sessions_status_idx", "status"),
        Index("sessions_agent_status_idx", "agent_id", "status"),
        Index("sessions_created_at_idx", "created_at"),
    )


class SessionAlignmentHistory(BaseModel):
    """
    Alignment history for tracking alignment results over time.

    This model records the evolution of alignment results for each session,
    storing key terms extraction, tool invocation rules, and other alignment
    data. The latest record represents the current alignment state.

    Attributes:
        id: Unique identifier for the alignment history record (UUID primary key)
        session_id: Session this alignment belongs to (required)
        agent_id: Agent (denormalized from session for fast queries, required)
        user_instruction: User instruction for this alignment iteration (required)
        past_instructions_history: Past instructions history for context (optional)
        previous_extraction_output: Previous extraction output for iteration (optional)
        alignment_result: JSONB containing alignment data (key_terms, tool_invocation_rules)
        created_at: Timestamp when alignment was created (auto-managed)
        updated_at: Timestamp when alignment was last updated (auto-managed)

    Relationships:
        session: The session this alignment belongs to
        agent: The agent (denormalized)

    Example:
        >>> # Create alignment history record
        >>> alignment = SessionAlignmentHistory(
        ...     session_id=session_id,
        ...     agent_id=agent_id,
        ...     user_instruction="Analyze exam results for spring semester",
        ...     past_instructions_history="Previous instruction context...",
        ...     previous_extraction_output='{"key_terms": [...]}',
        ...     alignment_result={
        ...         "key_terms": [...],  # KeyTermsOutput
        ...         "tool_invocation_rules": [...]  # Generated rules
        ...     }
        ... )
        >>> db_session.add(alignment)
        >>> await db_session.commit()
        >>>
        >>> # Get latest alignment for session
        >>> latest = await db_session.execute(
        ...     select(SessionAlignmentHistory)
        ...     .where(SessionAlignmentHistory.session_id == session_id)
        ...     .order_by(SessionAlignmentHistory.created_at.desc())
        ...     .limit(1)
        ... )
        >>> latest_alignment = latest.scalar_one_or_none()

    Note:
        - session_id is required (alignment belongs to session)
        - agent_id is denormalized for fast queries without joins
        - user_instruction stores the input that triggered this alignment
        - past_instructions_history stores context from previous instructions (optional)
        - previous_extraction_output stores previous extraction result (optional)
        - alignment_result uses JSONB for flexible schema evolution
        - alignment_result structure: {"key_terms": [...], "tool_invocation_rules": [...]}
        - created_at is used for ordering (latest first with DESC)
        - GIN index on alignment_result enables fast JSON queries
    """

    __tablename__ = "session_alignment_history"

    id = uuid_column(primary_key=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session this alignment belongs to",
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent (denormalized for fast queries)",
    )
    user_instruction = Column(
        Text,
        nullable=False,
        comment="User instruction for this alignment iteration",
    )
    past_instructions_history = Column(
        Text,
        nullable=True,
        comment="Past instructions history (for context in key term extraction)",
    )
    previous_extraction_output = Column(
        Text,
        nullable=True,
        comment="Previous extraction output (for iterative key term extraction)",
    )
    alignment_result = Column(
        JSONB,
        nullable=False,
        comment="JSONB containing alignment data (key_terms, tool_invocation_rules)",
    )

    # Relationships
    session = relationship("Session", back_populates="alignment_history")
    agent = relationship("Agent", backref="alignment_history")

    __table_args__ = (
        Index("session_alignment_history_session_id_idx", "session_id"),
        Index("session_alignment_history_agent_id_idx", "agent_id"),
        Index("session_alignment_history_created_at_idx", "created_at"),
        Index(
            "session_alignment_history_session_created_at_idx",
            "session_id",
            "created_at",
        ),
        Index(
            "session_alignment_history_alignment_result_gin_idx",
            "alignment_result",
            postgresql_using="gin",
        ),
    )


__all__ = [
    "Session",
    "SessionAlignmentHistory",
]
