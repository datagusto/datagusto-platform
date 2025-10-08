"""
Guardrail repository for database operations.

This repository handles operations for the Guardrail model and its related
tables (assignments, active status, archive).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail import (
    Guardrail,
    GuardrailActiveStatus,
    GuardrailArchive,
)
from app.repositories.base_repository import BaseRepository


class GuardrailRepository(BaseRepository[Guardrail]):
    """Repository for guardrail database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Guardrail)

    async def get_by_project(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        is_archived: bool | None = None,
    ) -> tuple[list[Guardrail], int]:
        """
        Get guardrails by project with pagination and filtering.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status (None = no filter)
            is_archived: Filter by archived status (None = no filter)

        Returns:
            Tuple of (guardrails list, total count)
        """
        # Base query
        stmt = select(Guardrail).where(Guardrail.project_id == project_id)

        # Apply filters
        if is_active is not None:
            if is_active:
                stmt = stmt.where(Guardrail.active_status.has())
            else:
                stmt = stmt.where(~Guardrail.active_status.has())

        if is_archived is not None:
            if is_archived:
                stmt = stmt.where(Guardrail.archive.has())
            else:
                stmt = stmt.where(~Guardrail.archive.has())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Guardrail.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        guardrails = result.scalars().all()

        return list(guardrails), total

    # Active Status Methods
    async def activate(self, guardrail_id: UUID) -> GuardrailActiveStatus:
        """
        Activate guardrail (create active status record).

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            Created GuardrailActiveStatus

        Raises:
            IntegrityError: If guardrail is already active
        """
        status = GuardrailActiveStatus(guardrail_id=guardrail_id)
        self.db.add(status)
        await self.db.flush()
        return status

    async def deactivate(self, guardrail_id: UUID) -> bool:
        """
        Deactivate guardrail (delete active status record).

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            True if deactivated, False if not found
        """
        stmt = select(GuardrailActiveStatus).where(
            GuardrailActiveStatus.guardrail_id == guardrail_id
        )
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        if not status:
            return False

        await self.db.delete(status)
        await self.db.flush()
        return True

    async def is_active(self, guardrail_id: UUID) -> bool:
        """
        Check if guardrail is active.

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            True if guardrail is active, False otherwise
        """
        stmt = select(GuardrailActiveStatus).where(
            GuardrailActiveStatus.guardrail_id == guardrail_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Archive Methods
    async def archive(
        self, guardrail_id: UUID, archived_by: UUID, reason: str | None = None
    ) -> GuardrailArchive:
        """
        Archive guardrail (create archive record).

        Args:
            guardrail_id: Guardrail UUID
            archived_by: User UUID who archived the guardrail
            reason: Optional reason for archiving

        Returns:
            Created GuardrailArchive

        Raises:
            IntegrityError: If guardrail is already archived
        """
        archive = GuardrailArchive(
            guardrail_id=guardrail_id,
            archived_by=archived_by,
            reason=reason,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def is_archived(self, guardrail_id: UUID) -> bool:
        """
        Check if guardrail is archived.

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            True if guardrail is archived, False otherwise
        """
        stmt = select(GuardrailArchive).where(
            GuardrailArchive.guardrail_id == guardrail_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
