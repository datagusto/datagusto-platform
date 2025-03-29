from sqlalchemy import Column, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class OrganizationRole(str, enum.Enum):
    """Roles within an organization."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class OrganizationMember(Base):
    """SQLAlchemy OrganizationMember model."""
    
    __tablename__ = "organization_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER)
    joined_at = Column(TIMESTAMP, server_default=func.now())
    
    # Create a unique constraint on user_id and organization_id
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_org_member_user_org"),
    )
    
    # Relationships
    user = relationship("User", back_populates="organization_memberships")
    organization = relationship("Organization", back_populates="members") 