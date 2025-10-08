"""
UserProfileRepository integration tests.

Tests verify profile database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_profile_repository import UserProfileRepository
from tests.repositories.conftest import seed_test_user

# ============================================================================
# Test: create_profile() - Create user profile
# ============================================================================


@pytest.mark.asyncio
async def test_create_profile(
    test_db_session: AsyncSession,
    user_profile_repository: UserProfileRepository,
):
    """
    Test creating user profile.

    Verifies:
    - Profile created successfully
    - Name, bio, avatar_url stored correctly
    """
    # Arrange
    user = await seed_test_user(test_db_session, with_profile=False)
    await test_db_session.flush()

    # Act
    profile = await user_profile_repository.create_profile(
        user_id=user.id,
        profile_data={
            "name": "John Doe",
            "bio": "Software Engineer",
            "avatar_url": "https://example.com/avatar.png",
        },
    )
    await test_db_session.flush()

    # Assert
    assert profile is not None
    assert profile.user_id == user.id
    assert profile.name == "John Doe"
    assert profile.bio == "Software Engineer"
    assert profile.avatar_url == "https://example.com/avatar.png"


# ============================================================================
# Test: update_profile() - Update user profile
# ============================================================================


@pytest.mark.asyncio
async def test_update_profile(
    test_db_session: AsyncSession,
    user_profile_repository: UserProfileRepository,
):
    """
    Test updating user profile.

    Verifies:
    - Profile updated successfully
    - Changes persisted to database
    """
    # Arrange
    user = await seed_test_user(
        test_db_session,
        name="Old Name",
        with_profile=True,
    )
    await test_db_session.flush()

    # Act
    updated_profile = await user_profile_repository.update_profile(
        user_id=user.id,
        update_data={
            "name": "New Name",
            "bio": "Updated bio",
        },
    )
    await test_db_session.flush()

    # Assert
    assert updated_profile is not None
    assert updated_profile.name == "New Name"
    assert updated_profile.bio == "Updated bio"

    # Verify in database
    profile = await user_profile_repository.get_by_user_id(user.id)
    assert profile.name == "New Name"
    assert profile.bio == "Updated bio"
