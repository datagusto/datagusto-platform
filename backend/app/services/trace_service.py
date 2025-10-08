"""
Trace service for managing trace and observation operations.

This service handles trace-related operations including CRUD operations,
observation management, and hierarchical tree building.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.agent_repository import AgentRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.trace_repository import TraceRepository


class TraceService:
    """Service for handling trace and observation operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the trace service.

        Args:
            db: Async database session
        """
        self.db = db
        self.trace_repo = TraceRepository(db)
        self.observation_repo = ObservationRepository(db)
        self.agent_repo = AgentRepository(db)
        self.member_repo = ProjectMemberRepository(db)

    async def get_trace(self, trace_id: UUID) -> dict[str, Any]:
        """
        Get trace by ID.

        Args:
            trace_id: Trace UUID

        Returns:
            Dictionary containing trace data

        Raises:
            HTTPException: If trace not found
        """
        trace = await self.trace_repo.get_by_id(trace_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found",
            )

        # Get observation count
        observation_count = await self.trace_repo.get_observation_count(trace.id)

        # Calculate duration
        duration_seconds = await self.trace_repo.calculate_duration(trace.id)
        duration_ms = int(duration_seconds * 1000) if duration_seconds else None

        return {
            "id": str(trace.id),
            "agent_id": str(trace.agent_id),
            "project_id": str(trace.project_id),
            "organization_id": str(trace.organization_id),
            "status": trace.status,
            "started_at": trace.started_at.isoformat() if trace.started_at else None,
            "ended_at": trace.ended_at.isoformat() if trace.ended_at else None,
            "metadata": trace.trace_metadata,
            "created_at": trace.created_at.isoformat() if trace.created_at else None,
            "updated_at": trace.updated_at.isoformat() if trace.updated_at else None,
            "observation_count": observation_count,
            "duration_ms": duration_ms,
        }

    async def list_traces(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        List traces for an agent with pagination and filtering.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status
            start_date: Filter traces started after this date
            end_date: Filter traces started before this date

        Returns:
            Dictionary with items, total, page, page_size
        """
        traces, total = await self.trace_repo.get_by_agent(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        items = []
        for trace in traces:
            observation_count = await self.trace_repo.get_observation_count(trace.id)
            duration_seconds = await self.trace_repo.calculate_duration(trace.id)
            duration_ms = int(duration_seconds * 1000) if duration_seconds else None

            items.append(
                {
                    "id": str(trace.id),
                    "agent_id": str(trace.agent_id),
                    "project_id": str(trace.project_id),
                    "organization_id": str(trace.organization_id),
                    "status": trace.status,
                    "started_at": trace.started_at.isoformat()
                    if trace.started_at
                    else None,
                    "ended_at": trace.ended_at.isoformat() if trace.ended_at else None,
                    "metadata": trace.trace_metadata,
                    "created_at": trace.created_at.isoformat()
                    if trace.created_at
                    else None,
                    "updated_at": trace.updated_at.isoformat()
                    if trace.updated_at
                    else None,
                    "observation_count": observation_count,
                    "duration_ms": duration_ms,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_trace(
        self,
        agent_id: UUID,
        status: str,
        trace_metadata: dict[str, Any],
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Create a new trace.

        Automatically sets project_id and organization_id from agent.

        Args:
            agent_id: Agent UUID
            status: Initial status
            trace_metadata: JSONB metadata
            started_at: Start timestamp (defaults to now())

        Returns:
            Created trace data

        Raises:
            HTTPException: If agent not found
        """
        # Verify agent exists and get project/organization IDs
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        try:
            # Create trace
            trace_data = {
                "agent_id": agent_id,
                "project_id": agent.project_id,
                "organization_id": agent.organization_id,
                "status": status,
                "started_at": started_at or datetime.utcnow(),
                "trace_metadata": trace_metadata,
            }
            trace = await self.trace_repo.create(trace_data)

            await self.db.commit()
            return await self.get_trace(trace.id)

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create trace: {str(e)}",
            )

    async def update_trace(
        self,
        trace_id: UUID,
        status: str | None = None,
        ended_at: datetime | None = None,
        trace_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update trace information.

        Args:
            trace_id: Trace UUID
            status: New status (optional)
            ended_at: End timestamp (optional)
            trace_metadata: New metadata (optional)

        Returns:
            Updated trace data

        Raises:
            HTTPException: If trace not found
        """
        # Verify trace exists
        trace = await self.trace_repo.get_by_id(trace_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found",
            )

        try:
            update_data = {}
            if status is not None:
                update_data["status"] = status
            if ended_at is not None:
                update_data["ended_at"] = ended_at
            if trace_metadata is not None:
                update_data["trace_metadata"] = trace_metadata

            updated_trace = await self.trace_repo.update(trace_id, update_data)
            if not updated_trace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Trace not found",
                )

            await self.db.commit()
            return await self.get_trace(trace_id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update trace: {str(e)}",
            )

    # Observation methods

    async def get_observation(self, observation_id: UUID) -> dict[str, Any]:
        """
        Get observation by ID.

        Args:
            observation_id: Observation UUID

        Returns:
            Dictionary containing observation data

        Raises:
            HTTPException: If observation not found
        """
        observation = await self.observation_repo.get_by_id(observation_id)
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation not found",
            )

        # Get child count
        child_count = await self.observation_repo.get_child_count(observation.id)

        # Calculate duration
        duration_seconds = await self.observation_repo.calculate_duration(
            observation.id
        )
        duration_ms = int(duration_seconds * 1000) if duration_seconds else None

        return {
            "id": str(observation.id),
            "trace_id": str(observation.trace_id),
            "parent_observation_id": str(observation.parent_observation_id)
            if observation.parent_observation_id
            else None,
            "type": observation.type,
            "name": observation.name,
            "status": observation.status,
            "started_at": observation.started_at.isoformat()
            if observation.started_at
            else None,
            "ended_at": observation.ended_at.isoformat()
            if observation.ended_at
            else None,
            "metadata": observation.observation_metadata,
            "created_at": observation.created_at.isoformat()
            if observation.created_at
            else None,
            "updated_at": observation.updated_at.isoformat()
            if observation.updated_at
            else None,
            "child_count": child_count,
            "duration_ms": duration_ms,
        }

    async def list_observations(
        self,
        trace_id: UUID,
        page: int = 1,
        page_size: int = 20,
        observation_type: str | None = None,
    ) -> dict[str, Any]:
        """
        List observations for a trace (flat list).

        Args:
            trace_id: Trace UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            observation_type: Filter by observation type

        Returns:
            Dictionary with items, total, page, page_size
        """
        observations, total = await self.observation_repo.get_by_trace_id(
            trace_id=trace_id,
            page=page,
            page_size=page_size,
            observation_type=observation_type,
        )

        items = []
        for observation in observations:
            child_count = await self.observation_repo.get_child_count(observation.id)
            duration_seconds = await self.observation_repo.calculate_duration(
                observation.id
            )
            duration_ms = int(duration_seconds * 1000) if duration_seconds else None

            items.append(
                {
                    "id": str(observation.id),
                    "trace_id": str(observation.trace_id),
                    "parent_observation_id": str(observation.parent_observation_id)
                    if observation.parent_observation_id
                    else None,
                    "type": observation.type,
                    "name": observation.name,
                    "status": observation.status,
                    "started_at": observation.started_at.isoformat()
                    if observation.started_at
                    else None,
                    "ended_at": observation.ended_at.isoformat()
                    if observation.ended_at
                    else None,
                    "metadata": observation.observation_metadata,
                    "created_at": observation.created_at.isoformat()
                    if observation.created_at
                    else None,
                    "updated_at": observation.updated_at.isoformat()
                    if observation.updated_at
                    else None,
                    "child_count": child_count,
                    "duration_ms": duration_ms,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_observation_tree(self, trace_id: UUID) -> list[dict[str, Any]]:
        """
        Get observation tree for a trace (hierarchical structure).

        Args:
            trace_id: Trace UUID

        Returns:
            List of root observations with nested children
        """
        # Get all observations for the trace
        all_observations = await self.observation_repo.get_tree_by_trace_id(trace_id)

        # Build lookup map
        obs_map = {}
        for obs in all_observations:
            child_count = await self.observation_repo.get_child_count(obs.id)
            duration_seconds = await self.observation_repo.calculate_duration(obs.id)
            duration_ms = int(duration_seconds * 1000) if duration_seconds else None

            obs_map[str(obs.id)] = {
                "id": str(obs.id),
                "trace_id": str(obs.trace_id),
                "parent_observation_id": str(obs.parent_observation_id)
                if obs.parent_observation_id
                else None,
                "type": obs.type,
                "name": obs.name,
                "status": obs.status,
                "started_at": obs.started_at.isoformat() if obs.started_at else None,
                "ended_at": obs.ended_at.isoformat() if obs.ended_at else None,
                "metadata": obs.observation_metadata,
                "created_at": obs.created_at.isoformat() if obs.created_at else None,
                "updated_at": obs.updated_at.isoformat() if obs.updated_at else None,
                "child_count": child_count,
                "duration_ms": duration_ms,
                "children": [],
            }

        # Build tree structure
        roots = []
        for _, obs_data in obs_map.items():
            parent_id = obs_data["parent_observation_id"]
            if parent_id is None:
                roots.append(obs_data)
            else:
                if parent_id in obs_map:
                    obs_map[parent_id]["children"].append(obs_data)

        return roots

    async def create_observation(
        self,
        trace_id: UUID,
        observation_type: str,
        name: str,
        status: str,
        observation_metadata: dict[str, Any],
        parent_observation_id: UUID | None = None,
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Create a new observation.

        Args:
            trace_id: Trace UUID
            observation_type: Observation type
            name: Display name
            status: Initial status
            observation_metadata: JSONB metadata
            parent_observation_id: Parent observation (None for root)
            started_at: Start timestamp (defaults to now())

        Returns:
            Created observation data

        Raises:
            HTTPException: If trace not found or parent observation invalid
        """
        # Verify trace exists
        trace = await self.trace_repo.get_by_id(trace_id)
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found",
            )

        # Verify parent observation if provided
        if parent_observation_id:
            parent = await self.observation_repo.get_by_id(parent_observation_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent observation not found",
                )
            if parent.trace_id != trace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent observation must belong to the same trace",
                )

        try:
            # Create observation
            observation_data = {
                "trace_id": trace_id,
                "parent_observation_id": parent_observation_id,
                "type": observation_type,
                "name": name,
                "status": status,
                "started_at": started_at or datetime.utcnow(),
                "observation_metadata": observation_metadata,
            }
            observation = await self.observation_repo.create(observation_data)

            await self.db.commit()
            return await self.get_observation(observation.id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create observation: {str(e)}",
            )

    async def update_observation(
        self,
        observation_id: UUID,
        status: str | None = None,
        ended_at: datetime | None = None,
        observation_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update observation information.

        Args:
            observation_id: Observation UUID
            status: New status (optional)
            ended_at: End timestamp (optional)
            observation_metadata: New metadata (optional)

        Returns:
            Updated observation data

        Raises:
            HTTPException: If observation not found
        """
        # Verify observation exists
        observation = await self.observation_repo.get_by_id(observation_id)
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observation not found",
            )

        try:
            update_data = {}
            if status is not None:
                update_data["status"] = status
            if ended_at is not None:
                update_data["ended_at"] = ended_at
            if observation_metadata is not None:
                update_data["observation_metadata"] = observation_metadata

            updated_observation = await self.observation_repo.update(
                observation_id, update_data
            )
            if not updated_observation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Observation not found",
                )

            await self.db.commit()
            return await self.get_observation(observation_id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update observation: {str(e)}",
            )
