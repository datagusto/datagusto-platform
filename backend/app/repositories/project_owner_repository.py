"""
Project owner repository for database operations.

This repository handles operations for the ProjectOwner model,
managing the 1:1 relationship between projects and their owners.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID

from app.models.project import ProjectOwner


class ProjectOwnerRepository:
    """Repository for project owner database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_project_id(self, project_id: UUID) -> Optional[ProjectOwner]:
        """
        Get project owner by project ID.

        Args:
            project_id: Project UUID

        Returns:
            ProjectOwner or None if not found
        """
        stmt = select(ProjectOwner).where(ProjectOwner.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_owner(self, project_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is the owner of the project.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            True if user is owner, False otherwise
        """
        stmt = select(ProjectOwner).where(
            ProjectOwner.project_id == project_id,
            ProjectOwner.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def set_owner(self, project_id: UUID, user_id: UUID) -> ProjectOwner:
        """
        Set project owner (replaces existing owner if any).

        This method ensures there is only one owner per project by
        deleting any existing owner record before creating a new one.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            Created ProjectOwner record

        Note:
            - Automatically deletes existing owner if present
            - Creates new owner record
            - Uses flush() to ensure changes are visible in same transaction
        """
        # Delete existing owner if any
        delete_stmt = delete(ProjectOwner).where(
            ProjectOwner.project_id == project_id
        )
        await self.db.execute(delete_stmt)
        await self.db.flush()

        # Create new owner
        owner = ProjectOwner(project_id=project_id, user_id=user_id)
        self.db.add(owner)
        await self.db.flush()
        return owner

    async def delete_owner(self, project_id: UUID) -> bool:
        """
        Delete project owner record.

        Args:
            project_id: Project UUID

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(ProjectOwner).where(ProjectOwner.project_id == project_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0