from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.dependencies import get_project_service
from app.models.user import User
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithoutApiKey,
    ProjectWithMembers,
    UserProjectInfo,
    ApiKeyResponse,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/", response_model=List[UserProjectInfo])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Get all projects for the current user.
    """
    return await project_service.get_user_projects(current_user.id)


@router.get("/organization/{org_id}", response_model=List[ProjectWithoutApiKey])
async def get_organization_projects(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Get all projects for an organization (requires organization membership).
    """
    return await project_service.get_organization_projects(org_id, current_user.id)


@router.post("/", response_model=ProjectWithoutApiKey)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new project in an organization.
    """
    project = await project_service.create_project(project_data, current_user.id)
    
    # Commit the transaction
    db.commit()
    
    return project


@router.get("/{project_id}", response_model=ProjectWithMembers)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Get project details with members.
    """
    return await project_service.get_project_with_members(project_id, current_user.id)


@router.put("/{project_id}", response_model=ProjectWithoutApiKey)
async def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update project details.
    """
    project = await project_service.update_project(project_id, project_update, current_user.id)
    
    # Commit the transaction
    db.commit()
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a project.
    """
    result = await project_service.delete_project(project_id, current_user.id)
    
    # Commit the transaction
    db.commit()
    
    return result


@router.post("/{project_id}/regenerate-api-key", response_model=ApiKeyResponse)
async def regenerate_api_key(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    db: Session = Depends(get_db)
) -> Any:
    """
    Regenerate API key for a project.
    """
    new_api_key = await project_service.regenerate_api_key(project_id, current_user.id)
    
    # Commit the transaction
    db.commit()
    
    return ApiKeyResponse(api_key=new_api_key)


@router.get("/{project_id}/api-key", response_model=ApiKeyResponse)
async def get_project_api_key(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Get API key for a project.
    """
    api_key = await project_service.get_project_api_key(project_id, current_user.id)
    
    return ApiKeyResponse(
        api_key=api_key, message="API key retrieved successfully"
    )
