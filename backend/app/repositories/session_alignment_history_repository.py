"""
Session alignment history repository for database operations.

This repository handles operations for the SessionAlignmentHistory model.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import SessionAlignmentHistory
from app.repositories.base_repository import BaseRepository


class SessionAlignmentHistoryRepository(BaseRepository[SessionAlignmentHistory]):
    """Repository for session alignment history database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, SessionAlignmentHistory)

    async def get_latest_by_session(
        self, session_id: UUID
    ) -> SessionAlignmentHistory | None:
        """
        Get the latest alignment result for a session.

        Args:
            session_id: Session UUID

        Returns:
            Latest alignment history record or None if not found

        Note:
            - Orders by created_at DESC and takes first result
            - This represents the current alignment state
        """
        stmt = (
            select(SessionAlignmentHistory)
            .where(SessionAlignmentHistory.session_id == session_id)
            .order_by(SessionAlignmentHistory.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_session_and_agent(
        self, session_id: UUID, agent_id: UUID
    ) -> SessionAlignmentHistory | None:
        """
        Get the latest alignment result for a session and agent.

        Args:
            session_id: Session UUID
            agent_id: Agent UUID

        Returns:
            Latest alignment history record or None if not found
        """
        stmt = (
            select(SessionAlignmentHistory)
            .where(
                SessionAlignmentHistory.session_id == session_id,
                SessionAlignmentHistory.agent_id == agent_id,
            )
            .order_by(SessionAlignmentHistory.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        session_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SessionAlignmentHistory], int]:
        """
        Get alignment history for a session with pagination.

        Args:
            session_id: Session UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (alignment history list, total count)

        Note:
            - Results are ordered by created_at DESC (most recent first)
        """
        # Base query
        stmt = select(SessionAlignmentHistory).where(
            SessionAlignmentHistory.session_id == session_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(SessionAlignmentHistory.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        history = result.scalars().all()

        return list(history), total

    async def get_by_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SessionAlignmentHistory], int]:
        """
        Get alignment history for an agent with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (alignment history list, total count)

        Note:
            - Results are ordered by created_at DESC (most recent first)
        """
        # Base query
        stmt = select(SessionAlignmentHistory).where(
            SessionAlignmentHistory.agent_id == agent_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(SessionAlignmentHistory.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        history = result.scalars().all()

        return list(history), total

    async def count_by_session(self, session_id: UUID) -> int:
        """
        Count alignment records for a session.

        Args:
            session_id: Session UUID

        Returns:
            Count of alignment records
        """
        stmt = select(func.count()).where(
            SessionAlignmentHistory.session_id == session_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()


__all__ = ["SessionAlignmentHistoryRepository"]
