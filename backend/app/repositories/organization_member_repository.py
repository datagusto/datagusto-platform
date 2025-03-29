from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.organization_member import OrganizationMember as OrganizationMemberModel, OrganizationRole


class OrganizationMemberRepository:
    """Repository for database organization member operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_member(self, member_data: Dict[str, Any]) -> OrganizationMemberModel:
        """
        Create a new organization member in the database.
        
        Args:
            member_data: Member data
            
        Returns:
            Created member
        """
        db_member = OrganizationMemberModel(**member_data)
        self.db.add(db_member)
        self.db.commit()
        self.db.refresh(db_member)
        return db_member
    
    async def get_member(self, user_id: str, organization_id: str) -> Optional[OrganizationMemberModel]:
        """
        Get a member by user ID and organization ID.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            
        Returns:
            Member or None if not found
        """
        return self.db.query(OrganizationMemberModel).filter(
            OrganizationMemberModel.user_id == user_id,
            OrganizationMemberModel.organization_id == organization_id
        ).first()
    
    async def get_members_by_organization_id(self, organization_id: str) -> List[OrganizationMemberModel]:
        """
        Get all members of an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of members
        """
        return self.db.query(OrganizationMemberModel).filter(
            OrganizationMemberModel.organization_id == organization_id
        ).all()
    
    async def update_member_role(self, user_id: str, organization_id: str, role: OrganizationRole) -> Optional[OrganizationMemberModel]:
        """
        Update a member's role.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            role: New role
            
        Returns:
            Updated member or None if not found
        """
        member = await self.get_member(user_id, organization_id)
        if not member:
            return None
        
        member.role = role
        self.db.commit()
        self.db.refresh(member)
        return member
    
    async def delete_member(self, user_id: str, organization_id: str) -> bool:
        """
        Delete a member.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            
        Returns:
            True if deleted, False if not found
        """
        member = await self.get_member(user_id, organization_id)
        if not member:
            return False
        
        self.db.delete(member)
        self.db.commit()
        return True 