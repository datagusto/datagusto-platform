"""
Agent repository for database operations.

This repository handles operations for the Agent model and its related
tables (API keys, active status, archive).
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.models.agent import (
    Agent,
    AgentActiveStatus,
    AgentArchive,
)
from app.repositories.base_repository import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """Repository for agent database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Agent)

    async def get_by_id_with_relations(
        self, agent_id: UUID
    ) -> Optional[Agent]:
        """
        Get agent by ID with all related data.

        Args:
            agent_id: Agent UUID

        Returns:
            Agent with related data or None if not found
        """
        stmt = (
            select(Agent)
            .options(
                joinedload(Agent.active_status),
            )
            .where(Agent.id == agent_id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> tuple[List[Agent], int]:
        """
        Get agents by project with pagination and filtering.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status (None = no filter)
            is_archived: Filter by archived status (None = no filter)

        Returns:
            Tuple of (agents list, total count)
        """
        # Base query
        stmt = select(Agent).where(Agent.project_id == project_id)

        # Apply filters
        if is_active is not None:
            if is_active:
                stmt = stmt.where(Agent.active_status.has())
            else:
                stmt = stmt.where(~Agent.active_status.has())

        if is_archived is not None:
            if is_archived:
                stmt = stmt.where(Agent.archive.has())
            else:
                stmt = stmt.where(~Agent.archive.has())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Agent.created_at.desc())

        # Execute query
        result = await self.db.execute(stmt)
        agents = result.scalars().all()

        return list(agents), total

    # Active Status Methods
    async def activate(self, agent_id: UUID) -> AgentActiveStatus:
        """
        Activate agent (create active status record).

        Args:
            agent_id: Agent UUID

        Returns:
            Created AgentActiveStatus

        Raises:
            IntegrityError: If agent is already active
        """
        status = AgentActiveStatus(agent_id=agent_id)
        self.db.add(status)
        await self.db.flush()
        return status

    async def deactivate(self, agent_id: UUID) -> bool:
        """
        Deactivate agent (delete active status record).

        Args:
            agent_id: Agent UUID

        Returns:
            True if deactivated, False if not found
        """
        stmt = select(AgentActiveStatus).where(
            AgentActiveStatus.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()

        if not status:
            return False

        await self.db.delete(status)
        await self.db.flush()
        return True

    async def is_active(self, agent_id: UUID) -> bool:
        """
        Check if agent is active.

        Args:
            agent_id: Agent UUID

        Returns:
            True if agent is active, False otherwise
        """
        stmt = select(AgentActiveStatus).where(
            AgentActiveStatus.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Archive Methods
    async def archive(
        self, agent_id: UUID, archived_by: UUID, reason: Optional[str] = None
    ) -> AgentArchive:
        """
        Archive agent (create archive record).

        Args:
            agent_id: Agent UUID
            archived_by: User UUID who archived the agent
            reason: Optional reason for archiving

        Returns:
            Created AgentArchive

        Raises:
            IntegrityError: If agent is already archived
        """
        archive = AgentArchive(
            agent_id=agent_id,
            archived_by=archived_by,
            reason=reason,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def unarchive(self, agent_id: UUID) -> bool:
        """
        Unarchive agent (delete archive record).

        Args:
            agent_id: Agent UUID

        Returns:
            True if unarchived, False if not found
        """
        stmt = select(AgentArchive).where(
            AgentArchive.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        archive = result.scalar_one_or_none()

        if not archive:
            return False

        await self.db.delete(archive)
        await self.db.flush()
        return True

    async def is_archived(self, agent_id: UUID) -> bool:
        """
        Check if agent is archived.

        Args:
            agent_id: Agent UUID

        Returns:
            True if agent is archived, False otherwise
        """
        stmt = select(AgentArchive).where(
            AgentArchive.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None