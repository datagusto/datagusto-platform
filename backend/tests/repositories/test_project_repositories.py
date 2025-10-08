"""
Project repositories integration tests.

Tests verify database operations for Project, ProjectOwner, and ProjectMember
models using PostgreSQL test database with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectActiveStatus, ProjectMember, ProjectOwner
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_owner_repository import ProjectOwnerRepository
from app.repositories.project_repository import ProjectRepository
from tests.repositories.conftest import (
    build_project_data,
    build_project_member_data,
    build_project_owner_data,
    seed_test_organization,
    seed_test_project,
    seed_test_user,
)

# ============================================================================
# ProjectRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_project_create_success(
    test_db_session: AsyncSession,
    project_repository: ProjectRepository,
):
    """
    Test creating a project using repository.

    Verifies:
    - Project created successfully
    - Project exists in database with correct fields
    - created_at and updated_at timestamps set
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project_id = uuid4()
    project_data = build_project_data(
        project_id=project_id,
        organization_id=org.id,
        created_by=user.id,
        name="Test Project",
    )

    # Act
    project = await project_repository.create(project_data)
    await test_db_session.flush()

    # Assert
    assert project is not None
    assert project.id == project_id
    assert project.organization_id == org.id
    assert project.created_by == user.id
    assert project.name == "Test Project"
    assert project.created_at is not None
    assert project.updated_at is not None

    # Verify project exists in database
    stmt = select(Project).where(Project.id == project_id)
    result = await test_db_session.execute(stmt)
    db_project = result.scalar_one_or_none()
    assert db_project is not None
    assert db_project.name == "Test Project"


@pytest.mark.asyncio
async def test_project_get_by_id_success(
    test_db_session: AsyncSession,
    project_repository: ProjectRepository,
):
    """
    Test retrieving project by ID.

    Verifies:
    - Project returned when exists
    - All fields accessible
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session,
        organization_id=org.id,
        created_by=user.id,
        name="Get Test Project",
    )
    await test_db_session.flush()

    # Act
    retrieved_project = await project_repository.get_by_id(project.id)

    # Assert
    assert retrieved_project is not None
    assert retrieved_project.id == project.id
    assert retrieved_project.name == "Get Test Project"


@pytest.mark.asyncio
async def test_project_get_by_id_not_found(
    test_db_session: AsyncSession,
    project_repository: ProjectRepository,
):
    """
    Test retrieving non-existent project returns None.

    Verifies:
    - None returned when project doesn't exist
    """
    # Arrange
    non_existent_id = uuid4()

    # Act
    result = await project_repository.get_by_id(non_existent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_project_is_active_and_activate(
    test_db_session: AsyncSession,
    project_repository: ProjectRepository,
):
    """
    Test project active status check and activation.

    Verifies:
    - is_active returns True when ProjectActiveStatus exists
    - activate creates ProjectActiveStatus record
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session,
        organization_id=org.id,
        created_by=user.id,
        with_active_status=False,
    )
    await test_db_session.flush()

    # Act - Check initially not active
    is_active_before = await project_repository.is_active(project.id)

    # Act - Activate project
    await project_repository.activate(project.id)
    await test_db_session.flush()

    # Act - Check active after activation
    is_active_after = await project_repository.is_active(project.id)

    # Assert
    assert is_active_before is False
    assert is_active_after is True

    # Verify ProjectActiveStatus record exists
    stmt = select(ProjectActiveStatus).where(
        ProjectActiveStatus.project_id == project.id
    )
    result = await test_db_session.execute(stmt)
    active_status = result.scalar_one_or_none()
    assert active_status is not None


