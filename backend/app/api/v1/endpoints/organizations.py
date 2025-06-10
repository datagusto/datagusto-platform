from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.organization import (
    Organization, 
    OrganizationCreate, 
    OrganizationUpdate,
    OrganizationWithMembers,
    UserOrganizationInfo
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get("/", response_model=List[UserOrganizationInfo])
async def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all organizations for the current user.
    """
    org_member_repo = OrganizationMemberRepository(db)
    memberships = await org_member_repo.get_user_memberships(current_user.id)
    
    result = []
    for membership in memberships:
        result.append({
            "organization": membership.organization,
            "membership": membership
        })
    
    return result


@router.get("/{org_id}", response_model=OrganizationWithMembers)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get organization details with members.
    """
    org_member_repo = OrganizationMemberRepository(db)
    
    # Check if user has access to this organization
    if not await org_member_repo.has_access(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    org_repo = OrganizationRepository(db)
    organization = await org_repo.get_organization_by_id(org_id)
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get members
    members = await org_member_repo.get_organization_memberships(org_id)
    
    return OrganizationWithMembers(
        **organization.__dict__,
        members=members
    )


@router.put("/{org_id}", response_model=Organization)
async def update_organization(
    org_id: uuid.UUID,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update organization details.
    """
    org_member_repo = OrganizationMemberRepository(db)
    
    # Check if user is admin or owner
    if not await org_member_repo.is_admin_or_owner(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner access required"
        )
    
    org_repo = OrganizationRepository(db)
    
    # Filter out None values
    update_data = {k: v for k, v in org_update.dict().items() if v is not None}
    
    organization = await org_repo.update_organization(org_id, update_data)
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization