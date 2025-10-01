"""
Agent service for managing agent operations.

This service handles agent-related operations including CRUD operations,
API key management, and status management.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.agent_repository import AgentRepository
from app.repositories.agent_api_key_repository import AgentAPIKeyRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.core.security import generate_api_key, hash_api_key, extract_key_prefix


class AgentService:
    """Service for handling agent operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the agent service.

        Args:
            db: Async database session
        """
        self.db = db
        self.agent_repo = AgentRepository(db)
        self.api_key_repo = AgentAPIKeyRepository(db)
        self.project_repo = ProjectRepository(db)
        self.member_repo = ProjectMemberRepository(db)

    async def get_agent(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent UUID

        Returns:
            Dictionary containing agent data

        Raises:
            HTTPException: If agent not found
        """
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        # Get API key count
        api_key_count = await self.api_key_repo.count_keys(agent.id)

        return {
            "id": str(agent.id),
            "project_id": str(agent.project_id),
            "organization_id": str(agent.organization_id),
            "name": agent.name,
            "created_by": str(agent.created_by),
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "is_active": await self.agent_repo.is_active(agent.id),
            "is_archived": await self.agent_repo.is_archived(agent.id),
            "api_key_count": api_key_count,
        }

    async def list_agents(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        List agents in a project with pagination and filtering.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status
            is_archived: Filter by archived status

        Returns:
            Dictionary with items, total, page, page_size
        """
        agents, total = await self.agent_repo.get_by_project(
            project_id=project_id,
            page=page,
            page_size=page_size,
            is_active=is_active,
            is_archived=is_archived,
        )

        items = []
        for agent in agents:
            api_key_count = await self.api_key_repo.count_keys(agent.id)
            items.append({
                "id": str(agent.id),
                "project_id": str(agent.project_id),
                "organization_id": str(agent.organization_id),
                "name": agent.name,
                "created_by": str(agent.created_by),
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "is_active": await self.agent_repo.is_active(agent.id),
                "is_archived": await self.agent_repo.is_archived(agent.id),
                "api_key_count": api_key_count,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_agent(
        self, project_id: UUID, name: str, created_by: UUID
    ) -> Dict[str, Any]:
        """
        Create a new agent.

        Automatically activates the agent and sets organization_id from project.

        Args:
            project_id: Project UUID
            name: Agent name
            created_by: UUID of user creating the agent

        Returns:
            Created agent data

        Raises:
            HTTPException: If creation fails or project not found
        """
        try:
            # Verify project exists and get organization_id
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            # Verify user is project member
            is_member = await self.member_repo.is_member(project_id, created_by)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User must be project member to create agent",
                )

            # Create agent
            agent_data = {
                "project_id": project_id,
                "organization_id": project.organization_id,
                "name": name,
                "created_by": created_by,
            }
            agent = await self.agent_repo.create(agent_data)

            # Activate agent
            await self.agent_repo.activate(agent.id)

            await self.db.commit()
            return await self.get_agent(agent.id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create agent: {str(e)}",
            )

    async def update_agent(
        self, agent_id: UUID, name: str, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Update agent information.

        Args:
            agent_id: Agent UUID
            name: New agent name
            user_id: User performing the update

        Returns:
            Updated agent data

        Raises:
            HTTPException: If agent not found or user lacks permission
        """
        # Verify agent exists
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(agent.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to update agent",
            )

        try:
            updated_agent = await self.agent_repo.update(agent_id, {"name": name})
            if not updated_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found",
                )

            await self.db.commit()
            return await self.get_agent(agent_id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update agent: {str(e)}",
            )

    async def archive_agent(
        self, agent_id: UUID, user_id: UUID, reason: Optional[str] = None
    ) -> None:
        """
        Archive an agent.

        Args:
            agent_id: Agent UUID
            user_id: User performing the archive
            reason: Optional reason for archiving

        Raises:
            HTTPException: If agent not found or user lacks permission
        """
        # Verify agent exists
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(agent.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to archive agent",
            )

        try:
            await self.agent_repo.archive(agent_id, user_id, reason)
            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to archive agent: {str(e)}",
            )

    # API Key management

    async def list_api_keys(
        self, agent_id: UUID, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List API keys for an agent with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with items, total, page, page_size

        Note:
            - Does not return key_hash (security)
            - Only returns key_prefix for identification
        """
        keys, total = await self.api_key_repo.get_by_agent_id(
            agent_id, page, page_size
        )

        items = []
        for key in keys:
            is_expired = await self.api_key_repo.is_expired(key.id)
            items.append({
                "id": str(key.id),
                "agent_id": str(key.agent_id),
                "key_prefix": key.key_prefix,
                "name": key.name,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "created_by": str(key.created_by),
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "updated_at": key.updated_at.isoformat() if key.updated_at else None,
                "is_expired": is_expired,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_api_key(
        self,
        agent_id: UUID,
        created_by: UUID,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new API key for an agent.

        Returns the plain text API key only once.

        Args:
            agent_id: Agent UUID
            created_by: User creating the key
            name: Optional friendly name
            expires_in_days: Optional days until expiration

        Returns:
            Dictionary with api_key (plain text) and key metadata

        Raises:
            HTTPException: If agent not found

        Note:
            - Plain text API key is only returned once
            - Key is hashed with bcrypt before storage
            - key_prefix is stored for fast lookup
        """
        # Verify agent exists
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        try:
            # Generate API key
            api_key = generate_api_key()
            key_prefix = extract_key_prefix(api_key, prefix_length=16)
            key_hash = hash_api_key(api_key)

            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            # Create key record
            key_record = await self.api_key_repo.create(
                agent_id=agent_id,
                key_prefix=key_prefix,
                key_hash=key_hash,
                created_by=created_by,
                name=name,
                expires_at=expires_at,
            )

            await self.db.commit()

            # Return with plain text key (only time it's returned)
            return {
                "api_key": api_key,  # Plain text - shown only once
                "id": str(key_record.id),
                "agent_id": str(key_record.agent_id),
                "key_prefix": key_record.key_prefix,
                "name": key_record.name,
                "last_used_at": None,
                "expires_at": key_record.expires_at.isoformat() if key_record.expires_at else None,
                "created_by": str(key_record.created_by),
                "created_at": key_record.created_at.isoformat() if key_record.created_at else None,
                "updated_at": key_record.updated_at.isoformat() if key_record.updated_at else None,
                "is_expired": False,
            }

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create API key: {str(e)}",
            )

    async def delete_api_key(self, key_id: UUID, user_id: UUID) -> None:
        """
        Delete an API key.

        Args:
            key_id: API key UUID
            user_id: User performing the deletion

        Raises:
            HTTPException: If key not found or user lacks permission
        """
        # Verify key exists
        key = await self.api_key_repo.get_by_id(key_id)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        # Verify user is project member
        agent = await self.agent_repo.get_by_id(key.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        is_member = await self.member_repo.is_member(agent.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to delete API key",
            )

        try:
            deleted = await self.api_key_repo.delete_key(key_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found",
                )

            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete API key: {str(e)}",
            )