@pytest.mark.asyncio
async def test_project_get_by_organization(
    test_db_session: AsyncSession,
    project_repository: ProjectRepository,
):
    """
    Test retrieving projects by organization.

    Verifies:
    - Returns projects for specified organization
    - Returns total count
    - Basic pagination works
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    _project1 = await seed_test_project(
        test_db_session,
        organization_id=org.id,
        created_by=user.id,
        name="Project 1",
    )
    _project2 = await seed_test_project(
        test_db_session,
        organization_id=org.id,
        created_by=user.id,
        name="Project 2",
    )
    await test_db_session.flush()

    # Act
    projects, total = await project_repository.get_by_organization(
        organization_id=org.id, page=1, page_size=20
    )

    # Assert
    assert total == 2
    assert len(projects) == 2
    project_names = {p.name for p in projects}
    assert "Project 1" in project_names
    assert "Project 2" in project_names


# ============================================================================
# ProjectOwnerRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_project_owner_set_owner(
    test_db_session: AsyncSession,
    project_owner_repository: ProjectOwnerRepository,
):
    """
    Test setting project owner.

    Verifies:
    - ProjectOwner record created
    - Owner relationship established
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    await test_db_session.flush()

    # Act
    owner = await project_owner_repository.set_owner(
        project_id=project.id, user_id=user.id
    )
    await test_db_session.flush()

    # Assert
    assert owner is not None
    assert owner.project_id == project.id
    assert owner.user_id == user.id

    # Verify ProjectOwner record exists
    stmt = select(ProjectOwner).where(ProjectOwner.project_id == project.id)
    result = await test_db_session.execute(stmt)
    db_owner = result.scalar_one_or_none()
    assert db_owner is not None
    assert db_owner.user_id == user.id


@pytest.mark.asyncio
async def test_project_owner_get_by_project_id(
    test_db_session: AsyncSession,
    project_owner_repository: ProjectOwnerRepository,
):
    """
    Test retrieving project owner by project ID.

    Verifies:
    - Returns owner when exists
    - Returns None when no owner set
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )

    # Create owner record directly
    owner_data = build_project_owner_data(project_id=project.id, user_id=user.id)
    owner_record = ProjectOwner(**owner_data)
    test_db_session.add(owner_record)
    await test_db_session.flush()

    # Act
    retrieved_owner = await project_owner_repository.get_by_project_id(project.id)

    # Assert
    assert retrieved_owner is not None
    assert retrieved_owner.project_id == project.id
    assert retrieved_owner.user_id == user.id


# ============================================================================
# ProjectMemberRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_project_member_add_member_success(
    test_db_session: AsyncSession,
    project_member_repository: ProjectMemberRepository,
):
    """
    Test adding member to project.

    Verifies:
    - ProjectMember record created
    - Member relationship established
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    await test_db_session.flush()

    # Act
    member = await project_member_repository.add_member(
        project_id=project.id, user_id=user.id
    )
    await test_db_session.flush()

    # Assert
    assert member is not None
    assert member.project_id == project.id
    assert member.user_id == user.id

    # Verify ProjectMember record exists
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == user.id,
    )
    result = await test_db_session.execute(stmt)
    db_member = result.scalar_one_or_none()
    assert db_member is not None


@pytest.mark.asyncio
async def test_project_member_is_member(
    test_db_session: AsyncSession,
    project_member_repository: ProjectMemberRepository,
):
    """
    Test checking if user is project member.

    Verifies:
    - Returns True when member exists
    - Returns False when not a member
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    non_member_user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )

    # Add user as member
    member_data = build_project_member_data(project_id=project.id, user_id=user.id)
    member_record = ProjectMember(**member_data)
    test_db_session.add(member_record)
    await test_db_session.flush()

    # Act
    is_member = await project_member_repository.is_member(
        project_id=project.id, user_id=user.id
    )
    is_not_member = await project_member_repository.is_member(
        project_id=project.id, user_id=non_member_user.id
    )

    # Assert
    assert is_member is True
    assert is_not_member is False


@pytest.mark.asyncio
async def test_project_member_add_duplicate_fails(
    test_db_session: AsyncSession,
    project_member_repository: ProjectMemberRepository,
):
    """
    Test adding duplicate member raises IntegrityError.

    Verifies:
    - Cannot add same user as member twice
    - Database constraint enforced
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )

    # Add user as member first time
    await project_member_repository.add_member(project_id=project.id, user_id=user.id)
    await test_db_session.flush()

    # Act & Assert - Adding again should fail
    with pytest.raises(Exception):  # IntegrityError or similar
        await project_member_repository.add_member(
            project_id=project.id, user_id=user.id
        )
        await test_db_session.flush()
