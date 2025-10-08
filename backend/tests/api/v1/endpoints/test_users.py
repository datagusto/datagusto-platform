"""
User management endpoint tests.

Tests for user CRUD operations and profile management.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from tests.api.base import BaseControllerTest


class TestUserEndpoints(BaseControllerTest):
    """Test cases for user management endpoints."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.users.UserService")
    async def test_get_user_success(
        self,
        mock_user_service_class,
        authenticated_client,
        test_user_data,
        test_user_id,
    ):
        """Test successful user retrieval."""
        # Mock UserService
        mock_service = AsyncMock()
        mock_service.get_user.return_value = test_user_data
        mock_user_service_class.return_value = mock_service

        # Make request
        response = await authenticated_client.get(f"/api/v1/users/{test_user_id}")

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert data["id"] == test_user_data["id"]
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert mock_service.get_user.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.users.UserService")
    async def test_get_user_not_found(
        self,
        mock_user_service_class,
        authenticated_client,
        test_user_id,
    ):
        """Test user retrieval when user doesn't exist."""
        # Mock UserService to raise 404
        mock_service = AsyncMock()
        mock_service.get_user.side_effect = HTTPException(
            status_code=404,
            detail="User not found",
        )
        mock_user_service_class.return_value = mock_service

        # Make request
        response = await authenticated_client.get(f"/api/v1/users/{test_user_id}")

        # Assertions
        self._assert_error(
            response,
            expected_status=404,
            expected_detail="User not found",
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.users.UserService")
    async def test_update_profile_success(
        self,
        mock_user_service_class,
        authenticated_client,
        test_user_data,
        test_user_id,
        mock_current_user,
    ):
        """Test successful profile update."""
        # Ensure current user matches the user being updated
        assert mock_current_user["id"] == str(test_user_id)

        # Mock UserService
        updated_data = test_user_data.copy()
        updated_data["name"] = "Updated Name"
        updated_data["bio"] = "Updated bio"

        mock_service = AsyncMock()
        mock_service.update_profile.return_value = updated_data
        mock_user_service_class.return_value = mock_service

        # Make request
        payload = {
            "name": "Updated Name",
            "bio": "Updated bio",
        }
        response = await authenticated_client.patch(
            f"/api/v1/users/{test_user_id}/profile", json=payload
        )

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert data["name"] == "Updated Name"
        assert data["bio"] == "Updated bio"
        assert mock_service.update_profile.called

    @pytest.mark.asyncio
    async def test_update_profile_permission_denied(
        self,
        authenticated_client,
        test_user_data,
    ):
        """Test profile update with mismatched user ID (permission denied)."""
        # Try to update a different user's profile
        different_user_id = "87654321-8765-8765-8765-876543210fed"

        # Make request
        payload = {
            "name": "Hacker Name",
        }
        response = await authenticated_client.patch(
            f"/api/v1/users/{different_user_id}/profile", json=payload
        )

        # Assertions
        self._assert_error(
            response,
            expected_status=403,
            expected_detail="You can only update your own profile",
        )
