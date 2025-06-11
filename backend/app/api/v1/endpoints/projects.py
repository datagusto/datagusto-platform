from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithoutApiKey,
    ProjectWithMembers,
    UserProjectInfo,
    ApiKeyResponse
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository

router = APIRouter()


@router.get("/", response_model=List[UserProjectInfo])
async def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all projects for the current user.
    """
    project_member_repo = ProjectMemberRepository(db)
    memberships = await project_member_repo.get_user_memberships(current_user.id)
    
    result = []
    for membership in memberships:
        result.append({
            "project": membership.project,
            "membership": membership
        })
    
    return result


@router.get("/organization/{org_id}", response_model=List[ProjectWithoutApiKey])
async def get_organization_projects(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all projects for an organization (requires organization membership).
    """
    org_member_repo = OrganizationMemberRepository(db)
    
    # Check if user has access to this organization
    if not await org_member_repo.has_access(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    project_repo = ProjectRepository(db)
    projects = await project_repo.get_projects_for_organization(org_id)
    
    return projects


@router.post("/", response_model=ProjectWithoutApiKey)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new project in an organization.
    """
    org_member_repo = OrganizationMemberRepository(db)
    
    # Check if user can create projects in this organization (admin or owner)
    if not await org_member_repo.is_admin_or_owner(current_user.id, project_data.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner access required to create projects"
        )
    
    project_repo = ProjectRepository(db)
    project_member_repo = ProjectMemberRepository(db)
    
    # Create project
    project_dict = project_data.model_dump()
    project_dict["id"] = uuid.uuid4()
    project = await project_repo.create_project(project_dict)
    
    # Add creator as owner
    membership_data = {
        "id": uuid.uuid4(),
        "user_id": current_user.id,
        "project_id": project.id,
        "role": "owner"
    }
    await project_member_repo.create_membership(membership_data)
    
    return project


@router.get("/{project_id}", response_model=ProjectWithMembers)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get project details with members.
    """
    project_member_repo = ProjectMemberRepository(db)
    
    # Check if user has access to this project
    if not await project_member_repo.has_access(current_user.id, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    project_repo = ProjectRepository(db)
    project = await project_repo.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get members
    members = await project_member_repo.get_project_memberships(project_id)
    
    return ProjectWithMembers(
        **project.__dict__,
        members=members
    )


@router.put("/{project_id}", response_model=ProjectWithoutApiKey)
async def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update project details.
    """
    project_member_repo = ProjectMemberRepository(db)
    
    # Check if user can edit project (owner, admin, member)
    if not await project_member_repo.can_edit(current_user.id, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required"
        )
    
    project_repo = ProjectRepository(db)
    
    # Filter out None values
    update_data = {k: v for k, v in project_update.model_dump().items() if v is not None}
    
    project = await project_repo.update_project(project_id, update_data)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a project.
    """
    project_member_repo = ProjectMemberRepository(db)
    
    # Check if user is owner
    if not await project_member_repo.is_owner(current_user.id, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required to delete project"
        )
    
    project_repo = ProjectRepository(db)
    
    success = await project_repo.delete_project(project_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/regenerate-api-key", response_model=ApiKeyResponse)
async def regenerate_api_key(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Regenerate API key for a project.
    """
    project_member_repo = ProjectMemberRepository(db)
    
    # Check if user is owner or admin
    if not await project_member_repo.is_admin_or_owner(current_user.id, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner access required to regenerate API key"
        )
    
    project_repo = ProjectRepository(db)
    
    new_api_key = await project_repo.regenerate_api_key(project_id)
    
    if not new_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ApiKeyResponse(api_key=new_api_key)


@router.get("/{project_id}/api-key", response_model=ApiKeyResponse)
async def get_project_api_key(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get API key for a project.
    """
    project_member_repo = ProjectMemberRepository(db)
    
    # Check if user can edit project (to view API key)
    if not await project_member_repo.can_edit(current_user.id, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required to view API key"
        )
    
    project_repo = ProjectRepository(db)
    project = await project_repo.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ApiKeyResponse(
        api_key=project.api_key,
        message="API key retrieved successfully"
    )