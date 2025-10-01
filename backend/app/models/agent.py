"""
Agent models for multi-tenant architecture.

This module contains all agent-related SQLAlchemy models following
ultra-fine-grained table separation principles. Agents are API-accessible
entities that users create within projects to enable programmatic access.

Models:
    - Agent: Core agent entity (identity only)
    - AgentAPIKey: API key management for authentication
    - AgentActiveStatus: Active agent tracking (presence-based)
    - AgentArchive: Soft delete pattern for agents
"""

from sqlalchemy import (
    Column,
    Text,
    ForeignKey,
    Index,
    String,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel, uuid_column


class Agent(BaseModel):
    """
    Core agents table for API-based programmatic access.

    Agents are entities created within projects that enable API access
    to the system. Each agent has API keys for authentication.

    Attributes:
        id: Unique identifier for the agent (UUID primary key)
        project_id: Project this agent belongs to (required)
        organization_id: Organization (denormalized from project, required)
        name: Agent display name (required)
        created_by: User who created the agent (required, audit trail)
        created_at: Timestamp when agent was created (auto-managed)
        updated_at: Timestamp when agent was last updated (auto-managed)

    Relationships:
        project: The project this agent belongs to
        organization: The organization (via project)
        creator: User who created the agent
        api_keys: API keys associated with this agent
        active_status: Active status record (AgentActiveStatus, one-to-one)
        archive: Archive record if soft-deleted (AgentArchive, one-to-one)

    Example:
        >>> # Create new agent
        >>> agent = Agent(
        ...     project_id=project_id,
        ...     organization_id=org_id,  # Denormalized from project
        ...     name="Production API Agent",
        ...     created_by=user_id
        ... )
        >>> session.add(agent)
        >>> await session.commit()
        >>>
        >>> # Query agents in project
        >>> agents = await session.execute(
        ...     select(Agent)
        ...     .where(Agent.project_id == project_id)
        ...     .order_by(Agent.created_at.desc())
        ... )

    Note:
        - project_id is required (agents belong to projects)
        - organization_id is denormalized for efficient RLS
        - name is required (no anonymous agents)
        - created_by provides audit trail
        - RLS policies automatically filter by organization_id
    """

    __tablename__ = "agents"

    id = uuid_column(primary_key=True)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project this agent belongs to",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization (denormalized from project for RLS)",
    )
    name = Column(Text, nullable=False, comment="Agent display name")
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the agent",
    )

    # Relationships
    project = relationship("Project", backref="agents")
    organization = relationship("Organization", backref="agents")
    creator = relationship("User", foreign_keys=[created_by], backref="created_agents")
    api_keys = relationship(
        "AgentAPIKey", back_populates="agent", cascade="all, delete-orphan"
    )
    active_status = relationship(
        "AgentActiveStatus",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
    archive = relationship(
        "AgentArchive",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("agents_project_id_idx", "project_id"),
        Index("agents_organization_id_idx", "organization_id"),
        Index("agents_name_idx", "name"),
        Index("agents_project_name_idx", "project_id", "name"),
    )


class AgentAPIKey(BaseModel):
    """
    Agent API keys for authentication.

    This table stores hashed API keys and their metadata. Keys are hashed
    using bcrypt (like passwords) and only the hash is stored. The plain
    text key is shown only once at creation time.

    Attributes:
        id: Unique identifier for the API key (UUID primary key)
        agent_id: FK to agents
        key_prefix: First 12-16 characters of key for identification
        key_hash: Bcrypt hashed full key (never plain text)
        name: Optional friendly name for the key
        last_used_at: Timestamp of last usage (for security auditing)
        expires_at: Optional expiration date (NULL = never expires)
        created_by: User who created the key (audit trail)
        created_at: Timestamp when key was created (auto-managed)
        updated_at: Timestamp when key was last updated (auto-managed)

    Relationships:
        agent: The agent this key belongs to
        creator: User who created the key

    Example:
        >>> # Create API key
        >>> from app.core.security import generate_api_key, hash_api_key
        >>>
        >>> raw_key = generate_api_key("agt_live")  # Returns full key
        >>> # "agt_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p"
        >>>
        >>> api_key = AgentAPIKey(
        ...     agent_id=agent_id,
        ...     key_prefix=raw_key[:16],  # "agt_live_1a2b3c4"
        ...     key_hash=hash_api_key(raw_key),  # Bcrypt hash
        ...     name="Production API",
        ...     created_by=user_id
        ... )
        >>> session.add(api_key)
        >>> await session.commit()
        >>>
        >>> # Display raw_key to user ONCE (cannot retrieve later)
        >>> return {"api_key": raw_key}  # ⚠️ Only time it's shown

    Note:
        - key_hash stores bcrypt hash (never plain text)
        - key_prefix is unique and used for fast lookup
        - Plain text key shown only once at creation
        - Multiple keys per agent enable key rotation
        - expires_at enables time-limited access
    """

    __tablename__ = "agent_api_keys"

    id = uuid_column(primary_key=True)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        comment="Agent this key belongs to",
    )
    key_prefix = Column(
        String(16),
        nullable=False,
        unique=True,
        comment="First 12-16 characters of key (for identification)",
    )
    key_hash = Column(Text, nullable=False, comment="Bcrypt hashed full key")
    name = Column(Text, nullable=True, comment="Optional friendly name for the key")
    last_used_at = Column(
        TIMESTAMP(timezone=True), nullable=True, comment="Timestamp of last usage"
    )
    expires_at = Column(
        TIMESTAMP(timezone=True), nullable=True, comment="Optional expiration date"
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the key",
    )

    # Relationships
    agent = relationship("Agent", back_populates="api_keys")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("agent_api_keys_agent_id_idx", "agent_id"),
        Index("agent_api_keys_prefix_idx", "key_prefix", unique=True),
        Index("agent_api_keys_expires_at_idx", "expires_at"),
    )


