from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.organization import Organization as OrganizationModel


class OrganizationRepository:
    """Repository for database organization operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_organization(self, organization_data: Dict[str, Any]) -> OrganizationModel:
        """
        Create a new organization in the database.
        
        Args:
            organization_data: Organization data
            
        Returns:
            Created organization
        """
        db_organization = OrganizationModel(**organization_data)
        self.db.add(db_organization)
        self.db.commit()
        self.db.refresh(db_organization)
        return db_organization
    
    async def get_organization_by_id(self, organization_id: str) -> Optional[OrganizationModel]:
        """
        Get an organization by ID.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Organization or None if not found
        """
        return self.db.query(OrganizationModel).filter(OrganizationModel.id == organization_id).first()
    
    async def get_organizations_by_user_id(self, user_id: str) -> List[OrganizationModel]:
        """
        Get all organizations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of organizations
        """
        from app.models.organization_member import OrganizationMember
        
        query = (
            self.db.query(OrganizationModel)
            .join(OrganizationMember, OrganizationModel.id == OrganizationMember.organization_id)
            .filter(OrganizationMember.user_id == user_id)
        )
        return query.all()
    
    async def update_organization(self, organization_id: str, organization_data: Dict[str, Any]) -> Optional[OrganizationModel]:
        """
        Update an organization.
        
        Args:
            organization_id: Organization ID
            organization_data: Organization data to update
            
        Returns:
            Updated organization or None if not found
        """
        organization = await self.get_organization_by_id(organization_id)
        if not organization:
            return None
        
        for key, value in organization_data.items():
            setattr(organization, key, value)
        
        self.db.commit()
        self.db.refresh(organization)
        return organization
    
    async def delete_organization(self, organization_id: str) -> bool:
        """
        Delete an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            True if deleted, False if not found
        """
        organization = await self.get_organization_by_id(organization_id)
        if not organization:
            return False
        
        self.db.delete(organization)
        self.db.commit()
        return True 