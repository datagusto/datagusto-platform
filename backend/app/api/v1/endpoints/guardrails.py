"""
Guardrail API endpoints.

This module provides endpoints for guardrail management including CRUD operations
and assignment management.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_organization_member
from app.core.database import get_async_db
from app.repositories.project_member_repository import ProjectMemberRepository
from app.schemas.guardrail import (
    GuardrailAgentAssignmentCreate,
    GuardrailAgentAssignmentResponse,
    GuardrailCreate,
    GuardrailListResponse,
    GuardrailResponse,
    GuardrailUpdate,
)
from app.schemas.guardrail_evaluation import GuardrailEvaluationLogListResponse
from app.services.guardrail_service import GuardrailService

router = APIRouter()


@router.get("/projects/{project_id}/guardrails", response_model=GuardrailListResponse)
async def list_guardrails(
    project_id: UUID,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
    is_archived: bool | None = None,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of guardrails in a project.

    Args:
        project_id: Project UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        is_active: Filter by active status
        is_archived: Filter by archived status
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of guardrails

    Note:
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to list guardrails",
        )

    return await guardrail_service.list_guardrails(
        project_id=project_id,
        page=page,
        page_size=min(page_size, 100),
        is_active=is_active,
        is_archived=is_archived,
    )


@router.post(
    "/projects/{project_id}/guardrails",
    response_model=GuardrailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_guardrail(
    project_id: UUID,
    guardrail_in: GuardrailCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new guardrail.

    Automatically:
    - Sets organization_id from project
    - Activates the guardrail

    Args:
        project_id: Project UUID
        guardrail_in: Guardrail creation data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created guardrail

    Note:
        - User must be project member
        - definition field contains JSONB trigger conditions and actions
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    return await guardrail_service.create_guardrail(
        project_id=project_id,
        name=guardrail_in.name,
        definition=guardrail_in.definition,
        created_by=user_id,
    )


@router.get("/{guardrail_id}", response_model=GuardrailResponse)
async def get_guardrail(
    guardrail_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get guardrail details.

    Args:
        guardrail_id: Guardrail UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Guardrail details

    Raises:
        HTTPException: 404 if guardrail not found, 403 if not project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    # Get guardrail to check project membership
    guardrail = await guardrail_service.get_guardrail(guardrail_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(guardrail["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view guardrail",
        )

    return guardrail


@router.patch("/{guardrail_id}", response_model=GuardrailResponse)
async def update_guardrail(
    guardrail_id: UUID,
    guardrail_update: GuardrailUpdate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update guardrail information.

    Args:
        guardrail_id: Guardrail UUID
        guardrail_update: Guardrail update data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated guardrail

    Raises:
        HTTPException: 404 if not found, 403 if not project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    return await guardrail_service.update_guardrail(
        guardrail_id=guardrail_id,
        name=guardrail_update.name,
        definition=guardrail_update.definition,
        user_id=user_id,
    )


@router.delete("/{guardrail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_guardrail(
    guardrail_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Archive a guardrail (soft delete).

    Args:
        guardrail_id: Guardrail UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if not found, 403 if not project member

    Note:
        - This is a soft delete (archive record created)
        - Archived guardrails can be filtered out in list queries
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    await guardrail_service.archive_guardrail(
        guardrail_id=guardrail_id,
        user_id=user_id,
        reason=None,
    )


# Assignment management endpoints


@router.get("/{guardrail_id}/assignments", response_model=dict)
async def list_assignments(
    guardrail_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of agents assigned to a guardrail.

    Args:
        guardrail_id: Guardrail UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of assignments

    Note:
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    # Get guardrail to check project membership
    guardrail = await guardrail_service.get_guardrail(guardrail_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(guardrail["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to list assignments",
        )

    return await guardrail_service.list_assignments(
        guardrail_id=guardrail_id,
        page=page,
        page_size=min(page_size, 100),
    )


@router.post(
    "/{guardrail_id}/assignments",
    response_model=GuardrailAgentAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_to_agent(
    guardrail_id: UUID,
    assignment_in: GuardrailAgentAssignmentCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Assign guardrail to an agent.

    Args:
        guardrail_id: Guardrail UUID
        assignment_in: Assignment data with agent_id
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created assignment

    Raises:
        HTTPException:
            - 404 if guardrail or agent not found
            - 400 if guardrail and agent are in different projects
            - 400 if assignment already exists
            - 403 if not project member

    Note:
        - Guardrail and agent must be in the same project
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    return await guardrail_service.assign_to_agent(
        guardrail_id=guardrail_id,
        agent_id=assignment_in.agent_id,
        user_id=user_id,
    )


@router.delete(
    "/{guardrail_id}/assignments/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unassign_from_agent(
    guardrail_id: UUID,
    agent_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Unassign guardrail from an agent.

    Args:
        guardrail_id: Guardrail UUID
        agent_id: Agent UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if assignment not found, 403 if not project member

    Note:
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    await guardrail_service.unassign_from_agent(
        guardrail_id=guardrail_id,
        agent_id=agent_id,
        user_id=user_id,
    )


@router.get("/agents/{agent_id}/guardrails", response_model=GuardrailListResponse)
async def list_agent_guardrails(
    agent_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of guardrails assigned to an agent.

    Args:
        agent_id: Agent UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of guardrails

    Note:
        - User must be project member
        - Returns full guardrail objects, not just assignment records
    """
    user_id = UUID(current_user["id"])
    guardrail_service = GuardrailService(db)

    # Import here to avoid circular dependency
    from app.services.agent_service import AgentService

    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to list agent guardrails",
        )

    return await guardrail_service.list_agent_guardrails(
        agent_id=agent_id,
        page=page,
        page_size=min(page_size, 100),
    )


