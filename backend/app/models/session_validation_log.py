"""
Session Validation Log model for tracking session-based validation history.

This module contains the SessionValidationLog model that stores validation
history for session-generated guardrails. Used for displaying validation
history in the frontend.
"""

from sqlalchemy import Column, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class SessionValidationLog(BaseModel):
    """
    Session validation log for audit trail and UI display.

    Records every session-based guardrail validation. Displayed in the
    frontend at /projects/{project_id}/agents/{agent_id}/sessions/{session_id}
    in the "Validation History" section.

    Attributes:
        id: Unique identifier for the log entry (UUID primary key)
        session_id: Session that contains the guardrails (required, indexed)
        agent_id: Agent that made the validation request (required, indexed)
        project_id: Project the agent belongs to (required, indexed)
        organization_id: Organization (denormalized for RLS, required, indexed)
        trace_id: Optional trace ID from external tracing system
        log_data: JSONB containing validation details (required)
        created_at: Timestamp when validation was performed (inherited, auto-managed)
        updated_at: Timestamp when log was last updated (inherited, auto-managed)

    JSONB log_data structure:
        {
            "process_name": "get_weather_tool",
            "process_type": "tool",
            "timing": "on_start",
            "context": {"input": {...}, "output": {...}},
            "validation_result": {
                "should_proceed": true,
                "triggered_guardrails": [...],
                "metadata": {...}
            },
            "session_alignment_history_id": "uuid"
        }

    Example:
        >>> # Create validation log
        >>> log = SessionValidationLog(
        ...     session_id=session_id,
        ...     agent_id=agent_id,
        ...     project_id=project_id,
        ...     organization_id=org_id,
        ...     trace_id="langfuse_trace_xxx",
        ...     log_data={
        ...         "process_name": "get_weather_tool",
        ...         "process_type": "tool",
        ...         "timing": "on_start",
        ...         "context": {...},
        ...         "validation_result": {...}
        ...     }
        ... )
        >>> session.add(log)
        >>> await session.commit()
    """

    __tablename__ = "session_validation_logs"

    id = uuid_column(primary_key=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session that contains the guardrails",
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent that made the validation request",
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project the agent belongs to",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization (denormalized for RLS)",
    )
    trace_id = Column(
        Text,
        nullable=True,
        comment="Optional trace ID from external tracing system",
    )
    log_data = Column(
        JSONB,
        nullable=False,
        comment="JSONB containing validation details",
    )

    # Relationships
    session = relationship("Session", backref="validation_logs")
    agent = relationship("Agent")
    project = relationship("Project")
    organization = relationship("Organization")

    __table_args__ = (
        Index("session_validation_logs_session_id_idx", "session_id"),
        Index("session_validation_logs_agent_id_idx", "agent_id"),
        Index("session_validation_logs_project_id_idx", "project_id"),
        Index("session_validation_logs_organization_id_idx", "organization_id"),
        Index("session_validation_logs_created_at_idx", "created_at"),
        Index(
            "session_validation_logs_log_data_gin_idx",
            "log_data",
            postgresql_using="gin",
        ),
    )


__all__ = ["SessionValidationLog"]
