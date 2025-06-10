from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
import uuid

from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create_organization(self, org_data: dict) -> Organization:
        """Create a new organization."""
        organization = Organization(**org_data)
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)
        return organization

    async def get_organization_by_id(self, org_id: uuid.UUID) -> Optional[Organization]:
        """Get organization by ID."""
        stmt = select(Organization).where(Organization.id == org_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        stmt = select(Organization).where(Organization.slug == slug)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_organizations_for_user(self, user_id: uuid.UUID) -> List[Organization]:
        """Get all organizations for a user."""
        stmt = (
            select(Organization)
            .join(Organization.members)
            .where(Organization.members.any(user_id=user_id))
            .where(Organization.is_active == True)
        )
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def update_organization(self, org_id: uuid.UUID, update_data: dict) -> Optional[Organization]:
        """Update organization."""
        stmt = select(Organization).where(Organization.id == org_id)
        result = self.db.execute(stmt)
        organization = result.scalar_one_or_none()
        
        if organization:
            for key, value in update_data.items():
                setattr(organization, key, value)
            self.db.commit()
            self.db.refresh(organization)
        
        return organization

    async def delete_organization(self, org_id: uuid.UUID) -> bool:
        """Soft delete organization by setting is_active to False."""
        stmt = select(Organization).where(Organization.id == org_id)
        result = self.db.execute(stmt)
        organization = result.scalar_one_or_none()
        
        if organization:
            organization.is_active = False
            self.db.commit()
            return True
        
        return False