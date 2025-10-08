"""
Service test utilities and helpers.

This module provides helper functions for setting up services with mocks,
assertion utilities, and test data generation.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

# ============================================================================
# UUID Generation Helpers
# ============================================================================


def generate_test_uuid() -> UUID:
    """
    Generate a random UUID for testing.

    Returns:
        UUID: Random UUID
    """
    return uuid4()


def generate_consistent_uuid(seed: str) -> UUID:
    """
    Generate a consistent UUID from a seed string.

    Useful for tests that need predictable UUIDs.

    Args:
        seed: Seed string to generate UUID from

    Returns:
        UUID: Consistent UUID based on seed

    Example:
        >>> user_id = generate_consistent_uuid("user1")
        >>> # Always returns same UUID for "user1"
    """
    # Use namespace UUID for consistent generation
    import hashlib

    hash_digest = hashlib.md5(seed.encode()).hexdigest()
    return UUID(hash_digest)


# ============================================================================
# Test Data Factories (Task 0.6)
# ============================================================================


class UserDataFactory:
    """
    Factory for creating test user data.

    Provides consistent test data for user-related tests.
    """

    @staticmethod
    def build(
        user_id: UUID | None = None,
        email: str | None = None,
        name: str | None = None,
        **overrides,
    ) -> dict[str, Any]:
        """
        Build test user data dictionary.

        Args:
            user_id: User UUID (auto-generated if not provided)
            email: User email (auto-generated if not provided)
            name: User name (auto-generated if not provided)
            **overrides: Override default values

        Returns:
            Dict with user data

        Example:
            >>> data = UserDataFactory.build(email="test@example.com")
            >>> assert data["email"] == "test@example.com"
        """
        if user_id is None:
            user_id = uuid4()
        if email is None:
            email = f"user{user_id.hex[:8]}@test.com"
        if name is None:
            name = f"Test User {user_id.hex[:8]}"

        data = {
            "id": user_id,
            "email": email,
            "name": name,
            "bio": f"Bio for {name}",
            "avatar_url": f"https://example.com/avatar/{user_id.hex[:8]}.png",
            "password": "Test123!@#",
            "hashed_password": "hashed_Test123!@#",
            "is_active": True,
            "is_suspended": False,
            "is_archived": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        data.update(overrides)
        return data


class OrganizationDataFactory:
    """
    Factory for creating test organization data.

    Provides consistent test data for organization-related tests.
    """

    @staticmethod
    def build(
        org_id: UUID | None = None,
        name: str | None = None,
        **overrides,
    ) -> dict[str, Any]:
        """
        Build test organization data dictionary.

        Args:
            org_id: Organization UUID (auto-generated if not provided)
            name: Organization name (auto-generated if not provided)
            **overrides: Override default values

        Returns:
            Dict with organization data

        Example:
            >>> data = OrganizationDataFactory.build(name="Acme Corp")
            >>> assert data["name"] == "Acme Corp"
        """
        if org_id is None:
            org_id = uuid4()
        if name is None:
            name = f"Test Organization {org_id.hex[:8]}"

        data = {
            "id": org_id,
            "name": name,
            "slug": name.lower().replace(" ", "-"),
            "description": f"Description for {name}",
            "website_url": "https://example.com",
            "logo_url": f"https://example.com/logo/{org_id.hex[:8]}.png",
            "is_active": True,
            "is_suspended": False,
            "is_archived": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        data.update(overrides)
        return data


class MembershipDataFactory:
    """
    Factory for creating test membership data.

    Provides consistent test data for membership-related tests.
    """

    @staticmethod
    def build(
        user_id: UUID,
        organization_id: UUID,
        is_owner: bool = False,
        is_admin: bool = False,
        **overrides,
    ) -> dict[str, Any]:
        """
        Build test membership data dictionary.

        Args:
            user_id: User UUID (required)
            organization_id: Organization UUID (required)
            is_owner: Is user an owner
            is_admin: Is user an admin
            **overrides: Override default values

        Returns:
            Dict with membership data

        Example:
            >>> data = MembershipDataFactory.build(user_id, org_id, is_owner=True)
            >>> assert data["is_owner"] is True
        """
        data = {
            "user_id": user_id,
            "organization_id": organization_id,
            "is_owner": is_owner,
            "is_admin": is_admin,
            "joined_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        data.update(overrides)
        return data


# ============================================================================
# Assertion Utilities
# ============================================================================


def assert_service_called_with(mock_service, method_name: str, **expected_kwargs):
    """
    Assert that a service method was called with expected arguments.

    Args:
        mock_service: Mocked service instance
        method_name: Name of the method to check
        **expected_kwargs: Expected keyword arguments

    Example:
        >>> assert_service_called_with(
        ...     mock_user_repo,
        ...     "create",
        ...     email="test@example.com"
        ... )
    """
    method = getattr(mock_service, method_name)
    assert method.called, f"{method_name} was not called"

    # Check if called with expected kwargs
    if expected_kwargs:
        call_args = method.call_args
        if call_args:
            _, actual_kwargs = call_args
            for key, expected_value in expected_kwargs.items():
                assert key in actual_kwargs, f"Expected kwarg '{key}' not found in call"
                assert actual_kwargs[key] == expected_value, (
                    f"Expected {key}={expected_value}, got {actual_kwargs[key]}"
                )


def assert_not_called(mock_service, method_name: str):
    """
    Assert that a service method was NOT called.

    Args:
        mock_service: Mocked service instance
        method_name: Name of the method to check

    Example:
        >>> assert_not_called(mock_user_repo, "delete")
    """
    method = getattr(mock_service, method_name)
    assert not method.called, f"{method_name} was unexpectedly called"


# ============================================================================
# Mock Data Builders for Responses
# ============================================================================


def build_mock_user_model(user_data: dict[str, Any]) -> AsyncMock:
    """
    Build a mock User model instance from test data.

    Args:
        user_data: User data dictionary

    Returns:
        AsyncMock: Mock User instance with data attributes
    """
    user = AsyncMock()
    user.id = user_data["id"]
    user.created_at = user_data.get("created_at", datetime.utcnow())
    user.updated_at = user_data.get("updated_at", datetime.utcnow())

    # Add profile if present
    if "name" in user_data:
        profile = AsyncMock()
        profile.name = user_data["name"]
        profile.bio = user_data.get("bio")
        profile.avatar_url = user_data.get("avatar_url")
        user.profile = profile

    # Add login_password if present
    if "email" in user_data:
        login_password = AsyncMock()
        login_password.email = user_data["email"]
        login_password.hashed_password = user_data.get(
            "hashed_password", "hashed_password"
        )
        user.login_password = login_password

    return user


def build_mock_organization_model(org_data: dict[str, Any]) -> AsyncMock:
    """
    Build a mock Organization model instance from test data.

    Args:
        org_data: Organization data dictionary

    Returns:
        AsyncMock: Mock Organization instance with data attributes
    """
    org = AsyncMock()
    org.id = org_data["id"]
    org.name = org_data["name"]
    org.created_at = org_data.get("created_at", datetime.utcnow())
    org.updated_at = org_data.get("updated_at", datetime.utcnow())

    # Add active_status if active
    if org_data.get("is_active", False):
        active_status = AsyncMock()
        active_status.organization_id = org_data["id"]
        org.active_status = active_status
    else:
        org.active_status = None

    return org
