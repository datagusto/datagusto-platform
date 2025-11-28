"""
Session Validation Log repository for database operations.

This repository handles CRUD operations for the SessionValidationLog model.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_validation_log import SessionValidationLog
from app.repositories.base_repository import BaseRepository


class SessionValidationLogRepository(BaseRepository[SessionValidationLog]):
    """Repository for session validation log database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, SessionValidationLog)

    async def list_by_session(
        self,
        session_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SessionValidationLog], int]:
        """
        List validation logs by session with pagination.

        Args:
            session_id: Session UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs list, total count)

        Example:
            >>> logs, total = await repo.list_by_session(session_id, page=1, page_size=10)
            >>> print(f"Found {total} logs, showing {len(logs)}")
        """
        # Base query
        stmt = select(SessionValidationLog).where(
            SessionValidationLog.session_id == session_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(SessionValidationLog.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total

    async def list_by_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SessionValidationLog], int]:
        """
        List validation logs by agent with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs list, total count)

        Example:
            >>> logs, total = await repo.list_by_agent(agent_id, page=1, page_size=20)
        """
        # Base query
        stmt = select(SessionValidationLog).where(
            SessionValidationLog.agent_id == agent_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(SessionValidationLog.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total


__all__ = ["SessionValidationLogRepository"]
