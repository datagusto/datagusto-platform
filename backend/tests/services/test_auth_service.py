"""
AuthService unit tests.

Tests authentication service business logic including user registration
and login with mocked repositories and security functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from tests.services.utils import UserDataFactory, OrganizationDataFactory, build_mock_user_model, build_mock_organization_model


# ============================================================================
# Test: register_user() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_register_user_success(auth_service, mock_user_repository, mock_user_auth_repository,
                                      mock_user_profile_repository, mock_user_status_repository,
                                      mock_organization_repository, mock_organization_member_repository,
                                      mock_organization_owner_repository, mock_db_session):
    """
    Test successful user registration.

    Verifies:
    - User created with organization
    - Organization activated
    - User profile, auth, and status created
    - Membership and ownership established
    - Tokens generated and returned
    """
    # Arrange
    user_id = uuid4()
    org_id = uuid4()
    user_data = UserDataFactory.build(
        user_id=user_id,
        email="test@example.com",
        name="Test User"
    )
    org_data = OrganizationDataFactory.build(
        org_id=org_id,
        name="Test Organization"
    )

    user_input = UserCreate(
        email=user_data["email"],
        name=user_data["name"],
        password="Test123!@#",
        organization_name=org_data["name"]
    )

    # Mock repository responses
    mock_user_auth_repository.email_exists.return_value = False
    mock_organization_repository.create.return_value = build_mock_organization_model(org_data)
    mock_organization_repository.activate.return_value = AsyncMock()

    mock_user = build_mock_user_model(user_data)
    mock_user.id = user_id
    mock_user_repository.create.return_value = mock_user

    mock_user_auth_repository.create_password_auth.return_value = AsyncMock()
    mock_user_profile_repository.create_profile.return_value = AsyncMock()
    mock_user_status_repository.activate.return_value = AsyncMock()
    mock_organization_member_repository.add_member.return_value = AsyncMock()
    mock_organization_owner_repository.set_owner.return_value = AsyncMock()

    # Mock security functions
    with patch('app.services.auth_service.get_password_hash') as mock_hash, \
         patch('app.services.auth_service.create_access_token') as mock_access, \
         patch('app.services.auth_service.create_refresh_token') as mock_refresh:

        mock_hash.return_value = "hashed_Test123!@#"
        mock_access.return_value = "access_token_123"
        mock_refresh.return_value = "refresh_token_456"

        # Act
        result = await auth_service.register_user(user_input)

    # Assert
    assert result is not None
    assert result["email"] == user_data["email"]
    assert result["name"] == user_data["name"]
    assert result["access_token"] == "access_token_123"
    assert result["refresh_token"] == "refresh_token_456"
    assert result["token_type"] == "bearer"

    # Verify repository calls
    mock_user_auth_repository.email_exists.assert_called_once_with(user_data["email"])
    mock_organization_repository.create.assert_called_once()
    mock_organization_repository.activate.assert_called_once()
    mock_user_repository.create.assert_called_once()
    mock_user_auth_repository.create_password_auth.assert_called_once()
    mock_user_profile_repository.create_profile.assert_called_once()
    mock_user_status_repository.activate.assert_called_once()
    mock_organization_member_repository.add_member.assert_called_once()
    mock_organization_owner_repository.set_owner.assert_called_once()
    mock_db_session.commit.assert_called_once()


# ============================================================================
# Test: register_user() - Email already exists
# ============================================================================


@pytest.mark.asyncio
async def test_register_user_email_exists(auth_service, mock_user_auth_repository,
                                           mock_organization_repository, mock_user_repository,
                                           mock_db_session):
    """
    Test user registration with existing email.

    Verifies:
    - HTTPException raised with 400 status
    - Error message indicates email already registered
    - No user or organization creation attempted
    - Transaction rolled back
    """
    # Arrange
    user_input = UserCreate(
        email="existing@example.com",
        name="Test User",
        password="Test123!@#",
        organization_name="Test Org"
    )

    # Mock email already exists
    mock_user_auth_repository.email_exists.return_value = True

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(user_input)

    assert exc_info.value.status_code == 400
    assert "Email already registered" in exc_info.value.detail

    # Verify no creation attempted
    mock_user_auth_repository.email_exists.assert_called_once()
    mock_organization_repository.create.assert_not_called()
    mock_user_repository.create.assert_not_called()
    mock_db_session.rollback.assert_called_once()


# ============================================================================
# Test: login_user() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_login_user_success(auth_service, mock_user_repository, mock_user_status_repository,
                                   mock_organization_member_repository, mock_organization_repository):
    """
    Test successful user login.

    Verifies:
    - User authenticated with correct credentials
    - User status checks passed (active, not suspended/archived)
    - Organization membership verified
    - Tokens generated and returned
    """
    # Arrange
    user_id = uuid4()
    org_id = uuid4()
    user_data = UserDataFactory.build(
        user_id=user_id,
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_Test123!@#"
    )
    org_data = OrganizationDataFactory.build(org_id=org_id)

    # Mock user lookup
    mock_user = build_mock_user_model(user_data)
    mock_user_repository.get_by_email_with_relations.return_value = mock_user

    # Mock status checks
    mock_user_status_repository.is_active.return_value = True
    mock_user_status_repository.is_suspended.return_value = False
    mock_user_status_repository.is_archived.return_value = False

    # Mock organization membership
    mock_org = build_mock_organization_model(org_data)
    mock_organization_member_repository.list_organizations_for_user.return_value = [mock_org]
    mock_organization_repository.is_active.return_value = True

    # Mock security functions
    with patch('app.services.auth_service.verify_password') as mock_verify, \
         patch('app.services.auth_service.create_access_token') as mock_access, \
         patch('app.services.auth_service.create_refresh_token') as mock_refresh:

        mock_verify.return_value = True
        mock_access.return_value = "access_token_123"
        mock_refresh.return_value = "refresh_token_456"

        # Act
        result = await auth_service.login_user(
            email=user_data["email"],
            password="Test123!@#"
        )

    # Assert
    assert result is not None
    assert result["email"] == user_data["email"]
    assert result["name"] == user_data["name"]
    assert result["access_token"] == "access_token_123"
    assert result["refresh_token"] == "refresh_token_456"
    assert result["token_type"] == "bearer"

    # Verify repository calls
    mock_user_repository.get_by_email_with_relations.assert_called_once_with(user_data["email"])
    mock_user_status_repository.is_active.assert_called_once_with(user_id)
    mock_user_status_repository.is_suspended.assert_called_once_with(user_id)
    mock_user_status_repository.is_archived.assert_called_once_with(user_id)
    mock_organization_member_repository.list_organizations_for_user.assert_called_once()
    mock_organization_repository.is_active.assert_called_once()


# ============================================================================
# Test: login_user() - Invalid password
# ============================================================================


@pytest.mark.asyncio
async def test_login_user_invalid_password(auth_service, mock_user_repository, mock_user_status_repository):
    """
    Test login with invalid password.

    Verifies:
    - HTTPException raised with 401 status
    - Error message indicates incorrect credentials
    - No tokens generated
    """
    # Arrange
    user_id = uuid4()
    user_data = UserDataFactory.build(
        user_id=user_id,
        email="test@example.com",
        hashed_password="hashed_CorrectPassword123"
    )

    # Mock user lookup
    mock_user = build_mock_user_model(user_data)
    mock_user_repository.get_by_email_with_relations.return_value = mock_user

    # Mock status checks (must pass to reach password verification)
    mock_user_status_repository.is_active.return_value = True
    mock_user_status_repository.is_suspended.return_value = False
    mock_user_status_repository.is_archived.return_value = False

    # Mock password verification failure
    with patch('app.services.auth_service.verify_password') as mock_verify:
        mock_verify.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login_user(
                email=user_data["email"],
                password="WrongPassword123"
            )

    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in exc_info.value.detail


# ============================================================================
# Test: login_user() - User not found
# ============================================================================


@pytest.mark.asyncio
async def test_login_user_user_not_found(auth_service, mock_user_repository):
    """
    Test login with non-existent email.

    Verifies:
    - HTTPException raised with 401 status
    - Error message indicates incorrect credentials
    - Password verification not attempted
    """
    # Arrange
    mock_user_repository.get_by_email_with_relations.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(
            email="nonexistent@example.com",
            password="Test123!@#"
        )

    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in exc_info.value.detail

    # Verify user lookup attempted
    mock_user_repository.get_by_email_with_relations.assert_called_once()