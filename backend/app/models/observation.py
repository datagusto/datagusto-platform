from sqlalchemy import Column, String, ForeignKey, Enum, Integer, Numeric
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ObservationType(str, enum.Enum):
    """Type of Observation."""
    LLM = "LLM"
    RETRIEVER = "RETRIEVER"
    TOOL = "TOOL"
    OTHER = "OTHER"


class Observation(Base):
    """SQLAlchemy Observation model.
    
    Represents the smallest unit of AI agent logs. Corresponds to individual processes
    like LLM calls or tool usage.
    """
    
    __tablename__ = "observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(ObservationType), nullable=False, index=True)
    name = Column(String, nullable=False)
    input = Column(JSONB, nullable=False)
    output = Column(JSONB, nullable=True)
    started_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tokens = Column(Integer, nullable=True)
    cost = Column(Numeric(precision=10, scale=4), nullable=True)
    observation_metadata = Column(JSONB, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("observations.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id = Column(String, nullable=True, index=True)
    
    # Relationships
    trace = relationship("Trace", back_populates="observations")
    parent = relationship("Observation", remote_side=[id], backref="children")
    # evaluation_results = relationship("EvaluationResult", 
    #                                  back_populates="observation", 
    #                                  primaryjoin="Observation.id==EvaluationResult.observation_id",
    #                                  cascade="all, delete-orphan") 