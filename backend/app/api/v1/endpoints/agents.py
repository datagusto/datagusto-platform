"""
Agent API endpoints.

This module provides endpoints for agent management including CRUD operations
and API key management.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_organization_member
from app.core.database import get_async_db
from app.repositories.project_member_repository import ProjectMemberRepository
from app.schemas.agent import (
    AgentAPIKeyCreate,
    AgentAPIKeyCreateResponse,
    AgentArchiveRequest,
    AgentResponse,
    AgentUpdate,
)
from app.services.agent_service import AgentService

router = APIRouter()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get agent details.

    Args:
        agent_id: Agent UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Agent details

    Raises:
        HTTPException: 404 if agent not found, 403 if not project member
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    # Get agent to check project membership
    agent = await agent_service.get_agent(agent_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view agent",
        )

    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_update: AgentUpdate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update agent information.

    Args:
        agent_id: Agent UUID
        agent_update: Agent update data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated agent

    Raises:
        HTTPException: 404 if not found, 403 if not project member
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    return await agent_service.update_agent(
        agent_id=agent_id,
        name=agent_update.name,
        user_id=user_id,
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_agent(
    agent_id: UUID,
    archive_request: AgentArchiveRequest,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Archive an agent (soft delete).

    Args:
        agent_id: Agent UUID
        archive_request: Archive reason
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if not found, 403 if not project member

    Note:
        - This is a soft delete (archive record created)
        - All API keys for this agent will be effectively disabled
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    await agent_service.archive_agent(
        agent_id=agent_id,
        user_id=user_id,
        reason=archive_request.reason,
    )


# API Key management endpoints


@router.get("/{agent_id}/api-keys", response_model=dict)
async def list_api_keys(
    agent_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of API keys for an agent.

    Args:
        agent_id: Agent UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of API keys

    Note:
        - Does not return key_hash or full API key (security)
        - Only returns key_prefix for identification
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    # Get agent to check project membership
    agent = await agent_service.get_agent(agent_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to list API keys",
        )

    return await agent_service.list_api_keys(
        agent_id=agent_id,
        page=page,
        page_size=min(page_size, 100),
    )


@router.post(
    "/{agent_id}/api-keys",
    response_model=AgentAPIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    agent_id: UUID,
    key_create: AgentAPIKeyCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new API key for an agent.

    IMPORTANT: The full API key is only returned once in this response.
    Store it securely - it cannot be retrieved again.

    Args:
        agent_id: Agent UUID
        key_create: API key creation data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created API key with full api_key (shown only once)

    Note:
        - User must be project member
        - API key is hashed with bcrypt before storage
        - Only key_prefix is stored for fast lookup
        - Full key cannot be retrieved after creation
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    # Get agent to check project membership
    agent = await agent_service.get_agent(agent_id)
    member_repo = ProjectMemberRepository(db)
    is_member = await member_repo.is_member(UUID(agent["project_id"]), user_id)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to create API key",
        )

    return await agent_service.create_api_key(
        agent_id=agent_id,
        created_by=user_id,
        name=key_create.name,
        expires_in_days=key_create.expires_in_days,
    )


@router.delete("/{agent_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    agent_id: UUID,
    key_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Delete an API key.

    Args:
        agent_id: Agent UUID (for URL consistency, not used)
        key_id: API key UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if not found, 403 if not project member

    Note:
        - User must be project member
        - Deleted keys cannot be recovered
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)

    await agent_service.delete_api_key(
        key_id=key_id,
        user_id=user_id,
    )
