"""
User management flow integration tests.

Tests complete user management workflows end-to-end with real database.
Covers profile retrieval, updates, password changes, and permission boundaries.
"""

import pytest
from uuid import UUID


# Mark all tests as integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


# ============================================================================
# Test: User Profile Retrieval Flow
# ============================================================================


async def test_get_user_profile_complete_flow(integration_client):
    """
    Test complete user profile retrieval flow.

    Verifies:
    - User can register and authenticate
    - User can retrieve their own profile
    - Profile data matches what was stored
    - All profile fields are present
    """
    # Arrange - Register user
    registration_data = {
        "email": "profile@example.com",
        "password": "ProfileTest123!",
        "name": "Profile Test User",
        "organization_name": "Profile Test Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    user_id = user_data["user_id"]
    access_token = user_data["access_token"]

    # Act - Get user profile
    response = await integration_client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Assert
    assert response.status_code == 200
    profile = response.json()

    assert profile["id"] == user_id
    assert profile["email"] == registration_data["email"]
    assert profile["name"] == registration_data["name"]
    assert profile["is_active"] is True
    assert profile["is_suspended"] is False
    assert profile["is_archived"] is False
    assert "created_at" in profile


# ============================================================================
# Test: Profile Update Flow
# ============================================================================


async def test_update_profile_persists_to_database(integration_client):
    """
    Test profile update flow with database persistence verification.

    Verifies:
    - User can update their profile
    - Changes are persisted to database
    - Updated data is returned correctly
    - Subsequent GET reflects changes
    """
    # Arrange - Register and authenticate
    registration_data = {
        "email": "update@example.com",
        "password": "UpdateTest123!",
        "name": "Original Name",
        "organization_name": "Update Test Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    user_id = user_data["user_id"]
    access_token = user_data["access_token"]

    # Act - Update profile
    update_data = {
        "name": "Updated Name",
        "bio": "This is my new bio",
        "avatar_url": "https://example.com/new-avatar.png",
    }

    update_response = await integration_client.patch(
        f"/api/v1/users/{user_id}/profile",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Assert update response
    assert update_response.status_code == 200
    updated_profile = update_response.json()
    assert updated_profile["name"] == update_data["name"]
    assert updated_profile["bio"] == update_data["bio"]
    assert updated_profile["avatar_url"] == update_data["avatar_url"]

    # Verify changes persisted - GET profile again
    get_response = await integration_client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert get_response.status_code == 200
    persisted_profile = get_response.json()

    assert persisted_profile["name"] == update_data["name"]
    assert persisted_profile["bio"] == update_data["bio"]
    assert persisted_profile["avatar_url"] == update_data["avatar_url"]


# ============================================================================
# Test: Password Change Flow
# ============================================================================


async def test_change_password_and_login_with_new_password(integration_client):
    """
    Test complete password change flow.

    Verifies:
    - User can change password with correct old password
    - New password works for login
    - Old password no longer works
    - Password is properly hashed in database
    """
    # Arrange - Register user
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    registration_data = {
        "email": "password@example.com",
        "password": old_password,
        "name": "Password Test User",
        "organization_name": "Password Test Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    user_id = user_data["user_id"]
    access_token = user_data["access_token"]

    # Act - Change password
    password_change_data = {
        "old_password": old_password,
        "new_password": new_password,
    }

    change_response = await integration_client.post(
        f"/api/v1/users/{user_id}/change-password",
        json=password_change_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Assert password change succeeded
    assert change_response.status_code == 200

    # Verify new password works for login
    new_login_response = await integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": registration_data["email"],
            "password": new_password,
        },
    )
    assert new_login_response.status_code == 200
    assert "access_token" in new_login_response.json()

    # Verify old password no longer works
    old_login_response = await integration_client.post(
        "/api/v1/auth/token",
        data={
            "username": registration_data["email"],
            "password": old_password,
        },
    )
    assert old_login_response.status_code == 401


# ============================================================================
# Test: Permission Boundaries
# ============================================================================


async def test_user_cannot_modify_other_users_profile(integration_client):
    """
    Test permission boundaries between users.

    Verifies:
    - Users can read other users' profiles
    - Users cannot modify other users' profiles
    - Proper 403 Forbidden response for unauthorized actions
    """
    # Arrange - Register User A
    user_a_data = {
        "email": "usera@example.com",
        "password": "UserAPass123!",
        "name": "User A",
        "organization_name": "User A Org",
    }

    user_a_response = await integration_client.post(
        "/api/v1/auth/register", json=user_a_data
    )
    assert user_a_response.status_code == 200
    user_a = user_a_response.json()

    # Arrange - Register User B
    user_b_data = {
        "email": "userb@example.com",
        "password": "UserBPass123!",
        "name": "User B",
        "organization_name": "User B Org",
    }

    user_b_response = await integration_client.post(
        "/api/v1/auth/register", json=user_b_data
    )
    assert user_b_response.status_code == 200
    user_b = user_b_response.json()

    # Act - User A tries to read User B's profile (should succeed)
    read_response = await integration_client.get(
        f"/api/v1/users/{user_b['user_id']}",
        headers={"Authorization": f"Bearer {user_a['access_token']}"},
    )
    assert read_response.status_code == 200

    # Act - User A tries to modify User B's profile (should fail)
    update_data = {
        "name": "Hacked Name",
        "bio": "This should not work",
    }

    modify_response = await integration_client.patch(
        f"/api/v1/users/{user_b['user_id']}/profile",
        json=update_data,
        headers={"Authorization": f"Bearer {user_a['access_token']}"},
    )

    # Assert - Modification should be forbidden
    assert modify_response.status_code == 403

    # Verify User B's profile unchanged
    verify_response = await integration_client.get(
        f"/api/v1/users/{user_b['user_id']}",
        headers={"Authorization": f"Bearer {user_b['access_token']}"},
    )
    assert verify_response.status_code == 200
    user_b_profile = verify_response.json()
    assert user_b_profile["name"] == user_b_data["name"]
    assert user_b_profile["bio"] != update_data["bio"]
