from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
import uuid

from app.models.project_member import ProjectMember


class ProjectMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    async def create_membership(self, membership_data: dict) -> ProjectMember:
        """Create a new project membership."""
        membership = ProjectMember(**membership_data)
        self.db.add(membership)
        self.db.flush()  # Get ID without committing
        return membership

    async def get_membership(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[ProjectMember]:
        """Get membership for user in project."""
        stmt = select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[ProjectMember]:
        """Get all memberships for a user."""
        stmt = select(ProjectMember).where(ProjectMember.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def get_project_memberships(self, project_id: uuid.UUID) -> List[ProjectMember]:
        """Get all memberships for a project."""
        stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    async def update_membership_role(self, user_id: uuid.UUID, project_id: uuid.UUID, role: str) -> Optional[ProjectMember]:
        """Update membership role."""
        stmt = select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id
        )
        result = self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            membership.role = role
            self.db.flush()
        
        return membership

    async def delete_membership(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Delete project membership."""
        stmt = select(ProjectMember).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id == project_id
        )
        result = self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            self.db.delete(membership)
            return True
        
        return False
    
    def commit(self):
        """Commit the transaction."""
        self.db.commit()
    
    def rollback(self):
        """Rollback the transaction."""
        self.db.rollback()

    async def is_owner(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Check if user is owner of project."""
        membership = await self.get_membership(user_id, project_id)
        return membership is not None and membership.role == "owner"

    async def is_admin_or_owner(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Check if user is admin or owner of project."""
        membership = await self.get_membership(user_id, project_id)
        return membership is not None and membership.role in ["owner", "admin"]

    async def can_edit(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Check if user can edit project (owner, admin, member)."""
        membership = await self.get_membership(user_id, project_id)
        return membership is not None and membership.role in ["owner", "admin", "member"]

    async def has_access(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Check if user has any access to project."""
        membership = await self.get_membership(user_id, project_id)
        return membership is not None