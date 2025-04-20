from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer, Numeric, Float
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class TraceStatus(str, enum.Enum):
    """Status of a Trace."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class Trace(Base):
    """SQLAlchemy Trace model.
    
    Represents a complete interaction from receiving a user's instruction to returning the output.
    """
    
    __tablename__ = "traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Langfuse fields
    observability_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    name = Column(String, nullable=True)
    timestamp = Column(TIMESTAMP, nullable=True)
    input = Column(String, nullable=True)
    output = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    latency = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True, default=0.0)

    # Evaluation
    evaluation_results = Column(JSONB, nullable=True)

    status = Column(Enum(TraceStatus), nullable=False, default=TraceStatus.IN_PROGRESS)
    trace_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="traces")
    observations = relationship("Observation", back_populates="trace", cascade="all, delete-orphan")
