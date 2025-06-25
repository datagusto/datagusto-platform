"""
Organization service layer for business logic and orchestration.
Provides organization management functionality following layered architecture.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.schemas.organization import OrganizationUpdate, OrganizationWithMembers, UserOrganizationInfo
from app.models.organization import Organization


class OrganizationService:
    """Service layer for organization operations with dependency injection."""
    
    def __init__(
        self,
        org_repo: OrganizationRepository,
        org_member_repo: OrganizationMemberRepository
    ):
        """
        Initialize service with repository dependencies.
        
        Args:
            org_repo: Organization repository instance
            org_member_repo: Organization member repository instance
        """
        self.org_repo = org_repo
        self.org_member_repo = org_member_repo
    
    async def get_user_organizations(self, user_id: uuid.UUID) -> List[UserOrganizationInfo]:
        """
        Get all organizations for a user with their membership information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of organizations with membership details
        """
        memberships = await self.org_member_repo.get_user_memberships(user_id)
        
        result = []
        for membership in memberships:
            result.append({
                "organization": membership.organization,
                "membership": membership
            })
        
        return result
    
    async def get_organization_with_members(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationWithMembers:
        """
        Get organization details including members.
        
        Args:
            org_id: Organization ID
            user_id: User ID requesting access
            
        Returns:
            Organization with member information
            
        Raises:
            HTTPException: If organization not found or user lacks access
        """
        # Check organization access
        if not await self.org_member_repo.has_access(user_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        organization = await self.org_repo.get_organization_by_id(org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Get organization members
        members = await self.org_member_repo.get_organization_memberships(org_id)
        
        return OrganizationWithMembers(
            **organization.__dict__,
            members=members
        )
    
    async def update_organization(
        self, org_id: uuid.UUID, org_update: OrganizationUpdate, user_id: uuid.UUID
    ) -> Organization:
        """
        Update organization details.
        
        Args:
            org_id: Organization ID to update
            org_update: Update data
            user_id: User ID making the update
            
        Returns:
            Updated organization
            
        Raises:
            HTTPException: If organization not found or user lacks permission
        """
        # Check admin/owner permissions
        if not await self.org_member_repo.is_admin_or_owner(user_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner access required"
            )
        
        # Filter out None values
        update_data = {k: v for k, v in org_update.dict().items() if v is not None}
        
        organization = await self.org_repo.update_organization(org_id, update_data)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return organization