class AgentActiveStatus(BaseModel):
    """
    Active agents tracking using presence-based state management.

    Attributes:
        agent_id: FK to agents (primary key)
        created_at: When the agent was activated (inherited, semantically "activated_at")

    Relationships:
        agent: The agent this status belongs to

    Example:
        >>> # Activate agent
        >>> status = AgentActiveStatus(agent_id=agent_id)
        >>> session.add(status)
        >>> await session.commit()
        >>>
        >>> # Check if active
        >>> result = await session.execute(
        ...     select(AgentActiveStatus)
        ...     .where(AgentActiveStatus.agent_id == agent_id)
        ... )
        >>> is_active = result.scalar_one_or_none() is not None
        >>>
        >>> # Deactivate agent
        >>> await session.delete(status)
        >>> await session.commit()

    Note:
        - No updated_at needed for status table (state is binary)
        - Activation timestamp is stored in created_at
        - To deactivate, simply delete the record
    """

    __tablename__ = "agent_active_status"

    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Agent ID (also primary key)",
    )

    # Override BaseModel to remove updated_at
    updated_at = None

    # Relationship
    agent = relationship("Agent", back_populates="active_status")


class AgentArchive(BaseModel):
    """
    Agent archives (soft delete pattern).

    Attributes:
        agent_id: FK to agents (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving)
        created_at: When agent was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        agent: The archived agent
        archiver: User who performed the archiving

    Example:
        >>> # Archive agent
        >>> archive = AgentArchive(
        ...     agent_id=agent_id,
        ...     reason="Agent no longer needed",
        ...     archived_by=user_id
        ... )
        >>> session.add(archive)
        >>> await session.commit()
        >>>
        >>> # Check if archived
        >>> result = await session.execute(
        ...     select(AgentArchive)
        ...     .where(AgentArchive.agent_id == agent_id)
        ... )
        >>> is_archived = result.scalar_one_or_none() is not None

    Note:
        - Soft delete: agent record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "agent_archives"

    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived agent ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the archiving",
    )

    # Relationships
    agent = relationship("Agent", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


__all__ = [
    "Agent",
    "AgentAPIKey",
    "AgentActiveStatus",
    "AgentArchive",
]