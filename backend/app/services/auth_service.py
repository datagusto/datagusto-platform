"""
Authentication service for user registration and login.

This service handles user authentication using the ultra-fine-grained
data model with separate tables for user identity, authentication,
profile, and status.
"""

from datetime import timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.organization_owner_repository import OrganizationOwnerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_auth_repository import UserAuthRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_status_repository import UserStatusRepository
from app.schemas.user import UserCreate


class AuthService:
    """Service for handling user authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the authentication service.

        Args:
            db: Async database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.auth_repo = UserAuthRepository(db)
        self.profile_repo = UserProfileRepository(db)
        self.status_repo = UserStatusRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.owner_repo = OrganizationOwnerRepository(db)
        self.member_repo = OrganizationMemberRepository(db)

    async def register_user(self, user_in: UserCreate) -> dict[str, Any]:
        """
        Register a new user with their own organization.

        This creates:
        1. New organization (user becomes owner)
        2. User record
        3. User authentication credentials
        4. User profile
        5. User active status
        6. Organization membership
        7. Organization ownership

        Args:
            user_in: User registration data

        Returns:
            Dictionary containing user data and tokens

        Raises:
            HTTPException: If registration fails or email already exists
        """
        try:
            # Check if email already exists
            if await self.auth_repo.email_exists(user_in.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

            # Create organization for the user
            organization = await self.org_repo.create(
                {"name": user_in.organization_name or f"{user_in.name}'s Organization"}
            )

            # Activate organization
            await self.org_repo.activate(organization.id)

            # Create user
            user_id = uuid4()
            user = await self.user_repo.create({"id": user_id})

            # Create authentication credentials
            hashed_password = get_password_hash(user_in.password)
            await self.auth_repo.create_password_auth(
                user_id=user.id, email=user_in.email, hashed_password=hashed_password
            )

            # Create user profile
            await self.profile_repo.create_profile(
                user_id=user.id, profile_data={"name": user_in.name}
            )

            # Activate user
            await self.status_repo.activate(user.id)

            # Add user as organization member
            await self.member_repo.add_member(
                organization_id=organization.id, user_id=user.id
            )

            # Set user as organization owner
            await self.owner_repo.set_owner(
                organization_id=organization.id, user_id=user.id
            )

            # Commit transaction
            await self.db.commit()

            # Generate tokens (user authentication only, no org_id)
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=access_token_expires,
            )

            refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = create_refresh_token(
                data={"sub": str(user.id)},
                expires_delta=refresh_token_expires,
            )

            return {
                "user_id": str(user.id),
                "email": user_in.email,
                "name": user_in.name,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except HTTPException:
            await self.db.rollback()
            raise
        except IntegrityError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}",
            )
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}",
            )

    async def login_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate user with email and password.

        Args:
            email: User email address
            password: Plain text password

        Returns:
            Dictionary containing access tokens and user info

        Raises:
            HTTPException: If authentication fails or user is inactive
        """
        # Get user by email with all relations
        user = await self.user_repo.get_by_email_with_relations(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not await self.status_repo.is_active(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        # Check if user is archived
        if await self.status_repo.is_archived(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is archived",
            )

        # Verify password
        if not user.login_password or not verify_password(
            password, user.login_password.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user's first organization for initial setup
        organizations = await self.member_repo.list_organizations_for_user(
            user_id=user.id, limit=1
        )
        if not organizations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of any organization",
            )

        # Use the first organization for response (frontend will use this as initial org)
        first_organization = organizations[0]

        # Check if organization is active
        if not await self.org_repo.is_active(first_organization.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is not active",
            )

        # Create access token (user authentication only, no org_id)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )

        # Create refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_token_expires,
        )

        return {
            "user_id": str(user.id),
            "email": email,
            "name": user.profile.name if user.profile else None,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
