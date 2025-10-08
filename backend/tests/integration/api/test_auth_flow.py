"""
Authentication flow integration tests.

Tests complete authentication workflows end-to-end with real database.
Uses standard FastAPI testing patterns with AsyncClient.
"""

from uuid import UUID

import pytest

# Mark all tests as integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


# ============================================================================
# Test: Complete Registration Flow
# ============================================================================


async def test_register_user_success(integration_client):
    """
    Test user registration returns tokens and user data.

    Verifies:
    - API returns 200 with user data
    - Tokens are generated
    - Email and name are correct
    """
    # Arrange
    registration_data = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "name": "New Test User",
        "organization_name": "New Test Organization",
    }

    # Act
    response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "user_id" in data
    assert data["email"] == registration_data["email"]
    assert data["name"] == registration_data["name"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# ============================================================================
# Test: Registration → Login Flow
# ============================================================================


async def test_register_then_login_success(integration_client):
    """
    Test complete registration → login flow.

    Verifies:
    - User can register
    - Same credentials work for login
    - Login returns valid tokens
    """
    # Arrange - Register user
    registration_data = {
        "email": "logintest@example.com",
        "password": "LoginPassword123!",
        "name": "Login Test User",
        "organization_name": "Login Test Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    register_data = register_response.json()

    # Act - Login with same credentials
    login_response = await integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": registration_data["email"],
            "password": registration_data["password"],
        },
    )

    # Assert
    assert login_response.status_code == 200
    login_data = login_response.json()

    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["token_type"] == "bearer"

    # Verify tokens are JWT format (3 parts)
    assert login_data["access_token"].count(".") == 2
    assert login_data["refresh_token"].count(".") == 2

    # Verify user ID matches
    assert login_data["user_id"] == register_data["user_id"]


# ============================================================================
# Test: Authenticated Request with Real Token
# ============================================================================


async def test_authenticated_request_with_token(integration_client):
    """
    Test making authenticated API request with real JWT token.

    Verifies:
    - Access token works for protected endpoints
    - Correct user data returned
    - Token validation working end-to-end
    """
    # Arrange - Register and login
    registration_data = {
        "email": "authtest@example.com",
        "password": "AuthTest123!",
        "name": "Auth Test User",
        "organization_name": "Auth Test Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    user_data = register_response.json()

    login_response = await integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": registration_data["email"],
            "password": registration_data["password"],
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Act - Make authenticated request
    response = await integration_client.get(
        f"/api/v1/users/{user_data['user_id']}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    # Assert
    assert response.status_code == 200
    user_info = response.json()

    assert user_info["id"] == user_data["user_id"]
    assert user_info["email"] == registration_data["email"]
    assert user_info["name"] == registration_data["name"]
    assert user_info["is_active"] is True


# ============================================================================
# Test: Registration with Duplicate Email
# ============================================================================


async def test_register_duplicate_email_fails(integration_client):
    """
    Test that registration with duplicate email fails.

    Verifies:
    - First registration succeeds
    - Second registration with same email returns 400
    - Error message indicates email already registered
    """
    # Arrange - Register first user
    first_registration = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "name": "First User",
        "organization_name": "First Org",
    }

    response1 = await integration_client.post(
        "/api/v1/auth/register", json=first_registration
    )
    assert response1.status_code == 200

    # Act - Try to register with same email
    second_registration = {
        "email": "duplicate@example.com",
        "password": "DifferentPassword123!",
        "name": "Second User",
        "organization_name": "Second Org",
    }

    response2 = await integration_client.post(
        "/api/v1/auth/register", json=second_registration
    )

    # Assert
    assert response2.status_code == 400
    error_data = response2.json()
    assert "Email already registered" in error_data["detail"]


# ============================================================================
# Test: Login with Invalid Credentials
# ============================================================================


async def test_login_with_invalid_password_fails(integration_client):
    """
    Test that login with wrong password fails.

    Verifies:
    - User can register
    - Login with wrong password returns 401
    - Error message is appropriate
    """
    # Arrange - Register user
    registration_data = {
        "email": "validuser@example.com",
        "password": "CorrectPassword123!",
        "name": "Valid User",
        "organization_name": "Valid Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200

    # Act - Try to login with wrong password
    login_response = await integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": registration_data["email"],
            "password": "WrongPassword123!",
        },
    )

    # Assert
    assert login_response.status_code == 401
    error_data = login_response.json()
    assert "Incorrect email or password" in error_data["detail"]
