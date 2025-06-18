from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
import uuid
import secrets

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def _generate_api_key(self) -> str:
        """Generate a secure API key for the project."""
        return f"dg_{secrets.token_urlsafe(32)}"

    async def create_project(self, project_data: dict) -> Project:
        """Create a new project."""
        # Auto-generate API key if not provided
        if 'api_key' not in project_data:
            project_data['api_key'] = self._generate_api_key()
        
        project = Project(**project_data)
        self.db.add(project)
        self.db.flush()  # Get ID without committing
        return project

    async def get_project_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID."""
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_project_by_id_str(self, project_id: str) -> Optional[Project]:
        """Get project by ID string."""
        try:
            project_uuid = uuid.UUID(project_id)
            return await self.get_project_by_id(project_uuid)
        except (ValueError, TypeError):
            return None

    async def get_project_by_api_key(self, api_key: str) -> Optional[Project]:
        """Get project by API key."""
        stmt = select(Project).where(Project.api_key == api_key)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_projects_for_organization(self, org_id: uuid.UUID) -> List[Project]:
        """Get all projects for an organization."""
        stmt = select(Project).where(Project.organization_id == org_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def get_projects_for_user(self, user_id: uuid.UUID) -> List[Project]:
        """Get all projects for a user (through project memberships)."""
        stmt = (
            select(Project)
            .join(Project.members)
            .where(Project.members.any(user_id=user_id))
        )
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def update_project(self, project_id: uuid.UUID, update_data: dict) -> Optional[Project]:
        """Update project."""
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if project:
            for key, value in update_data.items():
                setattr(project, key, value)
            self.db.flush()
        
        return project

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        """Delete project."""
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if project:
            self.db.delete(project)
            return True
        
        return False

    async def regenerate_api_key(self, project_id: uuid.UUID) -> Optional[str]:
        """Regenerate API key for project."""
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if project:
            new_api_key = self._generate_api_key()
            project.api_key = new_api_key
            self.db.flush()
            return new_api_key
        
        return None
    
    # Synchronous methods for guardrails API
    def get_by_api_key(self, api_key: str) -> Optional[Project]:
        """Get project by API key (synchronous)."""
        stmt = select(Project).where(Project.api_key == api_key)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID if user has access (synchronous)."""
        stmt = (
            select(Project)
            .join(Project.members)
            .where(
                Project.id == project_id,
                Project.members.any(user_id=user_id)
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def commit(self):
        """Commit the transaction."""
        self.db.commit()
    
    def rollback(self):
        """Rollback the transaction."""
        self.db.rollback()