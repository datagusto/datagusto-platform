"""
Trace repository for database operations.

This repository handles operations for the Trace model, including
CRUD operations, filtering, and archive management.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID

from app.models.trace import Trace, TraceArchive
from app.repositories.base_repository import BaseRepository


class TraceRepository(BaseRepository[Trace]):
    """Repository for trace database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Trace)

    async def get_by_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[Trace], int]:
        """
        Get traces by agent with pagination and filtering.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status (pending, running, completed, failed, error)
            start_date: Filter traces started after this date
            end_date: Filter traces started before this date

        Returns:
            Tuple of (traces list, total count)
        """
        # Base query
        stmt = select(Trace).where(Trace.agent_id == agent_id)

        # Apply filters
        if status:
            stmt = stmt.where(Trace.status == status)
        if start_date:
            stmt = stmt.where(Trace.started_at >= start_date)
        if end_date:
            stmt = stmt.where(Trace.started_at <= end_date)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Trace.started_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        traces = result.scalars().all()

        return list(traces), total

    async def get_observation_count(self, trace_id: UUID) -> int:
        """
        Count observations in a trace.

        Args:
            trace_id: Trace UUID

        Returns:
            Number of observations
        """
        from app.models.trace import Observation

        stmt = select(func.count()).select_from(Observation).where(
            Observation.trace_id == trace_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def calculate_duration(self, trace_id: UUID) -> Optional[float]:
        """
        Calculate trace duration in seconds.

        Args:
            trace_id: Trace UUID

        Returns:
            Duration in seconds, None if trace is still running (ended_at is NULL)
        """
        trace = await self.get_by_id(trace_id)
        if not trace or not trace.ended_at:
            return None

        delta = trace.ended_at - trace.started_at
        return delta.total_seconds()

    async def archive(
        self, trace_id: UUID, archived_by: Optional[UUID], reason: str
    ) -> TraceArchive:
        """
        Archive trace (create archive record).

        Args:
            trace_id: Trace UUID
            archived_by: User UUID who archived the trace (None for automated)
            reason: Reason for archiving

        Returns:
            Created TraceArchive

        Raises:
            IntegrityError: If trace is already archived
        """
        archive = TraceArchive(
            trace_id=trace_id,
            archived_by=archived_by,
            reason=reason,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def is_archived(self, trace_id: UUID) -> bool:
        """
        Check if trace is archived.

        Args:
            trace_id: Trace UUID

        Returns:
            True if trace is archived, False otherwise
        """
        stmt = select(TraceArchive).where(TraceArchive.trace_id == trace_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
