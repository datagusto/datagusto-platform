"""
Project service layer for business logic and orchestration.
Provides project management functionality following layered architecture.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectWithMembers, UserProjectInfo
from app.models.project import Project


class ProjectService:
    """Service layer for project operations with dependency injection."""
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        project_member_repo: ProjectMemberRepository,
        org_member_repo: OrganizationMemberRepository
    ):
        """
        Initialize service with repository dependencies.
        
        Args:
            project_repo: Project repository instance
            project_member_repo: Project member repository instance  
            org_member_repo: Organization member repository instance
        """
        self.project_repo = project_repo
        self.project_member_repo = project_member_repo
        self.org_member_repo = org_member_repo
    
    async def get_user_projects(self, user_id: uuid.UUID) -> List[UserProjectInfo]:
        """
        Get all projects for a user with their membership information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of projects with membership details
        """
        memberships = await self.project_member_repo.get_user_memberships(user_id)
        
        result = []
        for membership in memberships:
            result.append({"project": membership.project, "membership": membership})
        
        return result
    
    async def get_organization_projects(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Project]:
        """
        Get all projects for an organization.
        
        Args:
            org_id: Organization ID
            user_id: User ID requesting access
            
        Returns:
            List of projects in the organization
            
        Raises:
            HTTPException: If user doesn't have access to the organization
        """
        # Check organization access
        if not await self.org_member_repo.has_access(user_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization",
            )
        
        return await self.project_repo.get_projects_for_organization(org_id)
    
    async def create_project(
        self, project_data: ProjectCreate, creator_id: uuid.UUID
    ) -> Project:
        """
        Create a new project and assign creator as owner.
        
        Args:
            project_data: Project creation data
            creator_id: ID of the user creating the project
            
        Returns:
            Created project
            
        Raises:
            HTTPException: If user doesn't have permission to create projects
        """
        # Check organization permissions
        if not await self.org_member_repo.is_admin_or_owner(
            creator_id, project_data.organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner access required to create projects",
            )
        
        # Create project
        project_dict = project_data.model_dump()
        project_dict["id"] = uuid.uuid4()
        project = await self.project_repo.create_project(project_dict)
        
        # Add creator as owner
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": creator_id,
            "project_id": project.id,
            "role": "owner",
        }
        await self.project_member_repo.create_membership(membership_data)
        
        return project
    
    async def get_project_with_members(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectWithMembers:
        """
        Get project details including members.
        
        Args:
            project_id: Project ID
            user_id: User ID requesting access
            
        Returns:
            Project with member information
            
        Raises:
            HTTPException: If project not found or user lacks access
        """
        # Check project access
        if not await self.project_member_repo.has_access(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )
        
        project = await self.project_repo.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found"
            )
        
        # Get project members
        members = await self.project_member_repo.get_project_memberships(project_id)
        
        return ProjectWithMembers(**project.__dict__, members=members)
    
    async def update_project(
        self, project_id: uuid.UUID, project_update: ProjectUpdate, user_id: uuid.UUID
    ) -> Project:
        """
        Update project details.
        
        Args:
            project_id: Project ID to update
            project_update: Update data
            user_id: User ID making the update
            
        Returns:
            Updated project
            
        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Check edit permissions
        if not await self.project_member_repo.can_edit(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Edit access required"
            )
        
        # Filter out None values
        update_data = {
            k: v for k, v in project_update.model_dump().items() if v is not None
        }
        
        project = await self.project_repo.update_project(project_id, update_data)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found"
            )
        
        return project
    
    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, str]:
        """
        Delete a project.
        
        Args:
            project_id: Project ID to delete
            user_id: User ID requesting deletion
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If project not found or user isn't owner
        """
        # Check owner permissions
        if not await self.project_member_repo.is_owner(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner access required to delete project",
            )
        
        success = await self.project_repo.delete_project(project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found"
            )
        
        return {"message": "Project deleted successfully"}
    
    async def regenerate_api_key(self, project_id: uuid.UUID, user_id: uuid.UUID) -> str:
        """
        Regenerate API key for a project.
        
        Args:
            project_id: Project ID
            user_id: User ID requesting regeneration
            
        Returns:
            New API key
            
        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Check admin/owner permissions
        if not await self.project_member_repo.is_admin_or_owner(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner access required to regenerate API key",
            )
        
        new_api_key = await self.project_repo.regenerate_api_key(project_id)
        if not new_api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found"
            )
        
        return new_api_key
    
    async def get_project_api_key(self, project_id: uuid.UUID, user_id: uuid.UUID) -> str:
        """
        Get API key for a project.
        
        Args:
            project_id: Project ID
            user_id: User ID requesting API key
            
        Returns:
            Project API key
            
        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Check edit permissions to view API key
        if not await self.project_member_repo.can_edit(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Edit access required to view API key",
            )
        
        project = await self.project_repo.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Project not found"
            )
        
        return project.api_key