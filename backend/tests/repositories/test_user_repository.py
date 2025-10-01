"""
UserRepository integration tests.

Tests verify database operations for the User model using PostgreSQL test database
with transaction rollback for isolation.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from tests.repositories.conftest import (
    seed_test_user,
    build_user_data,
)
from tests.repositories.utils import (
    assert_user_matches,
    query_user_by_id,
)


# ============================================================================
# Test: create() - Create user
# ============================================================================


@pytest.mark.asyncio
async def test_create_user_success(
    test_db_session: AsyncSession,
    user_repository: UserRepository,
):
    """
    Test creating a user using repository.

    Verifies:
    - User created successfully
    - User exists in database with correct ID
    - created_at and updated_at timestamps set
    """
    # Arrange
    user_id = uuid4()
    user_data = build_user_data(user_id=user_id)

    # Act
    user = await user_repository.create(user_data)
    await test_db_session.flush()

    # Assert
    assert user is not None
    assert user.id == user_id
    assert user.created_at is not None
    assert user.updated_at is not None

    # Verify user exists in database
    db_user = await query_user_by_id(test_db_session, user_id)
    assert db_user is not None
    assert db_user.id == user_id


# ============================================================================
# Test: get_by_id_with_relations() - Success case
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_with_relations_success(
    test_db_session: AsyncSession,
    user_repository: UserRepository,
):
    """
    Test retrieving user with all relations (profile, auth, status).

    Verifies:
    - User returned with all relations loaded
    - profile, login_password, active_status accessible
    - No additional queries needed (eager loading)
    """
    # Arrange
    user = await seed_test_user(
        test_db_session,
        email="test@example.com",
        name="Test User",
        with_profile=True,
        with_auth=True,
        with_active_status=True,
    )
    await test_db_session.flush()

    # Act
    retrieved_user = await user_repository.get_by_id_with_relations(user.id)

    # Assert
    assert retrieved_user is not None
    assert_user_matches(
        retrieved_user,
        expected_id=user.id,
        expected_email="test@example.com",
        expected_name="Test User",
    )

    # Verify relations are eagerly loaded (no additional queries)
    assert retrieved_user.profile is not None
    assert retrieved_user.profile.name == "Test User"
    assert retrieved_user.profile.bio is not None

    assert retrieved_user.login_password is not None
    assert retrieved_user.login_password.email == "test@example.com"
    assert retrieved_user.login_password.hashed_password is not None

    assert retrieved_user.active_status is not None
    assert retrieved_user.active_status.user_id == user.id


# ============================================================================
# Test: get_by_email() - Find user by email
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_by_email_success(
    test_db_session: AsyncSession,
    user_repository: UserRepository,
):
    """
    Test finding user by email address.

    Verifies:
    - Correct user returned for existing email
    - None returned for non-existent email
    """
    # Arrange
    user = await seed_test_user(
        test_db_session,
        email="findme@example.com",
        with_auth=True,
    )
    await test_db_session.flush()

    # Act - Find existing email
    found_user = await user_repository.get_by_email("findme@example.com")

    # Assert
    assert found_user is not None
    assert found_user.id == user.id

    # Act - Find non-existent email
    not_found = await user_repository.get_by_email("notfound@example.com")

    # Assert
    assert not_found is None


# ============================================================================
# Test: get_by_email_with_relations() - Email lookup with relations
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_by_email_with_relations(
    test_db_session: AsyncSession,
    user_repository: UserRepository,
):
    """
    Test finding user by email with all relations eagerly loaded.

    Verifies:
    - User returned with all relations
    - All relations eagerly loaded (no N+1 queries)
    """
    # Arrange
    user = await seed_test_user(
        test_db_session,
        email="relations@example.com",
        name="Relations User",
        with_profile=True,
        with_auth=True,
        with_active_status=True,
    )
    await test_db_session.flush()

    # Act
    found_user = await user_repository.get_by_email_with_relations(
        "relations@example.com"
    )

    # Assert
    assert found_user is not None
    assert_user_matches(
        found_user,
        expected_id=user.id,
        expected_email="relations@example.com",
        expected_name="Relations User",
    )

    # Verify all relations eagerly loaded
    assert found_user.profile is not None
    assert found_user.profile.name == "Relations User"

    assert found_user.login_password is not None
    assert found_user.login_password.email == "relations@example.com"

    assert found_user.active_status is not None

    # Act - Query non-existent email
    not_found = await user_repository.get_by_email_with_relations(
        "nonexistent@example.com"
    )

    # Assert
    assert not_found is None