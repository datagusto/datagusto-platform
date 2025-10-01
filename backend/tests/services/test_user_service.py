"""
UserService unit tests.

Tests user management service methods including profile management,
password changes, and user retrieval with mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from fastapi import HTTPException

from app.services.user_service import UserService
from tests.services.utils import UserDataFactory, OrganizationDataFactory, build_mock_user_model, build_mock_organization_model


# ============================================================================
# Test: get_user() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_success(user_service, mock_user_repository, mock_organization_member_repository,
                                 mock_user_status_repository):
    """
    Test successful user retrieval.

    Verifies:
    - User data returned with all relations
    - Status flags included (active, suspended, archived)
    - Organization membership included
    """
    # Arrange
    user_id = uuid4()
    org_id = uuid4()
    user_data = UserDataFactory.build(
        user_id=user_id,
        email="test@example.com",
        name="Test User"
    )
    org_data = OrganizationDataFactory.build(org_id=org_id)

    # Mock user lookup
    mock_user = build_mock_user_model(user_data)
    mock_user_repository.get_by_id_with_relations.return_value = mock_user

    # Mock organization membership
    mock_org = build_mock_organization_model(org_data)
    mock_organization_member_repository.list_organizations_for_user.return_value = [mock_org]

    # Mock status checks
    mock_user_status_repository.is_active.return_value = True
    mock_user_status_repository.is_suspended.return_value = False
    mock_user_status_repository.is_archived.return_value = False

    # Act
    result = await user_service.get_user(user_id)

    # Assert
    assert result is not None
    assert result["id"] == str(user_id)
    assert result["email"] == user_data["email"]
    assert result["name"] == user_data["name"]
    assert result["organization_id"] == str(org_id)
    assert result["is_active"] is True
    assert result["is_suspended"] is False
    assert result["is_archived"] is False

    # Verify repository calls
    mock_user_repository.get_by_id_with_relations.assert_called_once_with(user_id)
    mock_organization_member_repository.list_organizations_for_user.assert_called_once()
    mock_user_status_repository.is_active.assert_called_once_with(user_id)
    mock_user_status_repository.is_suspended.assert_called_once_with(user_id)
    mock_user_status_repository.is_archived.assert_called_once_with(user_id)


# ============================================================================
# Test: get_user() - User not found
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_not_found(user_service, mock_user_repository):
    """
    Test user retrieval when user doesn't exist.

    Verifies:
    - HTTPException raised with 404 status
    - Error message indicates user not found
    """
    # Arrange
    user_id = uuid4()
    mock_user_repository.get_by_id_with_relations.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await user_service.get_user(user_id)

    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail

    # Verify lookup attempted
    mock_user_repository.get_by_id_with_relations.assert_called_once_with(user_id)


# ============================================================================
# Test: update_profile() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_update_profile_success(user_service, mock_user_repository, mock_user_profile_repository,
                                       mock_organization_member_repository, mock_user_status_repository,
                                       mock_db_session):
    """
    Test successful profile update.

    Verifies:
    - Profile updated with new data
    - User data returned after update
    - Database transaction committed
    """
    # Arrange
    user_id = uuid4()
    org_id = uuid4()
    user_data = UserDataFactory.build(
        user_id=user_id,
        email="test@example.com",
        name="Old Name"
    )

    profile_update = {
        "name": "New Name",
        "bio": "Updated bio",
        "avatar_url": "https://example.com/new-avatar.png"
    }

    # Mock user existence
    mock_user = build_mock_user_model(user_data)
    mock_user_repository.get_by_id.return_value = mock_user

    # Mock profile exists
    mock_profile = AsyncMock()
    mock_user_profile_repository.get_by_user_id.return_value = mock_profile
    mock_user_profile_repository.update_profile.return_value = AsyncMock()

    # Mock get_user for return value
    updated_user_data = user_data.copy()
    updated_user_data.update(profile_update)
    mock_updated_user = build_mock_user_model(updated_user_data)
    mock_user_repository.get_by_id_with_relations.return_value = mock_updated_user

    mock_org = build_mock_organization_model(OrganizationDataFactory.build(org_id=org_id))
    mock_organization_member_repository.list_organizations_for_user.return_value = [mock_org]
    mock_user_status_repository.is_active.return_value = True
    mock_user_status_repository.is_suspended.return_value = False
    mock_user_status_repository.is_archived.return_value = False

    # Act
    result = await user_service.update_profile(user_id, profile_update)

    # Assert
    assert result is not None
    assert result["name"] == "New Name"

    # Verify repository calls
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    mock_user_profile_repository.get_by_user_id.assert_called_once_with(user_id)
    mock_user_profile_repository.update_profile.assert_called_once_with(user_id, profile_update)
    mock_db_session.commit.assert_called_once()


# ============================================================================
# Test: change_password() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_change_password_success(user_service, mock_user_auth_repository, mock_db_session):
    """
    Test successful password change.

    Verifies:
    - Old password verified before change
    - New password hashed and stored
    - Database transaction committed
    """
    # Arrange
    user_id = uuid4()
    old_password = "OldPassword123"
    new_password = "NewPassword456"

    # Mock auth record
    mock_auth = AsyncMock()
    mock_auth.hashed_password = "hashed_OldPassword123"
    mock_user_auth_repository.get_by_user_id.return_value = mock_auth

    # Mock security functions
    with patch('app.services.user_service.verify_password') as mock_verify, \
         patch('app.services.user_service.get_password_hash') as mock_hash:

        mock_verify.return_value = True
        mock_hash.return_value = "hashed_NewPassword456"
        mock_user_auth_repository.update_password.return_value = AsyncMock()

        # Act
        result = await user_service.change_password(user_id, old_password, new_password)

    # Assert
    assert result is True

    # Verify repository calls
    mock_user_auth_repository.get_by_user_id.assert_called_once_with(user_id)
    mock_verify.assert_called_once_with(old_password, "hashed_OldPassword123")
    mock_hash.assert_called_once_with(new_password)
    mock_user_auth_repository.update_password.assert_called_once_with(user_id, "hashed_NewPassword456")
    mock_db_session.commit.assert_called_once()


# ============================================================================
# Test: change_password() - Wrong old password
# ============================================================================


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(user_service, mock_user_auth_repository):
    """
    Test password change with incorrect old password.

    Verifies:
    - HTTPException raised with 400 status
    - Error message indicates incorrect password
    - New password not set
    """
    # Arrange
    user_id = uuid4()
    old_password = "WrongPassword"
    new_password = "NewPassword456"

    # Mock auth record
    mock_auth = AsyncMock()
    mock_auth.hashed_password = "hashed_CorrectPassword123"
    mock_user_auth_repository.get_by_user_id.return_value = mock_auth

    # Mock password verification failure
    with patch('app.services.user_service.verify_password') as mock_verify:
        mock_verify.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await user_service.change_password(user_id, old_password, new_password)

    assert exc_info.value.status_code == 400
    assert "Incorrect current password" in exc_info.value.detail

    # Verify update not called
    mock_user_auth_repository.update_password.assert_not_called()