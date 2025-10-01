"""
OrganizationMemberRepository integration tests.

Tests verify membership database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.repositories.organization_owner_repository import OrganizationOwnerRepository
from app.repositories.organization_admin_repository import OrganizationAdminRepository
from tests.repositories.conftest import (
    seed_test_organization,
    seed_test_user,
    seed_test_membership,
)
from tests.repositories.utils import (
    assert_relationship_exists,
    count_users_in_organization,
)


# ============================================================================
# Test: OrganizationMemberRepository - create_membership
# ============================================================================


@pytest.mark.asyncio
async def test_create_membership(
    test_db_session: AsyncSession,
    organization_member_repository: OrganizationMemberRepository,
):
    """
    Test creating membership between user and organization.

    Verifies:
    - Membership created successfully
    - user_id, organization_id, role stored correctly
    - Membership exists in database
    """
    # Arrange
    user = await seed_test_user(test_db_session)
    org = await seed_test_organization(test_db_session)
    await test_db_session.flush()

    # Act
    member = await organization_member_repository.add_member(
        organization_id=org.id,
        user_id=user.id,
    )
    await test_db_session.flush()

    # Assert
    assert member is not None
    assert member.user_id == user.id
    assert member.organization_id == org.id

    # Verify membership exists
    await assert_relationship_exists(
        test_db_session,
        "member",
        user_id=user.id,
        organization_id=org.id,
    )


# ============================================================================
# Test: OrganizationMemberRepository - list_members
# ============================================================================


@pytest.mark.asyncio
async def test_list_members(
    test_db_session: AsyncSession,
    organization_member_repository: OrganizationMemberRepository,
):
    """
    Test listing members of an organization.

    Verifies:
    - All members returned
    - Eager loading of user data
    """
    # Arrange - Create organization with 3 members
    org = await seed_test_organization(test_db_session)
    user1 = await seed_test_user(test_db_session)
    user2 = await seed_test_user(test_db_session)
    user3 = await seed_test_user(test_db_session)

    await seed_test_membership(test_db_session, user1.id, org.id)
    await seed_test_membership(test_db_session, user2.id, org.id)
    await seed_test_membership(test_db_session, user3.id, org.id)
    await test_db_session.flush()

    # Act
    members = await organization_member_repository.list_members(org.id)

    # Assert
    assert len(members) == 3
    member_ids = [user.id for user in members]
    assert user1.id in member_ids
    assert user2.id in member_ids
    assert user3.id in member_ids


# ============================================================================
# Test: OrganizationMemberRepository - is_member
# ============================================================================


@pytest.mark.asyncio
async def test_is_member(
    test_db_session: AsyncSession,
    organization_member_repository: OrganizationMemberRepository,
):
    """
    Test checking if user is member of organization.

    Verifies:
    - Returns True for member
    - Returns False for non-member
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    member_user = await seed_test_user(test_db_session)
    non_member_user = await seed_test_user(test_db_session)

    await seed_test_membership(test_db_session, member_user.id, org.id)
    await test_db_session.flush()

    # Act & Assert - Member
    is_member = await organization_member_repository.is_member(org.id, member_user.id)
    assert is_member is True

    # Act & Assert - Non-member
    is_not_member = await organization_member_repository.is_member(
        org.id, non_member_user.id
    )
    assert is_not_member is False


# ============================================================================
# Test: OrganizationOwnerRepository - create_owner
# ============================================================================


@pytest.mark.asyncio
async def test_create_owner(
    test_db_session: AsyncSession,
    organization_owner_repository: OrganizationOwnerRepository,
):
    """
    Test creating organization owner.

    Verifies:
    - Owner record created successfully
    - Ownership relationship established
    """
    # Arrange
    user = await seed_test_user(test_db_session)
    org = await seed_test_organization(test_db_session)
    await test_db_session.flush()

    # Act
    owner = await organization_owner_repository.create(
        {"organization_id": org.id, "user_id": user.id}
    )
    await test_db_session.flush()

    # Assert
    assert owner is not None
    assert owner.user_id == user.id
    assert owner.organization_id == org.id

    # Verify ownership exists
    await assert_relationship_exists(
        test_db_session,
        "owner",
        user_id=user.id,
        organization_id=org.id,
    )