@router.get(
    "/agents/{agent_id}/evaluation-logs",
    response_model=GuardrailEvaluationLogListResponse,
)
async def list_agent_evaluation_logs(
    agent_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of evaluation logs for an agent.

    Returns paginated list of guardrail evaluation logs for a specific agent,
    ordered by creation time (most recent first).

    Args:
        agent_id: Agent UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of evaluation logs

    Raises:
        HTTPException:
            - 403: User is not a project member
            - 404: Agent not found

    Note:
        - User must be project member to access evaluation logs
        - Logs are returned in descending order by created_at
        - Each log contains full evaluation details in log_data JSONB field

    Example:
        >>> # GET /api/v1/guardrails/agents/{agent_id}/evaluation-logs?page=1&page_size=20
        >>> {
        ...     "items": [
        ...         {
        ...             "id": "123e4567-e89b-12d3-a456-426614174000",
        ...             "request_id": "req_a1b2c3d4e5f6",
        ...             "timing": "on_start",
        ...             "process_type": "tool",
        ...             "should_proceed": False,
        ...             "log_data": {...},
        ...             "created_at": "2025-01-15T10:30:00Z"
        ...         }
        ...     ],
        ...     "total": 42,
        ...     "page": 1,
        ...     "page_size": 20
        ... }
    """
    user_id = UUID(current_user["id"])

    # Import here to avoid circular dependency
    from app.repositories.guardrail_evaluation_log_repository import (
        GuardrailEvaluationLogRepository,
    )
    from app.services.agent_service import AgentService

    # Verify agent exists and user has access
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id)

    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view evaluation logs",
        )

    # Fetch evaluation logs
    log_repo = GuardrailEvaluationLogRepository(db)
    logs, total = await log_repo.list_by_agent(
        agent_id=agent_id,
        page=page,
        page_size=min(page_size, 100),
    )

    # Convert to response schema
    return GuardrailEvaluationLogListResponse(
        items=[
            {
                "id": str(log.id),
                "request_id": log.request_id,
                "agent_id": str(log.agent_id),
                "project_id": str(log.project_id),
                "organization_id": str(log.organization_id),
                "trace_id": log.trace_id,
                "timing": log.timing,
                "process_type": log.process_type,
                "should_proceed": log.should_proceed,
                "log_data": log.log_data,
                "created_at": log.created_at.isoformat() if log.created_at else "",
                "updated_at": log.updated_at.isoformat() if log.updated_at else "",
            }
            for log in logs
        ],
        total=total,
        page=page,
        page_size=min(page_size, 100),
    )
