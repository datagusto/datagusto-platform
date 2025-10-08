"""
Project repository for database operations.

This repository handles operations for the Project model and its related
tables (owner, members, active status, archive).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.project import (
    Project,
    ProjectActiveStatus,
    ProjectArchive,
)
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for project database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Project)

    async def get_by_id_with_relations(self, project_id: UUID) -> Project | None:
        """
        Get project by ID with all related data.

        Args:
            project_id: Project UUID

        Returns:
            Project with related data or None if not found
        """
        stmt = (
            select(Project)
            .options(
                joinedload(Project.active_status),
                joinedload(Project.owner),
            )
            .where(Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        is_archived: bool | None = None,
    ) -> tuple[list[Project], int]:
        """
        Get projects by organization with pagination and filtering.

        Args:
            organization_id: Organization UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status (None = no filter)
            is_archived: Filter by archived status (None = no filter)

        Returns:
            Tuple of (projects list, total count)
        """
        # Base query
        stmt = select(Project).where(Project.organization_id == organization_id)

        # Apply filters
        if is_active is not None:
            if is_active:
                stmt = stmt.where(Project.active_status.has())
            else:
                stmt = stmt.where(~Project.active_status.has())

        if is_archived is not None:
            if is_archived:
                stmt = stmt.where(Project.archive.has())
            else:
                stmt = stmt.where(~Project.archive.has())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Project.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        return list(projects), total

    # Active Status Methods
    async def activate(self, project_id: UUID) -> ProjectActiveStatus:
        """
        Activate project (create active status record).

        Args:
            project_id: Project UUID

        Returns:
            Created ProjectActiveStatus

        Raises:
            IntegrityError: If project is already active
        """
        status = ProjectActiveStatus(project_id=project_id)
        self.db.add(status)
        await self.db.flush()
        return status

    async def deactivate(self, project_id: UUID) -> bool:
        """
        Deactivate project (delete active status record).

        Args:
            project_id: Project UUID

        Returns:
            True if deactivated, False if not found
        """
        stmt = select(ProjectActiveStatus).where(
            ProjectActiveStatus.project_id == project_id
        )
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        if not status:
            return False

        await self.db.delete(status)
        await self.db.flush()
        return True

    async def is_active(self, project_id: UUID) -> bool:
        """
        Check if project is active.

        Args:
            project_id: Project UUID

        Returns:
            True if project is active, False otherwise
        """
        stmt = select(ProjectActiveStatus).where(
            ProjectActiveStatus.project_id == project_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Archive Methods
    async def archive(
        self, project_id: UUID, archived_by: UUID, reason: str | None = None
    ) -> ProjectArchive:
        """
        Archive project (create archive record).

        Args:
            project_id: Project UUID
            archived_by: User UUID who archived the project
            reason: Optional reason for archiving

        Returns:
            Created ProjectArchive

        Raises:
            IntegrityError: If project is already archived
        """
        archive = ProjectArchive(
            project_id=project_id,
            archived_by=archived_by,
            reason=reason,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def unarchive(self, project_id: UUID) -> bool:
        """
        Unarchive project (delete archive record).

        Args:
            project_id: Project UUID

        Returns:
            True if unarchived, False if not found
        """
        stmt = select(ProjectArchive).where(ProjectArchive.project_id == project_id)
        result = await self.db.execute(stmt)
        archive = result.scalar_one_or_none()

        if not archive:
            return False

        await self.db.delete(archive)
        await self.db.flush()
        return True

    async def is_archived(self, project_id: UUID) -> bool:
        """
        Check if project is archived.

        Args:
            project_id: Project UUID

        Returns:
            True if project is archived, False otherwise
        """
        stmt = select(ProjectArchive).where(ProjectArchive.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
