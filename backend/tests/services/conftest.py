"""
Service-specific pytest fixtures.

This module provides fixtures for service layer testing with mocked repositories,
database sessions, and security utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.organization_service import OrganizationService
from app.services.organization_member_service import OrganizationMemberService
from app.services.permission_service import PermissionService


# ============================================================================
# Mock Repository Fixtures (Task 0.2)
# ============================================================================


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for service tests."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_with_relations = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_email_with_relations = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_user_auth_repository():
    """Mock UserAuthRepository for service tests."""
    repo = AsyncMock()
    repo.email_exists = AsyncMock()
    repo.get_password_auth = AsyncMock()
    repo.create_password_auth = AsyncMock()
    repo.update_password = AsyncMock()
    return repo


@pytest.fixture
def mock_user_profile_repository():
    """Mock UserProfileRepository for service tests."""
    repo = AsyncMock()
    repo.get_by_user_id = AsyncMock()
    repo.create_profile = AsyncMock()
    repo.update_profile = AsyncMock()
    return repo


@pytest.fixture
def mock_user_status_repository():
    """Mock UserStatusRepository for service tests."""
    repo = AsyncMock()
    repo.is_active = AsyncMock()
    repo.is_suspended = AsyncMock()
    repo.is_archived = AsyncMock()
    repo.activate = AsyncMock()
    repo.suspend = AsyncMock()
    repo.get_active_suspension = AsyncMock()
    repo.archive = AsyncMock()
    repo.unarchive = AsyncMock()
    return repo


@pytest.fixture
def mock_organization_repository():
    """Mock OrganizationRepository for service tests."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_with_relations = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.is_active = AsyncMock()
    repo.activate = AsyncMock()
    repo.deactivate = AsyncMock()
    repo.suspend = AsyncMock()
    repo.archive = AsyncMock()
    repo.list_active = AsyncMock()
    return repo


@pytest.fixture
def mock_organization_member_repository():
    """Mock OrganizationMemberRepository for service tests."""
    repo = AsyncMock()
    repo.is_member = AsyncMock()
    repo.add_member = AsyncMock()
    repo.remove_member = AsyncMock()
    repo.list_members = AsyncMock()
    repo.count_members = AsyncMock()
    repo.list_organizations_for_user = AsyncMock()
    return repo


@pytest.fixture
def mock_organization_owner_repository():
    """Mock OrganizationOwnerRepository for service tests."""
    repo = AsyncMock()
    repo.is_owner = AsyncMock()
    repo.get_owner = AsyncMock()
    repo.create = AsyncMock()
    repo.set_owner = AsyncMock()
    repo.transfer_ownership = AsyncMock()
    return repo


@pytest.fixture
def mock_organization_admin_repository():
    """Mock OrganizationAdminRepository for service tests."""
    repo = AsyncMock()
    repo.is_admin = AsyncMock()
    repo.grant_admin = AsyncMock()
    repo.revoke_admin = AsyncMock()
    repo.list_admins = AsyncMock()
    return repo


# ============================================================================
# Database Session Fixtures (Task 0.3)
# ============================================================================


@pytest.fixture
def mock_db_session():
    """
    Mock database session for service tests.

    Provides mocked transaction management methods.
    """
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    return session


# ============================================================================
# Security/Auth Mocking Utilities (Task 0.4)
# ============================================================================


@pytest.fixture
def mock_password_hash():
    """Mock password hashing function."""
    def _mock_hash(password: str) -> str:
        return f"hashed_{password}"
    return _mock_hash


@pytest.fixture
def mock_password_verify():
    """Mock password verification function."""
    def _mock_verify(plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{plain_password}"
    return _mock_verify


@pytest.fixture
def mock_jwt_tokens():
    """
    Mock JWT token generation.

    Returns:
        dict: Contains mock functions for token creation
    """
    return {
        "create_access_token": lambda data: f"access_token_{data.get('sub', 'user')}",
        "create_refresh_token": lambda data: f"refresh_token_{data.get('sub', 'user')}",
    }


@pytest.fixture
def mock_security_functions(mock_password_hash, mock_password_verify, mock_jwt_tokens):
    """
    Combined security functions mock.

    Provides all security-related mocks in a single fixture.
    """
    return {
        "get_password_hash": mock_password_hash,
        "verify_password": mock_password_verify,
        "create_access_token": mock_jwt_tokens["create_access_token"],
        "create_refresh_token": mock_jwt_tokens["create_refresh_token"],
    }


# ============================================================================
# Service Factory Fixtures
# ============================================================================


@pytest.fixture
def auth_service(
    mock_db_session,
    mock_user_repository,
    mock_user_auth_repository,
    mock_user_profile_repository,
    mock_user_status_repository,
    mock_organization_repository,
    mock_organization_member_repository,
    mock_organization_owner_repository,
):
    """
    AuthService instance with mocked dependencies.

    Creates service instance and replaces repository attributes with mocks.

    Returns:
        AuthService: Service instance for testing
    """
    service = AuthService(db=mock_db_session)
    # Replace repository instances with mocks
    service.user_repo = mock_user_repository
    service.auth_repo = mock_user_auth_repository
    service.profile_repo = mock_user_profile_repository
    service.status_repo = mock_user_status_repository
    service.org_repo = mock_organization_repository
    service.member_repo = mock_organization_member_repository
    service.owner_repo = mock_organization_owner_repository
    return service


@pytest.fixture
def user_service(
    mock_db_session,
    mock_user_repository,
    mock_user_auth_repository,
    mock_user_profile_repository,
    mock_user_status_repository,
    mock_organization_member_repository,
):
    """
    UserService instance with mocked dependencies.

    Creates service instance and replaces repository attributes with mocks.

    Returns:
        UserService: Service instance for testing
    """
    service = UserService(db=mock_db_session)
    # Replace repository instances with mocks
    service.user_repo = mock_user_repository
    service.auth_repo = mock_user_auth_repository
    service.profile_repo = mock_user_profile_repository
    service.status_repo = mock_user_status_repository
    service.member_repo = mock_organization_member_repository
    return service


@pytest.fixture
def organization_service(
    mock_db_session,
    mock_organization_repository,
):
    """
    OrganizationService instance with mocked dependencies.

    Creates service instance and replaces repository attributes with mocks.

    Returns:
        OrganizationService: Service instance for testing
    """
    service = OrganizationService(db=mock_db_session)
    # Replace repository instances with mocks
    service.org_repo = mock_organization_repository
    return service


@pytest.fixture
def organization_member_service(
    mock_db_session,
    mock_user_repository,
    mock_organization_repository,
    mock_organization_member_repository,
):
    """
    OrganizationMemberService instance with mocked dependencies.

    Creates service instance and replaces repository attributes with mocks.

    Returns:
        OrganizationMemberService: Service instance for testing
    """
    service = OrganizationMemberService(db=mock_db_session)
    # Replace repository instances with mocks
    service.member_repo = mock_organization_member_repository
    service.org_repo = mock_organization_repository
    service.user_repo = mock_user_repository
    return service


@pytest.fixture
def permission_service(
    mock_db_session,
    mock_organization_member_repository,
    mock_organization_owner_repository,
    mock_organization_admin_repository,
):
    """
    PermissionService instance with mocked dependencies.

    Creates service instance and replaces repository attributes with mocks.

    Returns:
        PermissionService: Service instance for testing
    """
    service = PermissionService(db=mock_db_session)
    # Replace repository instances with mocks
    service.member_repo = mock_organization_member_repository
    service.owner_repo = mock_organization_owner_repository
    service.admin_repo = mock_organization_admin_repository
    return service