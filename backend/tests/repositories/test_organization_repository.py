"""
OrganizationRepository integration tests.

Tests verify organization database operations using PostgreSQL test database
with transaction rollback for isolation.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_repository import OrganizationRepository
from tests.repositories.conftest import (
    seed_test_organization,
    seed_test_user,
    seed_test_membership,
    build_organization_data,
)
from tests.repositories.utils import (
    assert_organization_matches,
    query_organization_by_id,
)


# ============================================================================
# Test: create() - Create organization
# ============================================================================


@pytest.mark.asyncio
async def test_create_organization_success(
    test_db_session: AsyncSession,
    organization_repository: OrganizationRepository,
):
    """
    Test creating an organization using repository.

    Verifies:
    - Organization created successfully
    - Organization exists in database with correct ID
    - name field stored correctly
    - created_at and updated_at timestamps set
    """
    # Arrange
    org_id = uuid4()
    org_data = build_organization_data(org_id=org_id, name="Test Organization")

    # Act
    org = await organization_repository.create(org_data)
    await test_db_session.flush()

    # Assert
    assert org is not None
    assert org.id == org_id
    assert org.name == "Test Organization"
    assert org.created_at is not None
    assert org.updated_at is not None

    # Verify organization exists in database
    db_org = await query_organization_by_id(test_db_session, org_id)
    assert db_org is not None
    assert db_org.name == "Test Organization"


# ============================================================================
# Test: get_by_id_with_relations() - Organization with relations
# ============================================================================


@pytest.mark.asyncio
async def test_get_organization_with_relations(
    test_db_session: AsyncSession,
    organization_repository: OrganizationRepository,
):
    """
    Test retrieving organization with all relations.

    Verifies:
    - Organization returned with relations loaded
    - active_status and owner accessible
    - Relations eagerly loaded (no N+1 queries)
    """
    # Arrange
    org = await seed_test_organization(
        test_db_session,
        name="Relations Org",
        with_active_status=True,
    )
    user = await seed_test_user(test_db_session)
    await seed_test_membership(
        test_db_session,
        user_id=user.id,
        organization_id=org.id,
        is_owner=True,
    )
    await test_db_session.flush()

    # Act
    retrieved_org = await organization_repository.get_by_id_with_relations(org.id)

    # Assert
    assert retrieved_org is not None
    assert_organization_matches(
        retrieved_org,
        expected_id=org.id,
        expected_name="Relations Org",
        expected_active=True,
    )

    # Verify relations are eagerly loaded
    assert retrieved_org.active_status is not None
    assert retrieved_org.active_status.organization_id == org.id

    assert retrieved_org.owner is not None
    assert retrieved_org.owner.user_id == user.id


# ============================================================================
# Test: Status management methods
# ============================================================================


@pytest.mark.asyncio
async def test_activate_organization(
    test_db_session: AsyncSession,
    organization_repository: OrganizationRepository,
):
    """
    Test activating organization.

    Verifies:
    - Organization activated successfully
    - is_active() returns True after activation
    """
    # Arrange
    org = await seed_test_organization(
        test_db_session,
        with_active_status=False,
    )
    await test_db_session.flush()

    # Verify initially not active
    assert await organization_repository.is_active(org.id) is False

    # Act
    active_status = await organization_repository.activate(org.id)
    await test_db_session.flush()

    # Assert
    assert active_status is not None
    assert active_status.organization_id == org.id
    assert await organization_repository.is_active(org.id) is True


@pytest.mark.asyncio
async def test_deactivate_organization(
    test_db_session: AsyncSession,
    organization_repository: OrganizationRepository,
):
    """
    Test deactivating organization.

    Verifies:
    - Organization deactivated successfully
    - is_active() returns False after deactivation
    """
    # Arrange
    org = await seed_test_organization(
        test_db_session,
        with_active_status=True,
    )
    await test_db_session.flush()

    # Verify initially active
    assert await organization_repository.is_active(org.id) is True

    # Act
    deactivated = await organization_repository.deactivate(org.id)
    await test_db_session.flush()

    # Assert
    assert deactivated is True
    assert await organization_repository.is_active(org.id) is False


# ============================================================================
# Test: list_active() - Filtering active organizations
# ============================================================================


@pytest.mark.asyncio
async def test_list_active_organizations(
    test_db_session: AsyncSession,
    organization_repository: OrganizationRepository,
):
    """
    Test listing only active organizations.

    Verifies:
    - Only active organizations returned
    - Correct filtering applied
    - Inactive organizations excluded
    """
    # Arrange - Create 3 organizations: 2 active, 1 inactive
    org1 = await seed_test_organization(
        test_db_session,
        name="Active Org 1",
        with_active_status=True,
    )
    org2 = await seed_test_organization(
        test_db_session,
        name="Active Org 2",
        with_active_status=True,
    )
    org3 = await seed_test_organization(
        test_db_session,
        name="Inactive Org",
        with_active_status=False,
    )
    await test_db_session.flush()

    # Act
    active_orgs = await organization_repository.list_active()

    # Assert
    assert len(active_orgs) == 2
    active_ids = [org.id for org in active_orgs]
    assert org1.id in active_ids
    assert org2.id in active_ids
    assert org3.id not in active_ids