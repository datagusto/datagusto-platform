"""
UserAuthRepository integration tests.

Tests verify authentication database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_auth_repository import UserAuthRepository
from tests.repositories.conftest import seed_test_user

# ============================================================================
# Test: create_password_auth() - Create password authentication
# ============================================================================


@pytest.mark.asyncio
async def test_create_password_auth(
    test_db_session: AsyncSession,
    user_auth_repository: UserAuthRepository,
):
    """
    Test creating password authentication for user.

    Verifies:
    - Auth record created successfully
    - Email and hashed_password stored correctly
    """
    # Arrange
    user = await seed_test_user(test_db_session, with_auth=False)
    await test_db_session.flush()

    # Act
    auth = await user_auth_repository.create_password_auth(
        user_id=user.id,
        email="auth@example.com",
        hashed_password="hashed_pass_123",
    )
    await test_db_session.flush()

    # Assert
    assert auth is not None
    assert auth.user_id == user.id
    assert auth.email == "auth@example.com"
    assert auth.hashed_password == "hashed_pass_123"
    assert auth.password_algorithm == "bcrypt"


# ============================================================================
# Test: email_exists() - Check if email exists
# ============================================================================


@pytest.mark.asyncio
async def test_email_exists(
    test_db_session: AsyncSession,
    user_auth_repository: UserAuthRepository,
):
    """
    Test checking if email exists in database.

    Verifies:
    - Returns True for existing email
    - Returns False for non-existent email
    """
    # Arrange
    _user = await seed_test_user(
        test_db_session,
        email="exists@example.com",
        with_auth=True,
    )
    await test_db_session.flush()

    # Act & Assert - Existing email
    exists = await user_auth_repository.email_exists("exists@example.com")
    assert exists is True

    # Act & Assert - Non-existent email
    not_exists = await user_auth_repository.email_exists("notfound@example.com")
    assert not_exists is False


# ============================================================================
# Test: update_password() - Update password
# ============================================================================


@pytest.mark.asyncio
async def test_update_password(
    test_db_session: AsyncSession,
    user_auth_repository: UserAuthRepository,
):
    """
    Test updating user password.

    Verifies:
    - Password updated successfully
    - New hashed_password stored in database
    """
    # Arrange
    user = await seed_test_user(
        test_db_session,
        password_hash="old_hash_123",
        with_auth=True,
    )
    await test_db_session.flush()

    # Act
    updated_auth = await user_auth_repository.update_password(
        user_id=user.id,
        new_hashed_password="new_hash_456",
    )
    await test_db_session.flush()

    # Assert
    assert updated_auth is not None
    assert updated_auth.hashed_password == "new_hash_456"
    assert updated_auth.hashed_password != "old_hash_123"

    # Verify in database
    auth = await user_auth_repository.get_by_user_id(user.id)
    assert auth.hashed_password == "new_hash_456"
