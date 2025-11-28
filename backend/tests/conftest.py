"""
Shared pytest fixtures for controller layer tests.

This module provides fixtures for mocking services, database sessions,
authentication, and test data.
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.auth import get_current_user

# Import settings from application
from app.core.config import settings
from app.core.database import get_async_db
from app.main import app
from app.services.auth_service import AuthService
from app.services.organization_member_service import OrganizationMemberService
from app.services.organization_service import OrganizationService
from app.services.permission_service import PermissionService
from app.services.user_service import UserService

# ============================================================================
# Test Database Configuration
# ============================================================================

# Create test engine with NullPool for better test isolation
# NullPool prevents connection pooling which can interfere with test transactions
test_engine = create_async_engine(
    settings.test_async_database_url,
    echo=False,  # Set to True for SQL query debugging
    poolclass=NullPool,  # Disable connection pooling for tests
)

# Create async session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# Basic Fixtures (Task 0.2)
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def override_get_async_db(mock_db):
    """Override get_async_db dependency."""

    async def _override_get_async_db():
        yield mock_db

    return _override_get_async_db


@pytest.fixture
def test_app(override_get_async_db):
    """FastAPI test app with overridden dependencies."""
    app.dependency_overrides[get_async_db] = override_get_async_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_app):
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Test Data Fixtures (Task 0.3)
# ============================================================================


@pytest.fixture
def test_user_id() -> UUID:
    """Test user UUID."""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def test_organization_id() -> UUID:
    """Test organization UUID."""
    return UUID("87654321-4321-4321-4321-cba987654321")


@pytest.fixture
def test_user_data(test_user_id) -> dict:
    """Sample user data for testing."""
    return {
        "id": str(test_user_id),
        "email": "test@example.com",
        "name": "Test User",
        "bio": "Test bio",
        "avatar_url": "https://example.com/avatar.png",
        "is_active": True,
        "is_suspended": False,
        "is_archived": False,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_organization_data(test_organization_id) -> dict:
    """Sample organization data for testing."""
    return {
        "id": str(test_organization_id),
        "name": "Test Organization",
        "slug": "test-org",
        "description": "Test organization description",
        "website_url": "https://example.com",
        "logo_url": "https://example.com/logo.png",
        "is_active": True,
        "is_suspended": False,
        "is_archived": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_user(test_user_data):
    """Mock User model instance."""
    user = MagicMock()
    user.id = UUID(test_user_data["id"])
    user.email = test_user_data["email"]
    user.created_at = datetime.utcnow()
    return user


@pytest.fixture
def mock_organization(test_organization_data):
    """Mock Organization model instance."""
    org = MagicMock()
    org.id = UUID(test_organization_data["id"])
    org.name = test_organization_data["name"]
    org.slug = test_organization_data["slug"]
    org.created_at = datetime.utcnow()
    org.updated_at = datetime.utcnow()
    return org


@pytest.fixture
def mock_user_with_relations(mock_user, test_user_data):
    """Mock User with profile and auth relations."""
    # Add profile
    profile = MagicMock()
    profile.name = test_user_data["name"]
    profile.bio = test_user_data.get("bio")
    profile.avatar_url = test_user_data.get("avatar_url")
    mock_user.profile = profile

    # Add login_password
    login_password = MagicMock()
    login_password.email = test_user_data["email"]
    login_password.hashed_password = "hashed_password"
    mock_user.login_password = login_password

    return mock_user


# ============================================================================
# Authentication Fixtures (Task 0.4)
# ============================================================================


@pytest.fixture
def mock_jwt_token() -> str:
    """Mock JWT token for testing."""
    return "mock_jwt_token_12345"


@pytest.fixture
def auth_headers(mock_jwt_token) -> dict:
    """Authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def mock_current_user(test_user_id) -> dict:
    """Mock current user extracted from JWT."""
    return {
        "id": str(test_user_id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def override_get_current_user(mock_current_user):
    """Override get_current_user dependency."""

    async def _override_get_current_user():
        return mock_current_user

    return _override_get_current_user


@pytest.fixture
def authenticated_app(test_app, override_get_current_user):
    """Test app with authenticated user."""
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield test_app
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(authenticated_app):
    """Async client with authenticated user."""
    transport = ASGITransport(app=authenticated_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_permission_service():
    """Mock PermissionService for authorization checks."""
    service = AsyncMock(spec=PermissionService)
    service.is_owner = AsyncMock(return_value=False)
    service.is_admin_or_owner = AsyncMock(return_value=False)
    service.is_member_or_above = AsyncMock(return_value=False)
    return service


# ============================================================================
# Mock Service Fixtures (Task 0.5)
# ============================================================================


@pytest.fixture
def mock_auth_service():
    """Mock AuthService for authentication operations."""
    service = AsyncMock(spec=AuthService)
    service.register_user = AsyncMock()
    service.login_user = AsyncMock()
    return service


@pytest.fixture
def mock_user_service():
    """Mock UserService for user operations."""
    service = AsyncMock(spec=UserService)
    service.get_user = AsyncMock()
    service.update_profile = AsyncMock()
    service.change_password = AsyncMock()
    service.change_email = AsyncMock()
    service.suspend_user = AsyncMock()
    service.archive_user = AsyncMock()
    service.unarchive_user = AsyncMock()
    service.list_users_in_organization = AsyncMock()
    return service


@pytest.fixture
def mock_organization_service():
    """Mock OrganizationService for organization operations."""
    service = AsyncMock(spec=OrganizationService)
    service.get_organization = AsyncMock()
    service.create_organization = AsyncMock()
    service.update_organization = AsyncMock()
    service.suspend_organization = AsyncMock()
    service.archive_organization = AsyncMock()
    service.list_active_organizations = AsyncMock()
    return service


@pytest.fixture
def mock_member_service():
    """Mock OrganizationMemberService for member operations."""
    service = AsyncMock(spec=OrganizationMemberService)
    service.is_member = AsyncMock()
    service.add_member = AsyncMock()
    service.remove_member = AsyncMock()
    service.list_members = AsyncMock()
    service.count_members = AsyncMock()
    return service


# ============================================================================
# PostgreSQL Test Database Fixtures (for Repository & Integration Tests)
# ============================================================================


@pytest.fixture(scope="session")
def test_db_setup():
    """
    Setup test database with migrations (session scope).

    Runs alembic migrations on test database before any tests.
    Drops all tables after all tests complete.
    """
    from alembic.config import Config

    from alembic import command
    from app.core.config import Settings

    # Override POSTGRES_DB environment variable temporarily for test database
    original_db = os.environ.get("POSTGRES_DB")
    os.environ["POSTGRES_DB"] = settings.TEST_POSTGRES_DB

    # Create new settings instance with test database
    test_settings = Settings()

    try:
        # Run migrations using synchronous URL
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url", test_settings.test_sync_database_url
        )
        command.upgrade(alembic_cfg, "head")
        print("\n✅ Test database migrations applied successfully")
    finally:
        # Restore original POSTGRES_DB
        if original_db:
            os.environ["POSTGRES_DB"] = original_db
        else:
            os.environ.pop("POSTGRES_DB", None)

    yield

    # Cleanup: Drop all tables after all tests
    print("\n🧹 Cleaning up test database...")
    try:
        os.environ["POSTGRES_DB"] = settings.TEST_POSTGRES_DB
        test_settings = Settings()

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url", test_settings.test_sync_database_url
        )
        command.downgrade(alembic_cfg, "base")
        print("✅ Test database cleaned successfully")
    finally:
        # Restore original POSTGRES_DB
        if original_db:
            os.environ["POSTGRES_DB"] = original_db
        else:
            os.environ.pop("POSTGRES_DB", None)


@pytest.fixture(scope="function")
async def test_db_engine(test_db_setup):
    """
    PostgreSQL test database engine (function scope).

    Creates test engine for each test function.
    Used by repository and integration tests.
    Depends on test_db_setup to ensure migrations are applied.
    """
    yield test_engine
    # Engine disposal handled by conftest module


@pytest.fixture
async def test_db_session(test_db_engine):
    """
    PostgreSQL test database session with transaction rollback.

    Each test gets a fresh database state:
    1. Begin transaction
    2. Run test with session bound to transaction
    3. Rollback transaction (automatic cleanup)

    This ensures test isolation without manual cleanup.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create connection and begin transaction
    async with test_db_engine.connect() as connection:
        transaction = await connection.begin()

        # Create session bound to transaction
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            yield session
        finally:
            await session.close()
            # Rollback transaction - automatic cleanup
            await transaction.rollback()


# ============================================================================
# Cleanup Hooks
# ============================================================================


@pytest.fixture(autouse=True)
def reset_app_overrides():
    """Automatically reset app dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Integration Test Fixtures
# ============================================================================


async def _cleanup_test_database(engine):
    """Helper function to cleanup test database by truncating all tables."""
    from sqlalchemy import text

    async with engine.connect() as connection:
        # Truncate all tables in reverse order of dependencies
        await connection.execute(
            text("TRUNCATE TABLE guardrail_evaluation_logs CASCADE")
        )
        await connection.execute(text("TRUNCATE TABLE user_archives CASCADE"))
        await connection.execute(
            text("TRUNCATE TABLE organization_suspensions CASCADE")
        )
        await connection.execute(text("TRUNCATE TABLE organization_archives CASCADE"))
        await connection.execute(text("TRUNCATE TABLE organization_admins CASCADE"))
        await connection.execute(text("TRUNCATE TABLE organization_owners CASCADE"))
        await connection.execute(text("TRUNCATE TABLE organization_members CASCADE"))
        await connection.execute(text("TRUNCATE TABLE user_active_status CASCADE"))
        await connection.execute(text("TRUNCATE TABLE user_profile CASCADE"))
        await connection.execute(text("TRUNCATE TABLE user_login_password CASCADE"))
        await connection.execute(text("TRUNCATE TABLE users CASCADE"))
        await connection.execute(
            text("TRUNCATE TABLE organization_active_status CASCADE")
        )
        await connection.execute(text("TRUNCATE TABLE organizations CASCADE"))
        await connection.commit()


@pytest.fixture
async def integration_client(test_db_setup, test_db_engine):
    """
    HTTP client for integration tests with real application and real database.

    This is a true integration test fixture:
    - Uses real FastAPI application with dependency override for database
    - Connects to real PostgreSQL test database
    - Database is cleaned automatically after each test
    - Only difference from production: database session uses test database engine

    Args:
        test_db_setup: Ensures test database exists with migrations
        test_db_engine: Test database engine for test sessions

    Returns:
        AsyncClient: HTTP client for making real API requests

    Example:
        >>> async def test_register(integration_client):
        ...     response = await integration_client.post("/api/v1/auth/register", ...)
        ...     assert response.status_code == 200
    """
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_async_db
    from app.main import app

    # Override get_async_db to use test database
    async def override_get_async_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_db] = override_get_async_db

    # Create HTTP client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup: clear overrides and clean database
    app.dependency_overrides.clear()
    await _cleanup_test_database(test_db_engine)
