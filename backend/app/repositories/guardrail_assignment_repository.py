"""
Guardrail assignment repository for database operations.

This repository handles operations for the GuardrailAgentAssignment model,
managing the N:M relationship between guardrails and agents.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from uuid import UUID

from app.models.guardrail import GuardrailAgentAssignment


class GuardrailAssignmentRepository:
    """Repository for guardrail-agent assignment database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_guardrail_id(
        self, guardrail_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[GuardrailAgentAssignment], int]:
        """
        Get assignments by guardrail ID with pagination.

        Args:
            guardrail_id: Guardrail UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (assignments list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(GuardrailAgentAssignment).where(
            GuardrailAgentAssignment.guardrail_id == guardrail_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Get paginated assignments
        stmt = (
            select(GuardrailAgentAssignment)
            .where(GuardrailAgentAssignment.guardrail_id == guardrail_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(GuardrailAgentAssignment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        assignments = result.scalars().all()

        return list(assignments), total

    async def get_by_agent_id(
        self, agent_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[GuardrailAgentAssignment], int]:
        """
        Get assignments by agent ID with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (assignments list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(GuardrailAgentAssignment).where(
            GuardrailAgentAssignment.agent_id == agent_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Get paginated assignments
        stmt = (
            select(GuardrailAgentAssignment)
            .where(GuardrailAgentAssignment.agent_id == agent_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(GuardrailAgentAssignment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        assignments = result.scalars().all()

        return list(assignments), total

    async def is_assigned(self, guardrail_id: UUID, agent_id: UUID) -> bool:
        """
        Check if guardrail is assigned to agent.

        Args:
            guardrail_id: Guardrail UUID
            agent_id: Agent UUID

        Returns:
            True if assigned, False otherwise
        """
        stmt = select(GuardrailAgentAssignment).where(
            GuardrailAgentAssignment.guardrail_id == guardrail_id,
            GuardrailAgentAssignment.agent_id == agent_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def assign(
        self, guardrail_id: UUID, agent_id: UUID, project_id: UUID, assigned_by: UUID
    ) -> GuardrailAgentAssignment:
        """
        Assign guardrail to agent.

        Args:
            guardrail_id: Guardrail UUID
            agent_id: Agent UUID
            project_id: Project UUID (denormalized for RLS)
            assigned_by: User UUID who made the assignment

        Returns:
            Created GuardrailAgentAssignment

        Raises:
            IntegrityError: If assignment already exists (unique constraint violation)
        """
        assignment = GuardrailAgentAssignment(
            guardrail_id=guardrail_id,
            agent_id=agent_id,
            project_id=project_id,
            assigned_by=assigned_by,
        )
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def unassign(self, guardrail_id: UUID, agent_id: UUID) -> bool:
        """
        Unassign guardrail from agent.

        Args:
            guardrail_id: Guardrail UUID
            agent_id: Agent UUID

        Returns:
            True if unassigned, False if not found
        """
        stmt = delete(GuardrailAgentAssignment).where(
            GuardrailAgentAssignment.guardrail_id == guardrail_id,
            GuardrailAgentAssignment.agent_id == agent_id,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_assigned_agents(self, guardrail_id: UUID) -> int:
        """
        Count agents assigned to a guardrail.

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            Number of assigned agents
        """
        stmt = select(func.count()).select_from(GuardrailAgentAssignment).where(
            GuardrailAgentAssignment.guardrail_id == guardrail_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()