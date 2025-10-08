"""
Guardrail Evaluation Log repository for database operations.

This repository handles CRUD operations for the GuardrailEvaluationLog model.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail_evaluation_log import GuardrailEvaluationLog
from app.repositories.base_repository import BaseRepository


class GuardrailEvaluationLogRepository(BaseRepository[GuardrailEvaluationLog]):
    """Repository for guardrail evaluation log database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, GuardrailEvaluationLog)

    async def get_by_request_id(self, request_id: str) -> GuardrailEvaluationLog | None:
        """
        Get evaluation log by request ID.

        Args:
            request_id: Unique request ID

        Returns:
            Evaluation log if found, None otherwise

        Example:
            >>> log = await repo.get_by_request_id("req_abc123")
            >>> print(log.should_proceed)
        """
        stmt = select(GuardrailEvaluationLog).where(
            GuardrailEvaluationLog.request_id == request_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GuardrailEvaluationLog], int]:
        """
        List evaluation logs by agent with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs list, total count)

        Example:
            >>> logs, total = await repo.list_by_agent(agent_id, page=1, page_size=10)
            >>> print(f"Found {total} logs, showing {len(logs)}")
        """
        # Base query
        stmt = select(GuardrailEvaluationLog).where(
            GuardrailEvaluationLog.agent_id == agent_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(GuardrailEvaluationLog.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total

    async def list_by_project(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GuardrailEvaluationLog], int]:
        """
        List evaluation logs by project with pagination.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs list, total count)

        Example:
            >>> logs, total = await repo.list_by_project(project_id, page=1, page_size=20)
        """
        # Base query
        stmt = select(GuardrailEvaluationLog).where(
            GuardrailEvaluationLog.project_id == project_id
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(GuardrailEvaluationLog.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total


__all__ = ["GuardrailEvaluationLogRepository"]
