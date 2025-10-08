"""
Test utility functions for controller layer tests.

This module provides helper functions for assertions, mock data creation,
and common test operations.
"""

from typing import Any
from uuid import UUID, uuid4

from httpx import Response


def assert_response_success(response: Response, expected_status: int = 200) -> None:
    """
    Validate successful response structure.

    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code (default: 200)

    Raises:
        AssertionError: If response doesn't match expected structure
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )
    assert response.headers.get("content-type") == "application/json"


def assert_response_error(
    response: Response, expected_status: int, expected_detail: str = None
) -> None:
    """
    Validate error response structure.

    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code
        expected_detail: Expected error detail message (optional)

    Raises:
        AssertionError: If response doesn't match expected error structure
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()
    assert "detail" in data, "Error response should contain 'detail' field"

    if expected_detail:
        assert expected_detail in data["detail"], (
            f"Expected detail to contain '{expected_detail}', got '{data['detail']}'"
        )


def assert_permission_error(response: Response, expected_message: str = None) -> None:
    """
    Validate 403 permission denied response.

    Args:
        response: HTTP response object
        expected_message: Expected error message substring (optional)

    Raises:
        AssertionError: If response is not a 403 permission error
    """
    assert_response_error(response, 403, expected_message)


def create_mock_user(
    user_id: UUID = None,
    organization_id: UUID = None,
    email: str = "test@example.com",
    name: str = "Test User",
    **kwargs,
) -> dict[str, Any]:
    """
    Factory function for creating mock user data.

    Args:
        user_id: User UUID (generates new if not provided)
        organization_id: Organization UUID (generates new if not provided)
        email: User email
        name: User display name
        **kwargs: Additional user fields

    Returns:
        Dictionary containing user data
    """
    user_id = user_id or uuid4()
    organization_id = organization_id or uuid4()

    user_data = {
        "id": str(user_id),
        "organization_id": str(organization_id),
        "email": email,
        "name": name,
        "bio": kwargs.get("bio"),
        "avatar_url": kwargs.get("avatar_url"),
        "is_active": kwargs.get("is_active", True),
        "is_suspended": kwargs.get("is_suspended", False),
        "is_archived": kwargs.get("is_archived", False),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00"),
    }

    # Remove None values
    return {k: v for k, v in user_data.items() if v is not None}


def create_mock_organization(
    organization_id: UUID = None,
    name: str = "Test Organization",
    slug: str = "test-org",
    **kwargs,
) -> dict[str, Any]:
    """
    Factory function for creating mock organization data.

    Args:
        organization_id: Organization UUID (generates new if not provided)
        name: Organization name
        slug: URL-friendly slug
        **kwargs: Additional organization fields

    Returns:
        Dictionary containing organization data
    """
    organization_id = organization_id or uuid4()

    org_data = {
        "id": str(organization_id),
        "name": name,
        "slug": slug,
        "description": kwargs.get("description"),
        "website_url": kwargs.get("website_url"),
        "logo_url": kwargs.get("logo_url"),
        "is_active": kwargs.get("is_active", True),
        "is_suspended": kwargs.get("is_suspended", False),
        "is_archived": kwargs.get("is_archived", False),
        "created_at": kwargs.get("created_at", "2024-01-01T00:00:00"),
        "updated_at": kwargs.get("updated_at", "2024-01-01T00:00:00"),
    }

    # Remove None values
    return {k: v for k, v in org_data.items() if v is not None}


def assert_user_response(
    response_data: dict[str, Any], expected_user: dict[str, Any]
) -> None:
    """
    Assert that response data matches expected user structure.

    Args:
        response_data: Response data from API
        expected_user: Expected user data

    Raises:
        AssertionError: If response doesn't match expected user
    """
    assert "id" in response_data
    assert "organization_id" in response_data

    if "email" in expected_user:
        assert response_data["email"] == expected_user["email"]

    if "name" in expected_user:
        assert response_data["name"] == expected_user["name"]


def assert_organization_response(
    response_data: dict[str, Any], expected_org: dict[str, Any]
) -> None:
    """
    Assert that response data matches expected organization structure.

    Args:
        response_data: Response data from API
        expected_org: Expected organization data

    Raises:
        AssertionError: If response doesn't match expected organization
    """
    assert "id" in response_data
    assert "name" in response_data

    if "name" in expected_org:
        assert response_data["name"] == expected_org["name"]

    if "slug" in expected_org:
        assert response_data["slug"] == expected_org["slug"]
