import pytest
import os
from fastapi import status
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        # Ensure password is not returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_user_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@example.com",
            "name": "Test User",
            "password": "testpassword123"
        }
        
        # Register user first time - should succeed
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Try to register same email again - should fail
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_missing_password(self, client: TestClient):
        """Test registration without password."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_when_disabled(self, client: TestClient):
        """Test registration fails when disabled."""
        # Temporarily disable registration
        os.environ["ENABLE_REGISTRATION"] = "false"
        
        user_data = {
            "email": "test@example.com",
            "name": "Test User", 
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "registration is temporarily disabled" in response.json()["detail"]
        
        # Re-enable registration for other tests
        os.environ["ENABLE_REGISTRATION"] = "true"

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "name": "Login User",
            "password": "loginpassword123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Now login
        login_data = {
            "username": "login@example.com",  # OAuth2PasswordRequestForm uses 'username'
            "password": "loginpassword123"
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        # First register a user
        user_data = {
            "email": "wrongpass@example.com",
            "name": "Wrong Pass User",
            "password": "correctpassword123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Try login with wrong password
        login_data = {
            "username": "wrongpass@example.com",
            "password": "wrongpassword123"
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_current_user_success(self, client: TestClient):
        """Test getting current user info with valid token."""
        # Register and login user
        user_data = {
            "email": "currentuser@example.com",
            "name": "Current User",
            "password": "currentpassword123"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_response = client.post("/api/v1/auth/token", data={
            "username": "currentuser@example.com",
            "password": "currentpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert "id" in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user info without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user info with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED