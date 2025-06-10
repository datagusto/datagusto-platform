from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class OrganizationMember(Base):
    """SQLAlchemy OrganizationMember model."""
    
    __tablename__ = "organization_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    role = Column(String, default="member")  # owner, admin, member
    invited_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    joined_at = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'organization_id'),)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_memberships")
    organization = relationship("Organization", back_populates="members")
    inviter = relationship("User", foreign_keys=[invited_by])