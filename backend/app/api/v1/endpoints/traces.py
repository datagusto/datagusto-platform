"""
Trace and Observation API endpoints.

This module provides endpoints for trace and observation management,
supporting both JWT (user) and API Key (agent) authentication.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_or_agent
from app.core.database import get_async_db
from app.repositories.project_member_repository import ProjectMemberRepository
from app.schemas.trace import (
    ObservationCreate,
    ObservationResponse,
    ObservationTreeResponse,
    ObservationUpdate,
    TraceCreate,
    TraceListResponse,
    TraceResponse,
    TraceUpdate,
)
from app.services.trace_service import TraceService

router = APIRouter()


async def verify_trace_access(
    trace_id: UUID,
    current_auth: dict,
    db: AsyncSession,
) -> None:
    """
    Verify that user/agent has access to a trace.

    Args:
        trace_id: Trace UUID
        current_auth: Current authenticated user or agent
        db: Database session

    Raises:
        HTTPException: 403 if no access
    """
    trace_service = TraceService(db)
    trace = await trace_service.get_trace(trace_id)

    if current_auth["type"] == "user":
        # User must be project member
        user_id = UUID(current_auth["id"])
        member_repo = ProjectMemberRepository(db)
        is_member = await member_repo.is_member(UUID(trace["project_id"]), user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to access trace",
            )
    elif current_auth["type"] == "agent":
        # Agent must own the trace
        if current_auth["agent_id"] != trace["agent_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent can only access its own traces",
            )


@router.get("/agents/{agent_id}/traces", response_model=TraceListResponse)
async def list_traces(
    agent_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(
        None, pattern="^(pending|running|completed|failed|error)$"
    ),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of traces for an agent.

    Args:
        agent_id: Agent UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Filter by status
        start_date: Filter traces started after this date
        end_date: Filter traces started before this date
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Paginated list of traces

    Note:
        - JWT users must be project member
        - API key must belong to the agent
    """
    trace_service = TraceService(db)

    # Authorization
    if current_auth["type"] == "user":
        # User must be project member
        from app.services.agent_service import AgentService

        agent_service = AgentService(db)
        agent = await agent_service.get_agent(agent_id)

        user_id = UUID(current_auth["id"])
        member_repo = ProjectMemberRepository(db)
        is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to list traces",
            )
    elif current_auth["type"] == "agent":
        # Agent can only list its own traces
        if current_auth["agent_id"] != str(agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent can only list its own traces",
            )

    return await trace_service.list_traces(
        agent_id=agent_id,
        page=page,
        page_size=page_size,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )


