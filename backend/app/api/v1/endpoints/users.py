from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate
from app.services.user_service import UserService
from app.schemas.agent import Agent
from app.services.agent_service import AgentService
from app.schemas.organization import Organization
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.get("/me", response_model=User)
async def read_current_user(current_user: UserModel = Depends(get_current_active_user)) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Update current user details.
    """
    return await UserService.update_user(current_user, user_in, db)


@router.get("/me/organizations", response_model=List[Organization])
async def read_current_user_organizations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get all organizations the current user belongs to.
    """
    organizations = await OrganizationService.get_user_organizations(
        user_id=current_user.id,
        db=db
    )
    return organizations


@router.get("/me/agents", response_model=List[Agent])
async def read_current_user_agents(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get all agents created by the current user.
    """
    agents = await AgentService.get_agents_by_creator(
        user_id=current_user.id,
        db=db
    )
    return agents