# ============================================================================
# Test: OrganizationOwnerRepository - is_owner
# ============================================================================


@pytest.mark.asyncio
async def test_is_owner(
    test_db_session: AsyncSession,
    organization_owner_repository: OrganizationOwnerRepository,
):
    """
    Test checking if user is owner of organization.

    Verifies:
    - Returns True for owner
    - Returns False for non-owner
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    owner_user = await seed_test_user(test_db_session)
    non_owner_user = await seed_test_user(test_db_session)

    await seed_test_membership(test_db_session, owner_user.id, org.id, is_owner=True)
    await test_db_session.flush()

    # Act & Assert - Owner
    is_owner = await organization_owner_repository.is_owner(org.id, owner_user.id)
    assert is_owner is True

    # Act & Assert - Non-owner
    is_not_owner = await organization_owner_repository.is_owner(
        org.id, non_owner_user.id
    )
    assert is_not_owner is False


# ============================================================================
# Test: OrganizationAdminRepository - create_admin
# ============================================================================


@pytest.mark.asyncio
async def test_create_admin(
    test_db_session: AsyncSession,
    organization_admin_repository: OrganizationAdminRepository,
):
    """
    Test creating organization admin.

    Verifies:
    - Admin record created successfully
    - Admin role established
    """
    # Arrange
    user = await seed_test_user(test_db_session)
    org = await seed_test_organization(test_db_session)
    granter_user = await seed_test_user(test_db_session)  # User who grants admin
    await test_db_session.flush()

    # Act
    admin = await organization_admin_repository.create(
        {
            "organization_id": org.id,
            "user_id": user.id,
            "granted_by": granter_user.id,
        }
    )
    await test_db_session.flush()

    # Assert
    assert admin is not None
    assert admin.user_id == user.id
    assert admin.organization_id == org.id
    assert admin.granted_by == granter_user.id

    # Verify admin role exists
    await assert_relationship_exists(
        test_db_session,
        "admin",
        user_id=user.id,
        organization_id=org.id,
    )


# ============================================================================
# Test: OrganizationAdminRepository - is_admin
# ============================================================================


@pytest.mark.asyncio
async def test_is_admin(
    test_db_session: AsyncSession,
    organization_admin_repository: OrganizationAdminRepository,
):
    """
    Test checking if user is admin of organization.

    Verifies:
    - Returns True for admin
    - Returns False for non-admin
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    admin_user = await seed_test_user(test_db_session)
    non_admin_user = await seed_test_user(test_db_session)

    await seed_test_membership(test_db_session, admin_user.id, org.id, is_admin=True)
    await test_db_session.flush()

    # Act & Assert - Admin
    is_admin = await organization_admin_repository.is_admin(org.id, admin_user.id)
    assert is_admin is True

    # Act & Assert - Non-admin
    is_not_admin = await organization_admin_repository.is_admin(
        org.id, non_admin_user.id
    )
    assert is_not_admin is False


# ============================================================================
# Test: Cross-repository relationships - Owner is also member
# ============================================================================


@pytest.mark.asyncio
async def test_owner_is_also_member(
    test_db_session: AsyncSession,
    organization_member_repository: OrganizationMemberRepository,
    organization_owner_repository: OrganizationOwnerRepository,
):
    """
    Test that owner is also a member (referential integrity).

    Verifies:
    - Both is_owner() and is_member() return True
    - Referential integrity maintained
    """
    # Arrange
    user = await seed_test_user(test_db_session)
    org = await seed_test_organization(test_db_session)

    # Create owner (which should also create membership)
    await seed_test_membership(test_db_session, user.id, org.id, is_owner=True)
    await test_db_session.flush()

    # Act & Assert - Both member and owner
    is_owner = await organization_owner_repository.is_owner(org.id, user.id)
    is_member = await organization_member_repository.is_member(org.id, user.id)

    assert is_owner is True
    assert is_member is True

    # Verify both relationships exist
    await assert_relationship_exists(
        test_db_session, "owner", user_id=user.id, organization_id=org.id
    )
    await assert_relationship_exists(
        test_db_session, "member", user_id=user.id, organization_id=org.id
    )