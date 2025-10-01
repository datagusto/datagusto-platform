"""
Repository-specific pytest fixtures.

This module provides fixtures for repository testing with PostgreSQL test database.
All fixtures use the test_db_session from parent conftest.py with transaction rollback.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.repositories.user_auth_repository import UserAuthRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_status_repository import UserStatusRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.organization_owner_repository import OrganizationOwnerRepository
from app.repositories.organization_admin_repository import OrganizationAdminRepository
from app.models.user import (
    User,
    UserProfile,
    UserLoginPassword,
    UserActiveStatus,
)
from app.models.organization import (
    Organization,
    OrganizationMember,
    OrganizationOwner,
    OrganizationAdmin,
    OrganizationActiveStatus,
)
from uuid import UUID, uuid4
from typing import Dict, Any
from datetime import datetime


# ============================================================================
# Test Data Builders
# ============================================================================


def build_user_data(user_id: UUID | None = None, **overrides) -> Dict[str, Any]:
    """
    Build valid user data dictionary for testing.

    Args:
        user_id: User UUID (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with user data

    Example:
        >>> data = build_user_data()
        >>> user = User(**data)
        >>> session.add(user)
    """
    if user_id is None:
        user_id = uuid4()

    data = {"id": user_id}
    data.update(overrides)
    return data


def build_profile_data(
    user_id: UUID, name: str | None = None, **overrides
) -> Dict[str, Any]:
    """
    Build valid user profile data dictionary for testing.

    Args:
        user_id: User UUID (required)
        name: User name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with profile data

    Example:
        >>> data = build_profile_data(user.id, name="John Doe")
        >>> profile = UserProfile(**data)
        >>> session.add(profile)
    """
    if name is None:
        name = f"Test User {user_id.hex[:8]}"

    data = {
        "user_id": user_id,
        "name": name,
        "bio": f"Bio for {name}",
        "avatar_url": f"https://example.com/avatar/{user_id.hex[:8]}.png",
    }
    data.update(overrides)
    return data


def build_user_auth_data(
    user_id: UUID, email: str | None = None, **overrides
) -> Dict[str, Any]:
    """
    Build valid user authentication data dictionary for testing.

    Args:
        user_id: User UUID (required)
        email: User email (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with auth data

    Example:
        >>> data = build_user_auth_data(user.id, email="test@example.com")
        >>> auth = UserLoginPassword(**data)
        >>> session.add(auth)
    """
    if email is None:
        email = f"user{user_id.hex[:8]}@test.com"

    data = {
        "user_id": user_id,
        "email": email,
        "hashed_password": "hashed_password_123",
    }
    data.update(overrides)
    return data


def build_organization_data(
    org_id: UUID | None = None, name: str | None = None, **overrides
) -> Dict[str, Any]:
    """
    Build valid organization data dictionary for testing.

    Args:
        org_id: Organization UUID (auto-generated if not provided)
        name: Organization name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with organization data

    Example:
        >>> data = build_organization_data(name="Acme Corp")
        >>> org = Organization(**data)
        >>> session.add(org)
    """
    if org_id is None:
        org_id = uuid4()
    if name is None:
        name = f"Test Organization {org_id.hex[:8]}"

    data = {"id": org_id, "name": name}
    data.update(overrides)
    return data


def build_membership_data(
    user_id: UUID, organization_id: UUID, **overrides
) -> Dict[str, Any]:
    """
    Build valid organization membership data dictionary for testing.

    Args:
        user_id: User UUID (required)
        organization_id: Organization UUID (required)
        **overrides: Override default values

    Returns:
        Dict with membership data

    Example:
        >>> data = build_membership_data(user.id, org.id)
        >>> member = OrganizationMember(**data)
        >>> session.add(member)
    """
    data = {
        "user_id": user_id,
        "organization_id": organization_id,
    }
    data.update(overrides)
    return data


# ============================================================================
# Database Seeding Utilities
# ============================================================================


async def seed_test_user(
    session: AsyncSession,
    user_id: UUID | None = None,
    email: str | None = None,
    name: str | None = None,
    password_hash: str = "hashed_password_123",
    with_profile: bool = True,
    with_auth: bool = True,
    with_active_status: bool = True,
) -> User:
    """
    Create a test user with optional related records.

    Args:
        session: Database session
        user_id: User UUID (auto-generated if not provided)
        email: User email (auto-generated if not provided)
        name: User name (auto-generated if not provided)
        password_hash: Password hash for auth record
        with_profile: Create UserProfile record
        with_auth: Create UserLoginPassword record
        with_active_status: Create UserActiveStatus record

    Returns:
        User: Created user with relations

    Example:
        >>> user = await seed_test_user(session, email="test@example.com")
        >>> assert user.profile.name is not None
        >>> assert user.login_password.email == "test@example.com"
    """
    if user_id is None:
        user_id = uuid4()
    if email is None:
        email = f"user{user_id.hex[:8]}@test.com"
    if name is None:
        name = f"Test User {user_id.hex[:8]}"

    # Create user
    user = User(id=user_id)
    session.add(user)
    await session.flush()

    # Create related records
    if with_profile:
        profile = UserProfile(user_id=user.id, name=name, bio=f"Bio for {name}")
        session.add(profile)

    if with_auth:
        login_password = UserLoginPassword(
            user_id=user.id, email=email, hashed_password=password_hash
        )
        session.add(login_password)

    if with_active_status:
        active_status = UserActiveStatus(user_id=user.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(user)
    return user


async def seed_test_organization(
    session: AsyncSession,
    org_id: UUID | None = None,
    name: str | None = None,
    with_active_status: bool = True,
) -> Organization:
    """
    Create a test organization with optional related records.

    Args:
        session: Database session
        org_id: Organization UUID (auto-generated if not provided)
        name: Organization name (auto-generated if not provided)
        with_active_status: Create OrganizationActiveStatus record

    Returns:
        Organization: Created organization with relations

    Example:
        >>> org = await seed_test_organization(session, name="Test Org")
        >>> assert org.name == "Test Org"
        >>> assert org.active_status is not None
    """
    if org_id is None:
        org_id = uuid4()
    if name is None:
        name = f"Test Organization {org_id.hex[:8]}"

    # Create organization
    org = Organization(id=org_id, name=name)
    session.add(org)
    await session.flush()

    # Create related records
    if with_active_status:
        active_status = OrganizationActiveStatus(organization_id=org.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(org)
    return org


async def seed_test_membership(
    session: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    is_owner: bool = False,
    is_admin: bool = False,
    granted_by: UUID | None = None,
) -> OrganizationMember:
    """
    Create a test membership between user and organization.

    Args:
        session: Database session
        user_id: User UUID
        organization_id: Organization UUID
        is_owner: Create OrganizationOwner record
        is_admin: Create OrganizationAdmin record
        granted_by: User who granted admin privilege (required if is_admin=True)

    Returns:
        OrganizationMember: Created membership record

    Example:
        >>> user = await seed_test_user(session)
        >>> org = await seed_test_organization(session)
        >>> member = await seed_test_membership(
        ...     session, user.id, org.id, is_owner=True
        ... )
    """
    # Create membership
    member = OrganizationMember(organization_id=organization_id, user_id=user_id)
    session.add(member)
    await session.flush()

    # Create role records
    if is_owner:
        owner = OrganizationOwner(organization_id=organization_id, user_id=user_id)
        session.add(owner)

    if is_admin:
        if granted_by is None:
            granted_by = user_id  # Default to self-granted for tests
        admin = OrganizationAdmin(
            organization_id=organization_id, user_id=user_id, granted_by=granted_by
        )
        session.add(admin)

    await session.flush()
    return member


# ============================================================================
# Repository Factory Fixtures
# ============================================================================


@pytest.fixture
def user_repository(test_db_session: AsyncSession) -> UserRepository:
    """
    UserRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserRepository: Repository instance for testing
    """
    return UserRepository(test_db_session)


@pytest.fixture
def user_auth_repository(test_db_session: AsyncSession) -> UserAuthRepository:
    """
    UserAuthRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserAuthRepository: Repository instance for testing
    """
    return UserAuthRepository(test_db_session)


@pytest.fixture
def user_profile_repository(test_db_session: AsyncSession) -> UserProfileRepository:
    """
    UserProfileRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserProfileRepository: Repository instance for testing
    """
    return UserProfileRepository(test_db_session)


@pytest.fixture
def user_status_repository(test_db_session: AsyncSession) -> UserStatusRepository:
    """
    UserStatusRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserStatusRepository: Repository instance for testing
    """
    return UserStatusRepository(test_db_session)


@pytest.fixture
def organization_repository(test_db_session: AsyncSession) -> OrganizationRepository:
    """
    OrganizationRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationRepository: Repository instance for testing
    """
    return OrganizationRepository(test_db_session)


@pytest.fixture
def organization_member_repository(
    test_db_session: AsyncSession,
) -> OrganizationMemberRepository:
    """
    OrganizationMemberRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationMemberRepository: Repository instance for testing
    """
    return OrganizationMemberRepository(test_db_session)


@pytest.fixture
def organization_owner_repository(
    test_db_session: AsyncSession,
) -> OrganizationOwnerRepository:
    """
    OrganizationOwnerRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationOwnerRepository: Repository instance for testing
    """
    return OrganizationOwnerRepository(test_db_session)


@pytest.fixture
def organization_admin_repository(
    test_db_session: AsyncSession,
) -> OrganizationAdminRepository:
    """
    OrganizationAdminRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationAdminRepository: Repository instance for testing
    """
    return OrganizationAdminRepository(test_db_session)