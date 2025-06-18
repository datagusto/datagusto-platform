from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Trace(Base):
    """
    Abstract trace model for universal observability platform support.
    All platform-specific data is stored in raw_data JSON field.
    """
    __tablename__ = "traces"
    
    # Core identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    
    # Platform identification
    external_id = Column(String, nullable=False, index=True)  # ID from external platform
    platform_type = Column(String, nullable=False, index=True)  # langfuse, langsmith, wandb, etc.
    
    # Minimal common fields for indexing/searching
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)  # When trace occurred
    
    # Platform-agnostic data storage
    raw_data = Column(JSON, nullable=False)  # Complete platform response
    
    # datagusto-specific fields
    quality_score = Column(Float)  # Data quality analysis result
    quality_issues = Column(JSON)  # Identified data quality problems
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="traces")
    observations = relationship("Observation", back_populates="trace", cascade="all, delete-orphan")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_trace_project_timestamp', 'project_id', 'timestamp'),
        Index('idx_trace_external_platform', 'project_id', 'external_id', 'platform_type', unique=True),
        Index('idx_trace_platform_type', 'platform_type'),
        Index('idx_trace_quality_score', 'project_id', 'quality_score'),
    )


class Observation(Base):
    """
    Abstract observation model for universal observability platform support.
    All platform-specific data is stored in raw_data JSON field.
    """
    __tablename__ = "observations"
    
    # Core identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey('traces.id'), nullable=False, index=True)
    parent_observation_id = Column(UUID(as_uuid=True), ForeignKey('observations.id'), nullable=True)
    
    # Platform identification
    external_id = Column(String, nullable=False, index=True)  # ID from external platform
    platform_type = Column(String, nullable=False, index=True)  # langfuse, langsmith, wandb, etc.
    
    # Minimal common fields for indexing/searching
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)  # When observation started
    
    # Platform-agnostic data storage
    raw_data = Column(JSON, nullable=False)  # Complete platform response
    
    # System timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    trace = relationship("Trace", back_populates="observations")
    parent_observation = relationship("Observation", remote_side=[id])
    child_observations = relationship("Observation", back_populates="parent_observation")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_observation_trace_start', 'trace_id', 'start_time'),
        Index('idx_observation_external_platform', 'trace_id', 'external_id', 'platform_type', unique=True),
        Index('idx_observation_platform_type', 'platform_type'),
        Index('idx_observation_parent', 'parent_observation_id'),
    )