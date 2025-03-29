from sqlalchemy import Column, String, Text
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Organization(Base):
    """SQLAlchemy Organization model."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    settings = Column(JSONB, nullable=True)
    billing_info = Column(JSONB, nullable=True)
    
    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="organization", cascade="all, delete-orphan") 