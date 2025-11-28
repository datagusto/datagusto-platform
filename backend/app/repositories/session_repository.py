"""
Session repository for database operations.

This repository handles operations for the Session model.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.session import Session
from app.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for session database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Session)

    async def get_by_id_with_latest_alignment(
        self, session_id: UUID
    ) -> Session | None:
        """
        Get session by ID with latest alignment history eagerly loaded.

        Args:
            session_id: Session UUID

        Returns:
            Session with latest alignment or None if not found

        Note:
            - Eagerly loads alignment_history relationship
            - alignment_history is ordered by created_at DESC in model definition
        """
        stmt = (
            select(Session)
            .options(
                joinedload(Session.alignment_history),
            )
            .where(Session.id == session_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Session], int]:
        """
        Get sessions by agent with pagination and filtering.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status (None = no filter)

        Returns:
            Tuple of (sessions list, total count)
        """
        # Base query
        stmt = select(Session).where(Session.agent_id == agent_id)

        # Apply status filter
        if status is not None:
            stmt = stmt.where(Session.status == status)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Session.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return list(sessions), total

    async def get_by_project(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Session], int]:
        """
        Get sessions by project with pagination and filtering.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status (None = no filter)

        Returns:
            Tuple of (sessions list, total count)
        """
        # Base query
        stmt = select(Session).where(Session.project_id == project_id)

        # Apply status filter
        if status is not None:
            stmt = stmt.where(Session.status == status)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Session.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return list(sessions), total

    async def get_active_by_agent(self, agent_id: UUID) -> list[Session]:
        """
        Get all active sessions for an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            List of active sessions
        """
        stmt = (
            select(Session)
            .where(
                Session.agent_id == agent_id,
                Session.status == "active",
            )
            .order_by(Session.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, session_id: UUID, status: str) -> Session | None:
        """
        Update session status.

        Args:
            session_id: Session UUID
            status: New status value

        Returns:
            Updated session or None if not found
        """
        return await self.update_by_id(session_id, {"status": status})

    async def complete_session(self, session_id: UUID) -> Session | None:
        """
        Mark session as completed.

        Args:
            session_id: Session UUID

        Returns:
            Updated session or None if not found
        """
        return await self.update_status(session_id, "completed")

    async def expire_session(self, session_id: UUID) -> Session | None:
        """
        Mark session as expired.

        Args:
            session_id: Session UUID

        Returns:
            Updated session or None if not found
        """
        return await self.update_status(session_id, "expired")


__all__ = ["SessionRepository"]
