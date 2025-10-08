"""
Guardrail Evaluation Log model for tracking evaluation history.

This module contains the GuardrailEvaluationLog model that stores complete
audit trail of all guardrail evaluations performed via the public API.
All evaluation requests are logged regardless of whether guardrails were triggered.
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class GuardrailEvaluationLog(BaseModel):
    """
    Guardrail evaluation log for complete audit trail.

    This table records every guardrail evaluation API call made by AI agents,
    storing both the request context and evaluation results. Individual columns
    store frequently-queried fields with indexes, while detailed data is stored
    in the log_data JSONB column for flexibility.

    Attributes:
        id: Unique identifier for the log entry (UUID primary key)
        request_id: Server-generated unique request ID (required, unique)
        agent_id: Agent that made the evaluation request (required, indexed)
        project_id: Project the agent belongs to (required, indexed)
        organization_id: Organization (denormalized for RLS, required, indexed)
        trace_id: Optional trace ID from external tracing system (LangFuse, etc.)
        timing: When evaluation occurred - "on_start" or "on_end" (required, indexed)
        process_type: Type of process - "llm", "tool", "retrieval", "agent" (required, indexed)
        should_proceed: Final evaluation decision (required)
        log_data: JSONB containing detailed evaluation data (required)
        created_at: Timestamp when evaluation was performed (inherited, auto-managed)

    JSONB log_data structure:
        {
            "process_name": "get_weather_tool",
            "request_context": {
                "input": {...},
                "output": {...}
            },
            "evaluated_guardrail_ids": ["uuid1", "uuid2"],
            "triggered_guardrail_ids": ["uuid1"],
            "evaluation_result": {
                "triggered_guardrails": [...],
                "metadata": {...}
            },
            "evaluation_time_ms": 45
        }

    Relationships:
        agent: The agent that made the request
        project: The project this evaluation belongs to
        organization: The organization (via project)

    Example:
        >>> # Create evaluation log
        >>> log = GuardrailEvaluationLog(
        ...     request_id="req_a1b2c3d4e5f6",
        ...     agent_id=agent_id,
        ...     project_id=project_id,
        ...     organization_id=org_id,
        ...     trace_id="langfuse_trace_xxx",
        ...     timing="on_start",
        ...     process_type="tool",
        ...     should_proceed=False,
        ...     log_data={
        ...         "process_name": "get_weather_tool",
        ...         "request_context": {...},
        ...         "evaluation_result": {...}
        ...     }
        ... )
        >>> session.add(log)
        >>> await session.commit()
        >>>
        >>> # Query logs for an agent
        >>> logs = await session.execute(
        ...     select(GuardrailEvaluationLog)
        ...     .where(GuardrailEvaluationLog.agent_id == agent_id)
        ...     .order_by(GuardrailEvaluationLog.created_at.desc())
        ... )

    Note:
        - All API calls are logged (triggered or not) for complete audit trail
        - request_id is server-generated and globally unique
        - timing and process_type enable filtering evaluations
        - organization_id is denormalized for efficient RLS
        - log_data JSONB provides flexibility for future schema changes
        - GIN index on log_data enables fast JSONB queries
        - created_at semantically represents "evaluated_at"
    """

    __tablename__ = "guardrail_evaluation_logs"

    id = uuid_column(primary_key=True)
    request_id = Column(
        Text,
        nullable=False,
        unique=True,
        comment="Server-generated unique request ID",
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent that made the evaluation request",
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
    timing = Column(
        Text,
        nullable=False,
        comment="Evaluation timing: on_start or on_end",
    )
    process_type = Column(
        Text,
        nullable=False,
        comment="Process type: llm, tool, retrieval, agent",
    )
    should_proceed = Column(
        Boolean,
        nullable=False,
        comment="Final evaluation decision",
    )
    log_data = Column(
        JSONB,
        nullable=False,
        comment="JSONB containing detailed evaluation data",
    )

    # Relationships
    agent = relationship("Agent", backref="evaluation_logs")
    project = relationship("Project", backref="evaluation_logs")
    organization = relationship("Organization", backref="evaluation_logs")

    __table_args__ = (
        UniqueConstraint(
            "request_id", name="guardrail_evaluation_logs_request_id_unique"
        ),
        Index("guardrail_evaluation_logs_request_id_idx", "request_id"),
        Index("guardrail_evaluation_logs_agent_id_idx", "agent_id"),
        Index("guardrail_evaluation_logs_project_id_idx", "project_id"),
        Index("guardrail_evaluation_logs_organization_id_idx", "organization_id"),
        Index("guardrail_evaluation_logs_timing_idx", "timing"),
        Index("guardrail_evaluation_logs_process_type_idx", "process_type"),
        Index("guardrail_evaluation_logs_created_at_idx", "created_at"),
        Index(
            "guardrail_evaluation_logs_log_data_gin_idx",
            "log_data",
            postgresql_using="gin",
        ),
    )


__all__ = [
    "GuardrailEvaluationLog",
]
