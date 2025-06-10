from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
import uuid

from app.models.organization_member import OrganizationMember


class OrganizationMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create_membership(self, membership_data: dict) -> OrganizationMember:
        """Create a new organization membership."""
        membership = OrganizationMember(**membership_data)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    async def get_membership(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Optional[OrganizationMember]:
        """Get membership for user in organization."""
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[OrganizationMember]:
        """Get all memberships for a user."""
        stmt = select(OrganizationMember).where(OrganizationMember.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def get_organization_memberships(self, org_id: uuid.UUID) -> List[OrganizationMember]:
        """Get all memberships for an organization."""
        stmt = select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def update_membership_role(self, user_id: uuid.UUID, org_id: uuid.UUID, role: str) -> Optional[OrganizationMember]:
        """Update membership role."""
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id
        )
        result = self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            membership.role = role
            self.db.commit()
            self.db.refresh(membership)
        
        return membership

    async def delete_membership(self, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Delete organization membership."""
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id
        )
        result = self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            self.db.delete(membership)
            self.db.commit()
            return True
        
        return False

    async def is_owner(self, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Check if user is owner of organization."""
        membership = await self.get_membership(user_id, org_id)
        return membership is not None and membership.role == "owner"

    async def is_admin_or_owner(self, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Check if user is admin or owner of organization."""
        membership = await self.get_membership(user_id, org_id)
        return membership is not None and membership.role in ["owner", "admin"]

    async def has_access(self, user_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Check if user has any access to organization."""
        membership = await self.get_membership(user_id, org_id)
        return membership is not None