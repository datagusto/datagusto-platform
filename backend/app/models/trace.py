from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer, Numeric
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
    user_query = Column(Text, nullable=False)
    final_response = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
    status = Column(Enum(TraceStatus), nullable=False, default=TraceStatus.IN_PROGRESS)
    trace_metadata = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost = Column(Numeric(precision=10, scale=4), nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="traces")
    observations = relationship("Observation", back_populates="trace", cascade="all, delete-orphan")
    # evaluation_results = relationship("EvaluationResult", 
    #                                  back_populates="trace", 
    #                                  primaryjoin="Trace.id==EvaluationResult.trace_id",
    #                                  cascade="all, delete-orphan") 