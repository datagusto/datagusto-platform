"""
UserStatusRepository integration tests.

Tests verify user status database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_status_repository import UserStatusRepository
from tests.repositories.conftest import seed_test_user


# ============================================================================
# Test: activate() - Activate user
# ============================================================================


@pytest.mark.asyncio
async def test_activate_user(
    test_db_session: AsyncSession,
    user_status_repository: UserStatusRepository,
):
    """
    Test activating user.

    Verifies:
    - User activated successfully
    - is_active() returns True after activation
    """
    # Arrange
    user = await seed_test_user(test_db_session, with_active_status=False)
    await test_db_session.flush()

    # Verify initially not active
    assert await user_status_repository.is_active(user.id) is False

    # Act
    active_status = await user_status_repository.activate(user.id)
    await test_db_session.flush()

    # Assert
    assert active_status is not None
    assert active_status.user_id == user.id
    assert await user_status_repository.is_active(user.id) is True


# ============================================================================
# Test: suspend() - Suspend user
# ============================================================================


@pytest.mark.asyncio
async def test_suspend_user(
    test_db_session: AsyncSession,
    user_status_repository: UserStatusRepository,
):
    """
    Test suspending user.

    Verifies:
    - User suspended successfully
    - is_suspended() returns True after suspension
    - Suspension reason stored correctly
    """
    # Arrange
    user = await seed_test_user(test_db_session)
    admin_user = await seed_test_user(test_db_session)  # Create actual admin user
    await test_db_session.flush()

    # Verify initially not suspended
    assert await user_status_repository.is_suspended(user.id) is False

    # Act
    suspension = await user_status_repository.suspend(
        user_id=user.id,
        reason="Terms of service violation",
        suspended_by=admin_user.id,
    )
    await test_db_session.flush()

    # Assert
    assert suspension is not None
    assert suspension.user_id == user.id
    assert suspension.reason == "Terms of service violation"
    assert suspension.suspended_by == admin_user.id
    assert suspension.lifted_at is None
    assert await user_status_repository.is_suspended(user.id) is True

    # Verify get_active_suspension
    active_suspension = await user_status_repository.get_active_suspension(user.id)
    assert active_suspension is not None
    assert active_suspension.id == suspension.id