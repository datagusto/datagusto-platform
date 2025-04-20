from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class AgentStatus(str, enum.Enum):
    """Status of an Agent."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class Agent(Base):
    """SQLAlchemy Agent model."""
    
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    api_key = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.ACTIVE)
    config = Column(JSONB, nullable=True)
    observability_config = Column(JSONB, nullable=True, comment="Connection configuration for observability platforms")
    
    # Relationships
    organization = relationship("Organization", back_populates="agents")
    creator = relationship("User", backref="created_agents")
    traces = relationship("Trace", back_populates="agent", cascade="all, delete-orphan")
    # evaluators = relationship("Evaluator", back_populates="agent", cascade="all, delete-orphan") 