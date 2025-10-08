"""
UserStatusRepository integration tests.

Tests verify user status database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
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
