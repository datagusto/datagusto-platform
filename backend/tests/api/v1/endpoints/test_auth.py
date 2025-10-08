"""
Authentication endpoint tests.

Tests for /auth/register, /auth/token, /auth/refresh, and /auth/me endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from tests.api.base import BaseControllerTest


class TestAuthEndpoints(BaseControllerTest):
    """Test cases for authentication endpoints."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.auth.AuthService")
    @patch("app.api.v1.endpoints.auth.settings.ENABLE_REGISTRATION", "true")
    async def test_register_success(
        self,
        mock_auth_service_class,
        async_client,
        test_user_data,
    ):
        """Test successful user registration."""
        # Mock AuthService
        mock_service = AsyncMock()
        mock_service.register_user.return_value = {
            "user_id": test_user_data["id"],
            "email": test_user_data["email"],
            "name": test_user_data["name"],
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer",
        }
        mock_auth_service_class.return_value = mock_service

        # Make request
        payload = {
            "email": test_user_data["email"],
            "password": "testpassword123",
            "name": test_user_data["name"],
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert "user_id" in data
        assert "email" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["email"] == test_user_data["email"]
        assert mock_service.register_user.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.auth.settings.ENABLE_REGISTRATION", "false")
    async def test_register_disabled(self, async_client):
        """Test registration when disabled via environment variable."""
        # Make request
        payload = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        }
        response = await async_client.post("/api/v1/auth/register", json=payload)

        # Assertions
        self._assert_error(
            response,
            expected_status=403,
            expected_detail="registration is temporarily disabled",
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.auth.AuthService")
    async def test_login_success(
        self,
        mock_auth_service_class,
        async_client,
        test_user_data,
    ):
        """Test successful user login."""
        # Mock AuthService
        mock_service = AsyncMock()
        mock_service.login_user.return_value = {
            "user_id": test_user_data["id"],
            "email": test_user_data["email"],
            "name": test_user_data["name"],
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer",
        }
        mock_auth_service_class.return_value = mock_service

        # Make request (OAuth2PasswordRequestForm uses form data)
        form_data = {
            "username": test_user_data["email"],
            "password": "testpassword123",
        }
        response = await async_client.post("/api/v1/auth/token", data=form_data)

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert mock_service.login_user.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.auth.AuthService")
    async def test_login_invalid_credentials(
        self,
        mock_auth_service_class,
        async_client,
    ):
        """Test login with invalid credentials."""
        # Mock AuthService to raise authentication error
        mock_service = AsyncMock()
        mock_service.login_user.side_effect = HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )
        mock_auth_service_class.return_value = mock_service

        # Make request
        form_data = {
            "username": "wrong@example.com",
            "password": "wrongpassword",
        }
        response = await async_client.post("/api/v1/auth/token", data=form_data)

        # Assertions
        self._assert_error(
            response,
            expected_status=401,
            expected_detail="Incorrect email or password",
        )
