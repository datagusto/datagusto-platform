from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User as UserModel
from app.models.organization import Organization as OrganizationModel
from app.models.organization_member import OrganizationRole
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository


class OrganizationService:
    """Service for organization operations."""
    
    @staticmethod
    async def create_default_organization(user: UserModel, db: Session) -> OrganizationModel:
        """
        Create a default organization for a new user.
        
        Args:
            user: User model
            db: Database session
            
        Returns:
            Created organization
        """
        try:
            # Create organization with default name
            org_repo = OrganizationRepository(db)
            org_data = {
                "name": f"{user.name}'s Org",
                "settings": {},
                "billing_info": {}
            }
            organization = await org_repo.create_organization(org_data)
            
            # Add user as owner
            member_repo = OrganizationMemberRepository(db)
            member_data = {
                "user_id": user.id,
                "organization_id": organization.id,
                "role": OrganizationRole.OWNER
            }
            await member_repo.create_member(member_data)
            
            return organization
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create organization: {str(e)}"
            )
    
    @staticmethod
    async def get_user_organizations(user_id: str, db: Session) -> list[OrganizationModel]:
        """
        Get all organizations for a user.
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of organizations
        """
        try:
            org_repo = OrganizationRepository(db)
            return await org_repo.get_organizations_by_user_id(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get organizations: {str(e)}"
            )
    
    @staticmethod
    async def get_organization(organization_id: str, db: Session) -> OrganizationModel:
        """
        Get an organization by ID.
        
        Args:
            organization_id: Organization ID
            db: Database session
            
        Returns:
            Organization
        """
        try:
            org_repo = OrganizationRepository(db)
            organization = await org_repo.get_organization_by_id(organization_id)
            
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
                
            return organization
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get organization: {str(e)}"
            ) 