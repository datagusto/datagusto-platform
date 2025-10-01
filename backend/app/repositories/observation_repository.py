"""
Observation repository for database operations.

This repository handles operations for the Observation model, including
CRUD operations, hierarchical queries, and archive management.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.models.trace import Observation, ObservationArchive
from app.repositories.base_repository import BaseRepository


class ObservationRepository(BaseRepository[Observation]):
    """Repository for observation database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            db: Async database session
        """
        super().__init__(db, Observation)

    async def get_by_trace_id(
        self,
        trace_id: UUID,
        page: int = 1,
        page_size: int = 20,
        observation_type: Optional[str] = None,
    ) -> tuple[List[Observation], int]:
        """
        Get observations by trace ID with pagination (flat list).

        Args:
            trace_id: Trace UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            observation_type: Filter by observation type (llm, tool, retriever, etc.)

        Returns:
            Tuple of (observations list, total count)
        """
        # Base query
        stmt = select(Observation).where(Observation.trace_id == trace_id)

        # Apply type filter
        if observation_type:
            stmt = stmt.where(Observation.type == observation_type)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        stmt = stmt.order_by(Observation.started_at.asc())

        # Execute query
        result = await self.db.execute(stmt)
        observations = result.scalars().all()

        return list(observations), total

    async def get_tree_by_trace_id(self, trace_id: UUID) -> List[Observation]:
        """
        Get observations by trace ID as a hierarchical tree.

        This returns all observations for the trace without pagination.
        Client should build tree structure using parent_observation_id.

        Args:
            trace_id: Trace UUID

        Returns:
            List of all observations (flat, ordered by started_at)
        """
        stmt = (
            select(Observation)
            .where(Observation.trace_id == trace_id)
            .order_by(Observation.started_at.asc())
        )
        result = await self.db.execute(stmt)
        observations = result.scalars().all()
        return list(observations)

    async def get_root_observations(self, trace_id: UUID) -> List[Observation]:
        """
        Get root observations (parent_observation_id is NULL) for a trace.

        Args:
            trace_id: Trace UUID

        Returns:
            List of root observations
        """
        stmt = (
            select(Observation)
            .where(
                Observation.trace_id == trace_id,
                Observation.parent_observation_id.is_(None),
            )
            .order_by(Observation.started_at.asc())
        )
        result = await self.db.execute(stmt)
        observations = result.scalars().all()
        return list(observations)

    async def get_child_observations(
        self, parent_observation_id: UUID
    ) -> List[Observation]:
        """
        Get child observations for a parent observation.

        Args:
            parent_observation_id: Parent observation UUID

        Returns:
            List of child observations
        """
        stmt = (
            select(Observation)
            .where(Observation.parent_observation_id == parent_observation_id)
            .order_by(Observation.started_at.asc())
        )
        result = await self.db.execute(stmt)
        observations = result.scalars().all()
        return list(observations)

    async def get_child_count(self, observation_id: UUID) -> int:
        """
        Count child observations for an observation.

        Args:
            observation_id: Observation UUID

        Returns:
            Number of child observations
        """
        stmt = select(func.count()).select_from(Observation).where(
            Observation.parent_observation_id == observation_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def calculate_duration(self, observation_id: UUID) -> Optional[float]:
        """
        Calculate observation duration in seconds.

        Args:
            observation_id: Observation UUID

        Returns:
            Duration in seconds, None if observation is still running (ended_at is NULL)
        """
        observation = await self.get_by_id(observation_id)
        if not observation or not observation.ended_at:
            return None

        delta = observation.ended_at - observation.started_at
        return delta.total_seconds()

    async def archive(
        self, observation_id: UUID, archived_by: Optional[UUID], reason: str
    ) -> ObservationArchive:
        """
        Archive observation (create archive record).

        Args:
            observation_id: Observation UUID
            archived_by: User UUID who archived the observation (None for automated)
            reason: Reason for archiving

        Returns:
            Created ObservationArchive

        Raises:
            IntegrityError: If observation is already archived
        """
        archive = ObservationArchive(
            observation_id=observation_id,
            archived_by=archived_by,
            reason=reason,
        )
        self.db.add(archive)
        await self.db.flush()
        return archive

    async def is_archived(self, observation_id: UUID) -> bool:
        """
        Check if observation is archived.

        Args:
            observation_id: Observation UUID

        Returns:
            True if observation is archived, False otherwise
        """
        stmt = select(ObservationArchive).where(
            ObservationArchive.observation_id == observation_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
