"""
Project API endpoints.

This module provides endpoints for project management including CRUD operations,
member management, and owner management.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_organization_member
from app.core.database import get_async_db
from app.repositories.project_member_repository import ProjectMemberRepository
from app.schemas.agent import AgentCreate, AgentListResponse, AgentResponse
from app.schemas.guardrail import (
    GuardrailCreate,
    GuardrailListResponse,
    GuardrailResponse,
)
from app.schemas.project import (
    ProjectArchiveRequest,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectOwnerResponse,
    ProjectOwnerUpdate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.agent_service import AgentService
from app.services.guardrail_service import GuardrailService
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
    is_archived: bool | None = None,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of projects in the organization.

    Args:
        request: FastAPI Request (for X-Organization-ID header)
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        is_active: Filter by active status
        is_archived: Filter by archived status
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of projects

    Note:
        - Requires X-Organization-ID header
        - Only returns projects in the specified organization
    """
    organization_id = UUID(current_user["organization_id"])
    project_service = ProjectService(db)

    return await project_service.list_projects(
        organization_id=organization_id,
        page=page,
        page_size=min(page_size, 100),
        is_active=is_active,
        is_archived=is_archived,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    project_in: ProjectCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new project.

    Automatically:
    - Sets creator as project owner
    - Adds creator as project member
    - Activates the project

    Args:
        request: FastAPI Request (for X-Organization-ID header)
        project_in: Project creation data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created project

    Note:
        - Requires X-Organization-ID header
        - User must be organization member
    """
    organization_id = UUID(current_user["organization_id"])
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    return await project_service.create_project(
        organization_id=organization_id,
        name=project_in.name,
        created_by=user_id,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get project details.

    Args:
        project_id: Project UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Project details

    Raises:
        HTTPException: 404 if project not found, 403 if not project member

    Note:
        - User must be project member to view details
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view project",
        )

    return await project_service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Update project information.

    Args:
        project_id: Project UUID
        project_update: Project update data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: 404 if not found, 403 if not owner or org admin

    Note:
        - Only project owner or organization admin can update
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    return await project_service.update_project(
        project_id=project_id,
        name=project_update.name,
        user_id=user_id,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_project(
    project_id: UUID,
    archive_request: ProjectArchiveRequest,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Archive a project (soft delete).

    Args:
        project_id: Project UUID
        archive_request: Archive reason
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 404 if not found, 403 if not owner or org admin

    Note:
        - Only project owner or organization admin can archive
        - This is a soft delete (archive record created)
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    await project_service.archive_project(
        project_id=project_id,
        user_id=user_id,
        reason=archive_request.reason,
    )


# Owner management endpoints


@router.get("/{project_id}/owner", response_model=ProjectOwnerResponse)
async def get_project_owner(
    project_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get project owner information.

    Args:
        project_id: Project UUID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Owner information

    Raises:
        HTTPException: 404 if project or owner not found, 403 if not member

    Note:
        - User must be project member to view owner
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view owner",
        )

    return await project_service.get_owner(project_id)


@router.put("/{project_id}/owner", response_model=ProjectOwnerResponse)
async def transfer_project_ownership(
    project_id: UUID,
    owner_update: ProjectOwnerUpdate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Transfer project ownership to another user.

    Automatically adds new owner as member if not already.

    Args:
        project_id: Project UUID
        owner_update: New owner user ID
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        New owner information

    Raises:
        HTTPException: 404 if not found, 403 if not current owner or org admin

    Note:
        - Only current owner or organization admin can transfer
        - New owner must be organization member
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    return await project_service.transfer_ownership(
        project_id=project_id,
        new_owner_id=owner_update.user_id,
        current_user_id=user_id,
    )


# Member management endpoints


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(
    project_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of project members.

    Args:
        project_id: Project UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of members

    Raises:
        HTTPException: 403 if not project member

    Note:
        - User must be project member to view members
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to view members",
        )

    return await project_service.list_members(
        project_id=project_id,
        page=page,
        page_size=min(page_size, 100),
    )


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    member_create: ProjectMemberCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Add a member to the project.

    Args:
        project_id: Project UUID
        member_create: User ID to add
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created member record

    Raises:
        HTTPException: 403 if not owner or org admin, 400 if user not org member

    Note:
        - Only project owner or organization admin can add members
        - User to add must be organization member
    """
    user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    return await project_service.add_member(
        project_id=project_id,
        user_id=member_create.user_id,
        current_user_id=user_id,
    )


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Remove a member from the project.

    Cannot remove the project owner.

    Args:
        project_id: Project UUID
        user_id: User UUID to remove
        current_user: Current authenticated user (from JWT)
        db: Database session

    Raises:
        HTTPException: 403 if not owner or org admin, 400 if trying to remove owner

    Note:
        - Only project owner or organization admin can remove members
        - Cannot remove project owner (transfer ownership first)
    """
    current_user_id = UUID(current_user["id"])
    project_service = ProjectService(db)

    await project_service.remove_member(
        project_id=project_id,
        user_id=user_id,
        current_user_id=current_user_id,
    )


# Agent endpoints (project-scoped)


@router.get("/{project_id}/agents", response_model=AgentListResponse)
async def list_agents(
    project_id: UUID,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
    is_archived: bool | None = None,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get list of agents in a project.

    Args:
        project_id: Project UUID
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        is_active: Filter by active status
        is_archived: Filter by archived status
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Paginated list of agents

    Note:
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to list agents",
        )

    return await agent_service.list_agents(
        project_id=project_id,
        page=page,
        page_size=min(page_size, 100),
        is_active=is_active,
        is_archived=is_archived,
    )


@router.post(
    "/{project_id}/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    project_id: UUID,
    agent_in: AgentCreate,
    current_user: dict = Depends(require_organization_member),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Create a new agent.

    Automatically:
    - Sets organization_id from project
    - Activates the agent

    Args:
        project_id: Project UUID
        agent_in: Agent creation data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created agent

    Note:
        - User must be project member
    """
    user_id = UUID(current_user["id"])
    agent_service = AgentService(db)
    member_repo = ProjectMemberRepository(db)

    # Verify user is project member
    is_member = await member_repo.is_member(project_id, user_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be project member to create agent",
        )

    # Ensure project_id matches
    if str(agent_in.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in body must match URL parameter",
        )

    return await agent_service.create_agent(
        name=agent_in.name, project_id=project_id, created_by=user_id
    )


# Guardrail endpoints (project-scoped)


@router.get("/{project_id}/guardrails", response_model=GuardrailListResponse)
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
    "/{project_id}/guardrails",
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

    Args:
        project_id: Project UUID
        guardrail_in: Guardrail creation data
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Created guardrail

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
            detail="User must be project member to create guardrail",
        )

    # Ensure project_id matches
    if str(guardrail_in.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in body must match URL parameter",
        )

    return await guardrail_service.create_guardrail(
        name=guardrail_in.name,
        definition=guardrail_in.definition,
        project_id=project_id,
        created_by=user_id,
    )
