from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_async_db
from app.core.security import decode_access_token, verify_api_key_hash, extract_key_prefix
from app.core.multi_tenant import extract_organization_id_from_header
from app.repositories.user_repository import UserRepository
from app.repositories.user_status_repository import UserStatusRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.services.permission_service import PermissionService
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


class TokenData(BaseModel):
    user_id: Optional[str] = None
    organization_id: Optional[str] = None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header
        db: Async database session

    Returns:
        Dict containing user data (user_id only)

    Raises:
        HTTPException: 401 if credentials invalid or user not found

    Note:
        - Validates JWT token and extracts user_id
        - Does NOT validate organization context (use X-Organization-ID header)
        - Does NOT check if user is active (use get_current_active_user for that)
        - Organization context is managed separately via X-Organization-ID header
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token (only contains user_id)
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

    # Get user from database
    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_id(UUID(user_id))

    if db_user is None:
        raise credentials_exception

    # Return user data (no organization context)
    return {
        "id": str(db_user.id),
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Get current authenticated user and verify they are active.

    Args:
        current_user: User dict from get_current_user()
        db: Async database session

    Returns:
        User dict (same as input if active)

    Raises:
        HTTPException: 403 if user is not active

    Note:
        - Checks user_active_status table for active status
        - Use this dependency for endpoints that require active users
        - Does not check organization active status
    """
    status_repo = UserStatusRepository(db)
    is_active = await status_repo.is_active(UUID(current_user["id"]))

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )

    return current_user


async def get_current_user_with_org(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Get current user with full profile and organization information.

    Args:
        request: FastAPI Request object (for extracting X-Organization-ID header)
        current_user: User dict from get_current_user()
        db: Async database session

    Returns:
        Dict with user, profile, and organization data

    Example:
        >>> @app.get("/me")
        >>> async def get_me(user_with_org = Depends(get_current_user_with_org)):
        ...     return user_with_org

    Note:
        - Includes user profile if exists
        - Organization context from X-Organization-ID header
        - Use when you need full user context
    """
    user_repo = UserRepository(db)
    user_with_profile = await user_repo.get_with_profile(UUID(current_user["id"]))

    if user_with_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user_with_profile


async def require_organization_member(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Require user to be a member of the organization.

    Args:
        request: FastAPI Request object (for extracting X-Organization-ID header)
        current_user: User dict from get_current_user()
        db: Async database session

    Returns:
        User dict with organization_id added

    Raises:
        HTTPException: 400 if organization context missing, 403 if user is not a member

    Note:
        - Extracts organization ID from X-Organization-ID header
        - Validates organization membership
        - Use as FastAPI dependency in endpoints requiring member access
    """
    # Get organization ID from header
    organization_id = extract_organization_id_from_header(request)
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required for this operation",
        )

    # Validate membership
    permission_service = PermissionService(db)
    is_member = await permission_service.is_member_or_above(
        organization_id=organization_id,
        user_id=UUID(current_user["id"]),
    )

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this organization",
        )

    # Return user with organization context
    return {
        **current_user,
        "organization_id": str(organization_id),
    }


async def require_organization_admin(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Require user to be an admin of the organization.

    Args:
        request: FastAPI Request object (for extracting X-Organization-ID header)
        current_user: User dict from get_current_user()
        db: Async database session

    Returns:
        User dict with organization_id added

    Raises:
        HTTPException: 400 if organization context missing, 403 if user is not an admin

    Note:
        - Extracts organization ID from X-Organization-ID header
        - Validates admin privileges
        - Use as FastAPI dependency in endpoints requiring admin access
        - Owners are also considered admins
    """
    # Get organization ID from header
    organization_id = extract_organization_id_from_header(request)
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required for this operation",
        )

    # Validate admin privileges
    permission_service = PermissionService(db)
    is_admin = await permission_service.is_admin_or_owner(
        user_id=UUID(current_user["id"]),
        organization_id=organization_id,
    )

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this operation",
        )

    # Return user with organization context
    return {
        **current_user,
        "organization_id": str(organization_id),
    }


