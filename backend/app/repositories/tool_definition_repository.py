"""
Tool Definition repository for database operations.

This repository handles operations for ToolDefinition and ToolDefinitionRevision models,
including revision creation, history tracking, and linked list traversal.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_definition import ToolDefinition, ToolDefinitionRevision
from app.repositories.base_repository import BaseRepository


class ToolDefinitionRepository(BaseRepository[ToolDefinition]):
    """Repository for tool definition database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, ToolDefinition)

    async def get_by_agent_id(self, agent_id: UUID) -> ToolDefinition | None:
        """
        Get tool definition by agent ID.

        Args:
            agent_id: Agent UUID

        Returns:
            ToolDefinition or None if not found
        """
        stmt = select(ToolDefinition).where(ToolDefinition.agent_id == agent_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_by_agent(self, agent_id: UUID) -> ToolDefinition:
        """
        Get existing tool definition for agent or create a new one.

        Args:
            agent_id: Agent UUID

        Returns:
            ToolDefinition (existing or newly created)
        """
        # Try to get existing
        tool_def = await self.get_by_agent_id(agent_id)
        if tool_def:
            return tool_def

        # Create new if doesn't exist
        tool_def = ToolDefinition(
            agent_id=agent_id,
            latest_revision_id=None,  # Will be set when first revision is created
        )
        self.db.add(tool_def)
        await self.db.flush()
        return tool_def

    async def update_latest_revision_id(
        self, tool_definition_id: UUID, revision_id: UUID
    ) -> ToolDefinition | None:
        """
        Update the latest_revision_id for a tool definition.

        Args:
            tool_definition_id: ToolDefinition UUID
            revision_id: New latest revision UUID

        Returns:
            Updated ToolDefinition or None if not found
        """
        tool_def = await self.get_by_id(tool_definition_id)
        if not tool_def:
            return None

        tool_def.latest_revision_id = revision_id
        await self.db.flush()
        return tool_def


class ToolDefinitionRevisionRepository(BaseRepository[ToolDefinitionRevision]):
    """Repository for tool definition revision database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, ToolDefinitionRevision)

    async def create_revision(
        self,
        agent_id: UUID,
        tools_data: dict[str, Any],
        previous_revision_id: UUID | None,
    ) -> ToolDefinitionRevision:
        """
        Create a new tool definition revision.

        Args:
            agent_id: Agent UUID
            tools_data: JSONB containing tool definitions
            previous_revision_id: UUID of previous revision (None if first)

        Returns:
            Created ToolDefinitionRevision
        """
        revision = ToolDefinitionRevision(
            agent_id=agent_id,
            tools_data=tools_data,
            previous_revision_id=previous_revision_id,
        )
        self.db.add(revision)
        await self.db.flush()
        return revision

    async def get_by_agent_id(
        self, agent_id: UUID, limit: int = 10
    ) -> list[ToolDefinitionRevision]:
        """
        Get revisions for an agent ordered by creation time (newest first).

        Args:
            agent_id: Agent UUID
            limit: Maximum number of revisions to return

        Returns:
            List of ToolDefinitionRevision
        """
        stmt = (
            select(ToolDefinitionRevision)
            .where(ToolDefinitionRevision.agent_id == agent_id)
            .order_by(ToolDefinitionRevision.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_revision_history(
        self, revision_id: UUID, limit: int = 100
    ) -> list[ToolDefinitionRevision]:
        """
        Get full revision history by traversing the linked list.

        Starts from the given revision and follows previous_revision_id links
        to build the complete history chain.

        Args:
            revision_id: Starting revision UUID (typically the latest)
            limit: Maximum number of revisions to traverse

        Returns:
            List of ToolDefinitionRevision in chronological order (newest first)

        Note:
            This traverses the revision chain in application code rather than
            using a recursive CTE. For large histories, consider implementing
            a CTE-based version for better performance.
        """
        history = []
        current_id = revision_id
        count = 0

        while current_id and count < limit:
            # Get current revision
            revision = await self.get_by_id(current_id)
            if not revision:
                break

            history.append(revision)
            current_id = revision.previous_revision_id
            count += 1

        return history


__all__ = ["ToolDefinitionRepository", "ToolDefinitionRevisionRepository"]