@router.post(
    "/agents/{agent_id}/traces",
    response_model=TraceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trace(
    agent_id: UUID,
    trace_in: TraceCreate,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new trace.

    Automatically sets project_id and organization_id from agent.

    Args:
        agent_id: Agent UUID
        trace_in: Trace creation data
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Created trace

    Note:
        - API key authentication recommended for production
        - Agent API key must belong to the agent
    """
    trace_service = TraceService(db)

    # Authorization
    if current_auth["type"] == "agent":
        # Agent can only create traces for itself
        if current_auth["agent_id"] != str(agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent can only create traces for itself",
            )
    elif current_auth["type"] == "user":
        # User must be project member
        from app.services.agent_service import AgentService

        agent_service = AgentService(db)
        agent = await agent_service.get_agent(agent_id)

        user_id = UUID(current_auth["id"])
        member_repo = ProjectMemberRepository(db)
        is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to create trace",
            )

    return await trace_service.create_trace(
        agent_id=agent_id,
        status=trace_in.status,
        trace_metadata=trace_in.trace_metadata,
        started_at=trace_in.started_at,
    )


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(
    trace_id: UUID,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get trace details.

    Args:
        trace_id: Trace UUID
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Trace details

    Raises:
        HTTPException: 404 if not found, 403 if no access
    """
    await verify_trace_access(trace_id, current_auth, db)

    trace_service = TraceService(db)
    return await trace_service.get_trace(trace_id)


@router.patch("/{trace_id}", response_model=TraceResponse)
async def update_trace(
    trace_id: UUID,
    trace_update: TraceUpdate,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update trace information.

    Args:
        trace_id: Trace UUID
        trace_update: Trace update data
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Updated trace

    Raises:
        HTTPException: 404 if not found, 403 if no access

    Note:
        - API key authentication recommended for production
    """
    await verify_trace_access(trace_id, current_auth, db)

    trace_service = TraceService(db)
    return await trace_service.update_trace(
        trace_id=trace_id,
        status=trace_update.status,
        ended_at=trace_update.ended_at,
        trace_metadata=trace_update.trace_metadata,
    )


# Observation endpoints


@router.get("/{trace_id}/observations", response_model=dict)
async def list_observations(
    trace_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: str | None = Query(
        None, pattern="^(llm|tool|retriever|agent|embedding|reranker|custom)$"
    ),
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of observations for a trace (flat list).

    Args:
        trace_id: Trace UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        type: Filter by observation type
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Paginated list of observations

    Note:
        - Returns flat list ordered by started_at
        - Use /observations/tree for hierarchical structure
    """
    await verify_trace_access(trace_id, current_auth, db)

    trace_service = TraceService(db)
    return await trace_service.list_observations(
        trace_id=trace_id,
        page=page,
        page_size=page_size,
        observation_type=type,
    )


@router.get(
    "/{trace_id}/observations/tree", response_model=list[ObservationTreeResponse]
)
async def get_observation_tree(
    trace_id: UUID,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get observation tree for a trace (hierarchical structure).

    Args:
        trace_id: Trace UUID
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        List of root observations with nested children

    Note:
        - Returns hierarchical tree structure
        - Children are nested in "children" field
        - No pagination (returns all observations)
    """
    await verify_trace_access(trace_id, current_auth, db)

    trace_service = TraceService(db)
    return await trace_service.get_observation_tree(trace_id)


@router.post(
    "/{trace_id}/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_observation(
    trace_id: UUID,
    observation_in: ObservationCreate,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new observation.

    Args:
        trace_id: Trace UUID
        observation_in: Observation creation data
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Created observation

    Note:
        - API key authentication recommended for production
        - parent_observation_id is NULL for root observations
    """
    await verify_trace_access(trace_id, current_auth, db)

    trace_service = TraceService(db)
    return await trace_service.create_observation(
        trace_id=trace_id,
        observation_type=observation_in.type,
        name=observation_in.name,
        status=observation_in.status,
        observation_metadata=observation_in.observation_metadata,
        parent_observation_id=observation_in.parent_observation_id,
        started_at=observation_in.started_at,
    )


@router.get("/observations/{observation_id}", response_model=ObservationResponse)
async def get_observation(
    observation_id: UUID,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get observation details.

    Args:
        observation_id: Observation UUID
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Observation details

    Raises:
        HTTPException: 404 if not found, 403 if no access
    """
    trace_service = TraceService(db)
    observation = await trace_service.get_observation(observation_id)

    # Verify access to parent trace
    await verify_trace_access(UUID(observation["trace_id"]), current_auth, db)

    return observation


@router.patch("/observations/{observation_id}", response_model=ObservationResponse)
async def update_observation(
    observation_id: UUID,
    observation_update: ObservationUpdate,
    current_auth: dict = Depends(get_current_user_or_agent),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update observation information.

    Args:
        observation_id: Observation UUID
        observation_update: Observation update data
        current_auth: Current authenticated user or agent
        db: Database session

    Returns:
        Updated observation

    Raises:
        HTTPException: 404 if not found, 403 if no access

    Note:
        - API key authentication recommended for production
    """
    trace_service = TraceService(db)
    observation = await trace_service.get_observation(observation_id)

    # Verify access to parent trace
    await verify_trace_access(UUID(observation["trace_id"]), current_auth, db)

    return await trace_service.update_observation(
        observation_id=observation_id,
        status=observation_update.status,
        ended_at=observation_update.ended_at,
        observation_metadata=observation_update.observation_metadata,
    )
