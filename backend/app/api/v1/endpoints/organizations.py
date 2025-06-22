from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import get_organization_service
from app.models.user import User
from app.schemas.organization import (
    Organization, 
    OrganizationCreate, 
    OrganizationUpdate,
    OrganizationWithMembers,
    UserOrganizationInfo
)
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.get("/", response_model=List[UserOrganizationInfo])
async def get_user_organizations(
    current_user: User = Depends(get_current_user),
    org_service: OrganizationService = Depends(get_organization_service)
) -> Any:
    """
    Get all organizations for the current user.
    """
    return await org_service.get_user_organizations(current_user.id)


@router.get("/{org_id}", response_model=OrganizationWithMembers)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    org_service: OrganizationService = Depends(get_organization_service)
) -> Any:
    """
    Get organization details with members.
    """
    return await org_service.get_organization_with_members(org_id, current_user.id)


@router.put("/{org_id}", response_model=Organization)
async def update_organization(
    org_id: uuid.UUID,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    org_service: OrganizationService = Depends(get_organization_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update organization details.
    """
    organization = await org_service.update_organization(org_id, org_update, current_user.id)
    
    # Commit the transaction
    db.commit()
    
    return organization