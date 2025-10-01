"""
Agent API Key repository for database operations.

This repository handles operations for the AgentAPIKey model,
managing API keys with bcrypt hashing and prefix-based lookup.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import UUID

from app.models.agent import AgentAPIKey


class AgentAPIKeyRepository:
    """Repository for agent API key database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_by_id(self, key_id: UUID) -> Optional[AgentAPIKey]:
        """
        Get API key by ID.

        Args:
            key_id: API key UUID

        Returns:
            AgentAPIKey or None if not found
        """
        stmt = select(AgentAPIKey).where(AgentAPIKey.id == key_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_agent_id(
        self, agent_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[List[AgentAPIKey], int]:
        """
        Get API keys by agent ID with pagination.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (API keys list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(AgentAPIKey).where(
            AgentAPIKey.agent_id == agent_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Get paginated keys
        stmt = (
            select(AgentAPIKey)
            .where(AgentAPIKey.agent_id == agent_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(AgentAPIKey.created_at.desc())
        )
        result = await self.db.execute(stmt)
        keys = result.scalars().all()

        return list(keys), total

    async def get_by_key_prefix(self, key_prefix: str) -> Optional[AgentAPIKey]:
        """
        Get API key by prefix for authentication.

        Args:
            key_prefix: First 16 characters of API key

        Returns:
            AgentAPIKey or None if not found
        """
        stmt = select(AgentAPIKey).where(AgentAPIKey.key_prefix == key_prefix)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        agent_id: UUID,
        key_prefix: str,
        key_hash: str,
        created_by: UUID,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> AgentAPIKey:
        """
        Create a new API key.

        Args:
            agent_id: Agent UUID
            key_prefix: First 16 characters of API key (for fast lookup)
            key_hash: Bcrypt hash of full API key
            created_by: User UUID who created the key
            name: Optional friendly name
            expires_at: Optional expiration datetime

        Returns:
            Created AgentAPIKey
        """
        api_key = AgentAPIKey(
            agent_id=agent_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(api_key)
        await self.db.flush()
        return api_key

    async def delete_key(self, key_id: UUID) -> bool:
        """
        Delete API key.

        Args:
            key_id: API key UUID

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(AgentAPIKey).where(AgentAPIKey.id == key_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def update_last_used(self, key_id: UUID) -> None:
        """
        Update last_used_at timestamp.

        Args:
            key_id: API key UUID
        """
        stmt = select(AgentAPIKey).where(AgentAPIKey.id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key:
            api_key.last_used_at = datetime.utcnow()
            await self.db.flush()

    async def is_expired(self, key_id: UUID) -> bool:
        """
        Check if API key is expired.

        Args:
            key_id: API key UUID

        Returns:
            True if expired, False otherwise
        """
        stmt = select(AgentAPIKey).where(AgentAPIKey.id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return True

        if api_key.expires_at is None:
            return False

        return datetime.utcnow() > api_key.expires_at.replace(tzinfo=None)

    async def count_keys(self, agent_id: UUID) -> int:
        """
        Count total API keys for an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            Number of API keys
        """
        stmt = select(func.count()).select_from(AgentAPIKey).where(
            AgentAPIKey.agent_id == agent_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()