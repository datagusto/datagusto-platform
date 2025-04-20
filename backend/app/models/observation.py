from sqlalchemy import Column, String, ForeignKey, Enum, Integer, Numeric, Float
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class Observation(Base):
    """SQLAlchemy Observation model.
    
    Represents the smallest unit of AI agent logs. Corresponds to individual processes
    like LLM calls or tool usage.
    """
    
    __tablename__ = "observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True)

    # Langfuse fields
    observability_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    type = Column(String, nullable=True)
    parent_observation_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, nullable=True)
    start_time = Column(TIMESTAMP, nullable=True)
    end_time = Column(TIMESTAMP, nullable=True)
    input = Column(String, nullable=True)
    output = Column(String, nullable=True)
    
    model_parameters = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)

    usage_details = Column(JSONB, nullable=True)
    usage = Column(JSONB, nullable=True)
    cost_details = Column(JSONB, nullable=True)
    model = Column(String, nullable=True)
    latency = Column(Float, nullable=True)

    # observation_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    trace = relationship("Trace", back_populates="observations")
    # parent = relationship("Observation", remote_side=[id], backref="children")
    # evaluation_results = relationship("EvaluationResult", 
    #                                  back_populates="observation", 
    #                                  primaryjoin="Observation.id==EvaluationResult.observation_id",
    #                                  cascade="all, delete-orphan") 