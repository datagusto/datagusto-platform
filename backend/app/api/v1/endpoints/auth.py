"""
Authentication API endpoints.

This module provides endpoints for user registration, login, token refresh,
and current user information retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Any
from datetime import timedelta
import os

from app.core.database import get_async_db
from app.core.auth import get_current_user
from app.schemas.user import UserCreate, User, UserAuth, UserOrganizationList
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.permission_service import PermissionService
from app.core.security import (
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from uuid import UUID

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


@router.post("/register", response_model=UserAuth)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Register a new user.

    Creates a new user account with their own organization.
    The user becomes the owner of the newly created organization.

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        User data with authentication tokens

    Raises:
        HTTPException: If registration is disabled or fails
    """
    enable_registration = os.getenv("ENABLE_REGISTRATION", "false").lower() == "true"

    if not enable_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="New user registration is temporarily disabled.",
        )

    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)


@router.post("/token", response_model=UserAuth)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    """
    Login with email and password to get JWT token.

    Args:
        form_data: OAuth2 password request form (username is email)
        db: Database session

    Returns:
        Authentication tokens and user data

    Raises:
        HTTPException: If authentication fails
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(form_data.username, form_data.password)


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)
) -> dict[str, str]:
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access token with same organization context

    Raises:
        HTTPException: If refresh token is invalid or user no longer has access

    Note:
        - Validates organization access on refresh
        - Organization context persists from original token
    """
    try:
        # Decode refresh token
        payload = decode_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        organization_id = payload.get("organization_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing organization context",
            )

        # Validate user still has access to organization
        permission_service = PermissionService(db)
        has_access = await permission_service.is_organization_member(
            user_id=UUID(user_id), organization_id=UUID(organization_id)
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User no longer has access to this organization",
            )

        # Create new access token with same organization context
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "organization_id": organization_id},
            expires_delta=access_token_expires,
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    user_service = UserService(db)
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return await user_service.get_user(UUID(user_id))


@router.get("/me/organizations", response_model=UserOrganizationList)
async def get_user_organizations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """
    Get list of organizations that current user belongs to.

    This endpoint is used by the frontend to populate the organization
    switcher dropdown and manage organization context.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        List of organizations with membership details

    Raises:
        HTTPException: If user not found

    Example Response:
        {
          "organizations": [
            {
              "id": "uuid",
              "name": "Acme Corp",
              "role": "owner",
              "joined_at": "2024-01-01T00:00:00Z"
            }
          ]
        }
    """
    user_service = UserService(db)
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    organizations = await user_service.get_user_organizations(UUID(user_id))
    return {"organizations": organizations}
