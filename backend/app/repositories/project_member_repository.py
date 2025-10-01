"""
Project member repository for database operations.

This repository handles operations for the ProjectMember model,
managing the N:M relationship between projects and users.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.models.project import ProjectMember


class ProjectMemberRepository:
    """Repository for project member database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_project_id(
        self, project_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[ProjectMember], int]:
        """
        Get project members by project ID with pagination.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (members list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(ProjectMember).where(
            ProjectMember.project_id == project_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Get paginated members
        stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(ProjectMember.created_at.desc())
        )
        result = await self.db.execute(stmt)
        members = result.scalars().all()

        return list(members), total

    async def get_by_user_id(self, user_id: UUID) -> List[ProjectMember]:
        """
        Get all project memberships for a user.

        Args:
            user_id: User UUID

        Returns:
            List of ProjectMember records
        """
        stmt = select(ProjectMember).where(ProjectMember.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_member(self, project_id: UUID, user_id: UUID) -> bool:
        """
        Check if user is a member of the project.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            True if user is member, False otherwise
        """
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        """
        Add user as project member.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            Created ProjectMember record

        Raises:
            IntegrityError: If user is already a member (unique constraint violation)
        """
        member = ProjectMember(project_id=project_id, user_id=user_id)
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        """
        Remove user from project members.

        Args:
            project_id: Project UUID
            user_id: User UUID

        Returns:
            True if removed, False if not found
        """
        stmt = delete(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_members(self, project_id: UUID) -> int:
        """
        Count total members in a project.

        Args:
            project_id: Project UUID

        Returns:
            Number of members
        """
        stmt = select(func.count()).select_from(ProjectMember).where(
            ProjectMember.project_id == project_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()