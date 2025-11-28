"""
Tool Definition service for managing tool registration operations.

This service handles tool definition registration, revision creation,
and history management for AI agents.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tool_definition_repository import (
    ToolDefinitionRepository,
    ToolDefinitionRevisionRepository,
)
from app.schemas.tool_definition import (
    ToolRegistrationRequest,
    ToolRegistrationResponse,
)

logger = logging.getLogger(__name__)


class ToolDefinitionService:
    """Service for handling tool definition operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the tool definition service.

        Args:
            db: Async database session
        """
        self.db = db
        self.tool_def_repo = ToolDefinitionRepository(db)
        self.revision_repo = ToolDefinitionRevisionRepository(db)

    async def register_tools(
        self,
        agent_id: UUID,
        request: ToolRegistrationRequest,
    ) -> ToolRegistrationResponse:
        """
        Register tool definitions for an agent.

        Creates a new revision of tool definitions while preserving full history.
        If this is the first registration, creates a new ToolDefinition record.
        Otherwise, creates a new revision linked to the previous one.

        Args:
            agent_id: Agent UUID (from API key authentication)
            request: Tool registration request with tools list

        Returns:
            ToolRegistrationResponse with revision information

        Raises:
            Exception: If database operation fails

        Example:
            >>> request = ToolRegistrationRequest(
            ...     tools=[
            ...         {"name": "get_weather", "description": "...", ...},
            ...         {"name": "search", "description": "...", ...}
            ...     ]
            ... )
            >>> response = await service.register_tools(
            ...     agent_id=agent_uuid,
            ...     request=request
            ... )
            >>> print(response.revision_id)  # New revision UUID
            >>> print(response.tools_count)  # 2
        """
        try:
            # Step 1: Get or create ToolDefinition for this agent
            tool_definition = await self.tool_def_repo.get_or_create_by_agent(
                agent_id=agent_id
            )

            # Step 2: Get current latest revision ID (will be the previous revision)
            previous_revision_id = tool_definition.latest_revision_id

            # Step 3: Create new revision with tools data
            # Store tools as-is without validation
            tools_data = {"tools": request.tools}

            new_revision = await self.revision_repo.create_revision(
                agent_id=agent_id,
                tools_data=tools_data,
                previous_revision_id=previous_revision_id,
            )

            # Step 4: Update ToolDefinition to point to new revision
            await self.tool_def_repo.update_latest_revision_id(
                tool_definition_id=tool_definition.id, revision_id=new_revision.id
            )

            # Step 5: Commit transaction
            await self.db.commit()

            # Step 6: Build response
            response = ToolRegistrationResponse(
                tool_definition_id=str(tool_definition.id),
                revision_id=str(new_revision.id),
                agent_id=str(agent_id),
                tools_count=len(request.tools),
                previous_revision_id=str(previous_revision_id)
                if previous_revision_id
                else None,
                created_at=new_revision.created_at.isoformat(),
            )

            logger.info(
                f"Registered {len(request.tools)} tools for agent {agent_id}, "
                f"revision {new_revision.id}"
            )

            return response

        except Exception as e:
            # Rollback on error
            await self.db.rollback()
            logger.error(
                f"Failed to register tools for agent {agent_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def get_latest_revision(
        self, agent_id: UUID
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Get the latest tool definition revision for an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            Tuple of (tools_data dict, revision_id) or (None, None) if not found

        Example:
            >>> tools_data, revision_id = await service.get_latest_revision(agent_uuid)
            >>> if tools_data:
            ...     print(f"Found {len(tools_data['tools'])} tools")
            ...     print(f"Revision: {revision_id}")
        """
        tool_definition = await self.tool_def_repo.get_by_agent_id(agent_id)
        if not tool_definition or not tool_definition.latest_revision_id:
            return None, None

        revision = await self.revision_repo.get_by_id(
            tool_definition.latest_revision_id
        )
        if not revision:
            return None, None

        return revision.tools_data, str(revision.id)

    async def get_revision_history(
        self, agent_id: UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get revision history for an agent.

        Args:
            agent_id: Agent UUID
            limit: Maximum number of revisions to return

        Returns:
            List of revision info dictionaries (newest first)

        Example:
            >>> history = await service.get_revision_history(agent_uuid, limit=5)
            >>> for rev in history:
            ...     print(f"Revision {rev['revision_id']}: {rev['tools_count']} tools")
        """
        revisions = await self.revision_repo.get_by_agent_id(agent_id, limit=limit)

        return [
            {
                "revision_id": str(rev.id),
                "tools_count": len(rev.tools_data.get("tools", [])),
                "previous_revision_id": str(rev.previous_revision_id)
                if rev.previous_revision_id
                else None,
                "created_at": rev.created_at.isoformat(),
                "created_by": str(rev.created_by),
            }
            for rev in revisions
        ]


__all__ = ["ToolDefinitionService"]
