"""
Repository test utilities and assertion helpers.

This module provides helper functions for verifying database state and
comparing objects in repository layer tests.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import (
    Organization,
    OrganizationActiveStatus,
    OrganizationAdmin,
    OrganizationMember,
    OrganizationOwner,
)
from app.models.user import User, UserActiveStatus, UserLoginPassword, UserProfile

# ============================================================================
# Assertion Utilities
# ============================================================================


def assert_user_matches(
    actual: User,
    expected_id: UUID | None = None,
    expected_email: str | None = None,
    expected_name: str | None = None,
) -> None:
    """
    Assert that user object matches expected values.

    Args:
        actual: User object to verify
        expected_id: Expected user ID
        expected_email: Expected email (from UserLoginPassword)
        expected_name: Expected name (from UserProfile)

    Raises:
        AssertionError: If user doesn't match expected values

    Example:
        >>> user = await user_repository.get_by_id_with_relations(user_id)
        >>> assert_user_matches(
        ...     user,
        ...     expected_id=user_id,
        ...     expected_email="test@example.com",
        ...     expected_name="Test User"
        ... )
    """
    if expected_id is not None:
        assert actual.id == expected_id, f"Expected ID {expected_id}, got {actual.id}"

    if expected_email is not None:
        assert actual.login_password is not None, (
            "User has no login_password relationship"
        )
        assert actual.login_password.email == expected_email, (
            f"Expected email {expected_email}, got {actual.login_password.email}"
        )

    if expected_name is not None:
        assert actual.profile is not None, "User has no profile relationship"
        assert actual.profile.name == expected_name, (
            f"Expected name {expected_name}, got {actual.profile.name}"
        )

    # Verify timestamps exist
    assert actual.created_at is not None, "User has no created_at timestamp"
    assert actual.updated_at is not None, "User has no updated_at timestamp"


def assert_organization_matches(
    actual: Organization,
    expected_id: UUID | None = None,
    expected_name: str | None = None,
    expected_active: bool | None = None,
) -> None:
    """
    Assert that organization object matches expected values.

    Args:
        actual: Organization object to verify
        expected_id: Expected organization ID
        expected_name: Expected organization name
        expected_active: Expected active status

    Raises:
        AssertionError: If organization doesn't match expected values

    Example:
        >>> org = await organization_repository.get_by_id_with_relations(org_id)
        >>> assert_organization_matches(
        ...     org,
        ...     expected_id=org_id,
        ...     expected_name="Test Org",
        ...     expected_active=True
        ... )
    """
    if expected_id is not None:
        assert actual.id == expected_id, f"Expected ID {expected_id}, got {actual.id}"

    if expected_name is not None:
        assert actual.name == expected_name, (
            f"Expected name {expected_name}, got {actual.name}"
        )

    if expected_active is not None:
        if expected_active:
            assert actual.active_status is not None, (
                "Expected organization to be active, but has no active_status"
            )
        else:
            assert actual.active_status is None, (
                "Expected organization to be inactive, but has active_status"
            )

    # Verify timestamps exist
    assert actual.created_at is not None, "Organization has no created_at timestamp"
    assert actual.updated_at is not None, "Organization has no updated_at timestamp"


async def assert_relationship_exists(
    session: AsyncSession,
    relationship_type: str,
    user_id: UUID | None = None,
    organization_id: UUID | None = None,
) -> None:
    """
    Assert that a database relationship exists.

    Args:
        session: Database session
        relationship_type: Type of relationship ("member", "owner", "admin")
        user_id: User UUID (required for membership checks)
        organization_id: Organization UUID (required for membership checks)

    Raises:
        AssertionError: If relationship doesn't exist
        ValueError: If invalid parameters provided

    Example:
        >>> await assert_relationship_exists(
        ...     session,
        ...     "member",
        ...     user_id=user.id,
        ...     organization_id=org.id
        ... )
        >>> await assert_relationship_exists(
        ...     session,
        ...     "owner",
        ...     user_id=user.id,
        ...     organization_id=org.id
        ... )
    """
    if relationship_type == "member":
        if user_id is None or organization_id is None:
            raise ValueError("user_id and organization_id required for member check")

        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()
        assert member is not None, (
            f"No membership found for user {user_id} in org {organization_id}"
        )

    elif relationship_type == "owner":
        if user_id is None or organization_id is None:
            raise ValueError("user_id and organization_id required for owner check")

        stmt = select(OrganizationOwner).where(
            OrganizationOwner.user_id == user_id,
            OrganizationOwner.organization_id == organization_id,
        )
        result = await session.execute(stmt)
        owner = result.scalar_one_or_none()
        assert owner is not None, (
            f"No ownership found for user {user_id} in org {organization_id}"
        )

    elif relationship_type == "admin":
        if user_id is None or organization_id is None:
            raise ValueError("user_id and organization_id required for admin check")

        stmt = select(OrganizationAdmin).where(
            OrganizationAdmin.user_id == user_id,
            OrganizationAdmin.organization_id == organization_id,
        )
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        assert admin is not None, (
            f"No admin role found for user {user_id} in org {organization_id}"
        )

    else:
        raise ValueError(
            f"Invalid relationship_type: {relationship_type}. "
            'Must be "member", "owner", or "admin"'
        )


# ============================================================================
# Database Query Helpers
# ============================================================================


async def query_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """
    Query user by ID directly from database.

    Args:
        session: Database session
        user_id: User UUID

    Returns:
        User or None if not found

    Example:
        >>> user = await query_user_by_id(session, user_id)
        >>> assert user is not None
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def query_organization_by_id(
    session: AsyncSession, org_id: UUID
) -> Organization | None:
    """
    Query organization by ID directly from database.

    Args:
        session: Database session
        org_id: Organization UUID

    Returns:
        Organization or None if not found

    Example:
        >>> org = await query_organization_by_id(session, org_id)
        >>> assert org is not None
    """
    stmt = select(Organization).where(Organization.id == org_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def count_users_in_organization(
    session: AsyncSession, organization_id: UUID
) -> int:
    """
    Count members in an organization.

    Args:
        session: Database session
        organization_id: Organization UUID

    Returns:
        Number of members

    Example:
        >>> count = await count_users_in_organization(session, org.id)
        >>> assert count == 3
    """
    stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == organization_id
    )
    result = await session.execute(stmt)
    members = result.scalars().all()
    return len(members)
