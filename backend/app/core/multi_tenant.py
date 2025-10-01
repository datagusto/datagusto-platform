"""
Multi-tenant organization context management.

This module provides utilities for managing organization context in a multi-tenant
architecture. It handles setting and extracting organization IDs for Row Level
Security (RLS) policies and request isolation.
"""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.security import decode_access_token


async def set_organization_context(db: AsyncSession, organization_id: UUID) -> None:
    """
    Set the current organization ID for PostgreSQL Row Level Security policies.

    This function sets a session-local variable in PostgreSQL that can be used
    by RLS policies to filter data by organization. The setting only persists
    for the duration of the current transaction.

    Args:
        db: Active async database session
        organization_id: UUID of the organization to set as current context

    Raises:
        Exception: If the database operation fails

    Example:
        >>> async with AsyncSessionLocal() as session:
        ...     await set_organization_context(session, org_id)
        ...     # All subsequent queries will be filtered by org_id
        ...     users = await session.execute(select(User))

    Note:
        - Uses SET LOCAL to ensure the setting is transaction-scoped
        - RLS policies can reference this with current_setting('app.current_org_id')
        - The setting is automatically cleared at transaction end
    """
    try:
        await db.execute(
            text("SET LOCAL app.current_org_id = :org_id"),
            {"org_id": str(organization_id)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set organization context: {str(e)}",
        )


def extract_organization_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract organization ID from JWT token.

    Decodes the JWT token and extracts the organization_id claim. This is the
    primary method for determining which organization context to use for a request.

    Args:
        token: JWT access token string

    Returns:
        UUID of the organization, or None if not present in token

    Raises:
        HTTPException: If token is invalid or expired

    Example:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> org_id = extract_organization_id_from_token(token)
        >>> print(org_id)
        UUID('123e4567-e89b-12d3-a456-426614174000')

    Note:
        - Token must contain 'organization_id' claim
        - Token expiration is checked by decode_access_token()
        - Returns None if organization_id claim is missing (not an error)
    """
    try:
        payload = decode_access_token(token)
        org_id_str = payload.get("organization_id")

        if org_id_str is None:
            return None

        return UUID(org_id_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid organization ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate token: {str(e)}",
        )


def extract_organization_id_from_header(request: Request) -> Optional[UUID]:
    """
    Extract organization ID from HTTP header.

    Alternative method to extract organization context from X-Organization-ID header.
    This can be used when JWT token doesn't contain organization context, or for
    organization switching within the same session.

    Args:
        request: FastAPI Request object

    Returns:
        UUID of the organization, or None if header not present

    Raises:
        HTTPException: If header value is not a valid UUID

    Example:
        >>> # In FastAPI endpoint
        >>> @app.get("/resource")
        >>> async def get_resource(request: Request):
        ...     org_id = extract_organization_id_from_header(request)
        ...     # Use org_id for query filtering

    Note:
        - Header name: X-Organization-ID
        - Value must be a valid UUID string
        - Returns None if header is not present (not an error)
    """
    org_id_header = request.headers.get("X-Organization-ID")

    if org_id_header is None:
        return None

    try:
        return UUID(org_id_header)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-Organization-ID header format: {str(e)}",
        )


def extract_organization_id(
    request: Request, token: Optional[str] = None
) -> Optional[UUID]:
    """
    Extract organization ID from request using multiple strategies.

    Attempts to extract organization ID in the following order:
    1. From HTTP header (X-Organization-ID)
    2. From JWT token (organization_id claim)

    Args:
        request: FastAPI Request object
        token: Optional JWT token string. If not provided, tries to get from request state.

    Returns:
        UUID of the organization, or None if not found in any source

    Example:
        >>> @app.middleware("http")
        >>> async def org_middleware(request: Request, call_next):
        ...     org_id = extract_organization_id(request)
        ...     if org_id:
        ...         request.state.organization_id = org_id
        ...     return await call_next(request)

    Note:
        - Header takes precedence over token (for organization switching)
        - Returns None if organization ID not found (caller should handle)
        - Does not raise exceptions for missing organization ID
    """
    # Try header first (allows organization switching)
    org_id = extract_organization_id_from_header(request)
    if org_id is not None:
        return org_id

    # Try token
    if token is None:
        # Try to get token from request state (set by auth middleware)
        token = getattr(request.state, "token", None)

    if token is not None:
        return extract_organization_id_from_token(token)

    return None


def require_organization_context(organization_id: Optional[UUID]) -> UUID:
    """
    Ensure organization context is present, raise exception if not.

    This is a validation function that should be called in endpoints that require
    organization context. It converts Optional[UUID] to UUID, raising an error
    if the value is None.

    Args:
        organization_id: Optional organization ID to validate

    Returns:
        UUID of the organization (guaranteed not None)

    Raises:
        HTTPException: 400 Bad Request if organization_id is None

    Example:
        >>> @app.get("/organizations/{org_id}/users")
        >>> async def list_users(request: Request):
        ...     org_id = extract_organization_id(request)
        ...     org_id = require_organization_context(org_id)
        ...     # org_id is guaranteed to be UUID here

    Note:
        - Use this in endpoints that cannot function without organization context
        - Returns the same UUID if present, just removes Optional wrapper
        - HTTP 400 indicates client error (missing required context)
    """
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required for this operation. "
            "Please provide organization ID via X-Organization-ID header or JWT token.",
        )
    return organization_id


__all__ = [
    "set_organization_context",
    "extract_organization_id_from_token",
    "extract_organization_id_from_header",
    "extract_organization_id",
    "require_organization_context",
]
