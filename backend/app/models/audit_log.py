from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AuditLog(Base):
    """SQLAlchemy AuditLog model for tracking SDK audit events."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    audit_type = Column(String, nullable=False)  # "guardrail_execution", etc.
    data = Column(JSON, nullable=False)  # audit type specific data
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="audit_logs")