async def require_organization_owner(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """
    Require user to be the owner of the organization.

    Args:
        request: FastAPI Request object (for extracting X-Organization-ID header)
        current_user: User dict from get_current_user()
        db: Async database session

    Returns:
        User dict with organization_id added

    Raises:
        HTTPException: 400 if organization context missing, 403 if user is not the owner

    Note:
        - Extracts organization ID from X-Organization-ID header
        - Validates ownership
        - Use as FastAPI dependency in endpoints requiring owner access
        - Strictest permission level (only one owner per organization)
    """
    # Get organization ID from header
    organization_id = extract_organization_id_from_header(request)
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-ID header is required for this operation",
        )

    # Validate ownership
    permission_service = PermissionService(db)
    is_owner = await permission_service.is_organization_owner(
        user_id=UUID(current_user["id"]),
        organization_id=organization_id,
    )

    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization owner privileges required for this operation",
        )

    # Return user with organization context
    return {
        **current_user,
        "organization_id": str(organization_id),
    }


async def get_current_agent_from_api_key(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Authenticate and get agent information from API key.

    Args:
        token: API key from Authorization header (Bearer {api_key})
        db: Async database session

    Returns:
        Dict containing agent context:
            - agent_id: Agent UUID
            - project_id: Project UUID
            - organization_id: Organization UUID
            - api_key_id: API Key UUID

    Raises:
        HTTPException: 401 if API key is invalid, expired, or agent not found

    Example:
        >>> @app.post("/traces")
        >>> async def create_trace(agent = Depends(get_current_agent_from_api_key)):
        ...     # agent contains agent_id, project_id, organization_id
        ...     return {"agent_id": agent["agent_id"]}

    Note:
        - API key format: "agt_live_{random_32_chars}"
        - Uses key_prefix (first 16 chars) for fast lookup
        - Verifies full key with bcrypt hash comparison
        - Updates last_used_at timestamp on successful authentication
        - Checks expiration date (expires_at field)
        - Returns agent context for authorization checks
    """
    from sqlalchemy import select, update
    from app.models.agent import AgentAPIKey, Agent

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract key prefix for fast lookup (first 16 characters)
        key_prefix = extract_key_prefix(token, prefix_length=16)

        # Find API key by prefix
        stmt = (
            select(AgentAPIKey, Agent)
            .join(Agent, AgentAPIKey.agent_id == Agent.id)
            .where(AgentAPIKey.key_prefix == key_prefix)
        )
        result = await db.execute(stmt)
        row = result.first()

        if row is None:
            raise credentials_exception

        api_key_record, agent = row

        # Verify full API key with bcrypt hash
        if not verify_api_key_hash(token, api_key_record.key_hash):
            raise credentials_exception

        # Check expiration
        if api_key_record.expires_at is not None:
            if datetime.utcnow() > api_key_record.expires_at.replace(tzinfo=None):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Update last_used_at timestamp
        update_stmt = (
            update(AgentAPIKey)
            .where(AgentAPIKey.id == api_key_record.id)
            .values(last_used_at=datetime.utcnow())
        )
        await db.execute(update_stmt)
        await db.commit()

        # Return agent context
        return {
            "agent_id": str(agent.id),
            "project_id": str(agent.project_id),
            "organization_id": str(agent.organization_id),
            "api_key_id": str(api_key_record.id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise credentials_exception


async def get_current_user_or_agent(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Authenticate with either JWT token or API key.

    Attempts JWT authentication first, then falls back to API key authentication.
    Use this dependency for endpoints that accept both user and agent authentication.

    Args:
        token: JWT token or API key from Authorization header
        db: Async database session

    Returns:
        Dict containing either user context or agent context:
            - User: {"id": user_id, "created_at": ..., "type": "user"}
            - Agent: {"agent_id": ..., "project_id": ..., "organization_id": ..., "type": "agent"}

    Raises:
        HTTPException: 401 if both authentication methods fail

    Example:
        >>> @app.get("/traces/{trace_id}")
        >>> async def get_trace(
        ...     trace_id: UUID,
        ...     current_user_or_agent = Depends(get_current_user_or_agent)
        ... ):
        ...     if current_user_or_agent.get("type") == "user":
        ...         # Handle user authentication
        ...         user_id = current_user_or_agent["id"]
        ...     else:
        ...         # Handle agent authentication
        ...         agent_id = current_user_or_agent["agent_id"]

    Note:
        - JWT tokens are checked first (more common)
        - API keys are checked if JWT validation fails
        - Response includes "type" field to distinguish authentication method
        - Use for read endpoints that allow both users and agents
    """
    # Try JWT authentication first
    try:
        user = await get_current_user(token=token, db=db)
        return {**user, "type": "user"}
    except HTTPException:
        pass

    # Try API key authentication
    try:
        agent = await get_current_agent_from_api_key(token=token, db=db)
        return {**agent, "type": "agent"}
    except HTTPException:
        pass

    # Both failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials (JWT or API key)",
        headers={"WWW-Authenticate": "Bearer"},
    )
