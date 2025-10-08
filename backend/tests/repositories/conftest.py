"""
Repository-specific pytest fixtures.

This module provides fixtures for repository testing with PostgreSQL test database.
All fixtures use the test_db_session from parent conftest.py with transaction rollback.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import (
    Agent,
    AgentActiveStatus,
    AgentAPIKey,
    AgentArchive,
)
from app.models.guardrail import (
    Guardrail,
    GuardrailActiveStatus,
    GuardrailAgentAssignment,
    GuardrailArchive,
)
from app.models.organization import (
    Organization,
    OrganizationActiveStatus,
    OrganizationAdmin,
    OrganizationMember,
    OrganizationOwner,
)

# Phase 7 models
from app.models.project import (
    Project,
    ProjectActiveStatus,
    ProjectArchive,
    ProjectMember,
    ProjectOwner,
)
from app.models.trace import (
    Observation,
    ObservationArchive,
    Trace,
    TraceArchive,
)
from app.models.user import (
    User,
    UserActiveStatus,
    UserLoginPassword,
    UserProfile,
)
from app.repositories.agent_api_key_repository import AgentAPIKeyRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.guardrail_assignment_repository import (
    GuardrailAssignmentRepository,
)
from app.repositories.guardrail_repository import GuardrailRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.organization_admin_repository import OrganizationAdminRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.organization_owner_repository import OrganizationOwnerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_owner_repository import ProjectOwnerRepository

# Phase 7 repositories
from app.repositories.project_repository import ProjectRepository
from app.repositories.trace_repository import TraceRepository
from app.repositories.user_auth_repository import UserAuthRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_status_repository import UserStatusRepository

# ============================================================================
# Test Data Builders
# ============================================================================


def build_user_data(user_id: UUID | None = None, **overrides) -> dict[str, Any]:
    """
    Build valid user data dictionary for testing.

    Args:
        user_id: User UUID (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with user data

    Example:
        >>> data = build_user_data()
        >>> user = User(**data)
        >>> session.add(user)
    """
    if user_id is None:
        user_id = uuid4()

    data = {"id": user_id}
    data.update(overrides)
    return data


def build_profile_data(
    user_id: UUID, name: str | None = None, **overrides
) -> dict[str, Any]:
    """
    Build valid user profile data dictionary for testing.

    Args:
        user_id: User UUID (required)
        name: User name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with profile data

    Example:
        >>> data = build_profile_data(user.id, name="John Doe")
        >>> profile = UserProfile(**data)
        >>> session.add(profile)
    """
    if name is None:
        name = f"Test User {user_id.hex[:8]}"

    data = {
        "user_id": user_id,
        "name": name,
        "bio": f"Bio for {name}",
        "avatar_url": f"https://example.com/avatar/{user_id.hex[:8]}.png",
    }
    data.update(overrides)
    return data


def build_user_auth_data(
    user_id: UUID, email: str | None = None, **overrides
) -> dict[str, Any]:
    """
    Build valid user authentication data dictionary for testing.

    Args:
        user_id: User UUID (required)
        email: User email (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with auth data

    Example:
        >>> data = build_user_auth_data(user.id, email="test@example.com")
        >>> auth = UserLoginPassword(**data)
        >>> session.add(auth)
    """
    if email is None:
        email = f"user{user_id.hex[:8]}@test.com"

    data = {
        "user_id": user_id,
        "email": email,
        "hashed_password": "hashed_password_123",
    }
    data.update(overrides)
    return data


def build_organization_data(
    org_id: UUID | None = None, name: str | None = None, **overrides
) -> dict[str, Any]:
    """
    Build valid organization data dictionary for testing.

    Args:
        org_id: Organization UUID (auto-generated if not provided)
        name: Organization name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with organization data

    Example:
        >>> data = build_organization_data(name="Acme Corp")
        >>> org = Organization(**data)
        >>> session.add(org)
    """
    if org_id is None:
        org_id = uuid4()
    if name is None:
        name = f"Test Organization {org_id.hex[:8]}"

    data = {"id": org_id, "name": name}
    data.update(overrides)
    return data


def build_membership_data(
    user_id: UUID, organization_id: UUID, **overrides
) -> dict[str, Any]:
    """
    Build valid organization membership data dictionary for testing.

    Args:
        user_id: User UUID (required)
        organization_id: Organization UUID (required)
        **overrides: Override default values

    Returns:
        Dict with membership data

    Example:
        >>> data = build_membership_data(user.id, org.id)
        >>> member = OrganizationMember(**data)
        >>> session.add(member)
    """
    data = {
        "user_id": user_id,
        "organization_id": organization_id,
    }
    data.update(overrides)
    return data


# ============================================================================
# Database Seeding Utilities
# ============================================================================


async def seed_test_user(
    session: AsyncSession,
    user_id: UUID | None = None,
    email: str | None = None,
    name: str | None = None,
    password_hash: str = "hashed_password_123",
    with_profile: bool = True,
    with_auth: bool = True,
    with_active_status: bool = True,
) -> User:
    """
    Create a test user with optional related records.

    Args:
        session: Database session
        user_id: User UUID (auto-generated if not provided)
        email: User email (auto-generated if not provided)
        name: User name (auto-generated if not provided)
        password_hash: Password hash for auth record
        with_profile: Create UserProfile record
        with_auth: Create UserLoginPassword record
        with_active_status: Create UserActiveStatus record

    Returns:
        User: Created user with relations

    Example:
        >>> user = await seed_test_user(session, email="test@example.com")
        >>> assert user.profile.name is not None
        >>> assert user.login_password.email == "test@example.com"
    """
    if user_id is None:
        user_id = uuid4()
    if email is None:
        email = f"user{user_id.hex[:8]}@test.com"
    if name is None:
        name = f"Test User {user_id.hex[:8]}"

    # Create user
    user = User(id=user_id)
    session.add(user)
    await session.flush()

    # Create related records
    if with_profile:
        profile = UserProfile(user_id=user.id, name=name, bio=f"Bio for {name}")
        session.add(profile)

    if with_auth:
        login_password = UserLoginPassword(
            user_id=user.id, email=email, hashed_password=password_hash
        )
        session.add(login_password)

    if with_active_status:
        active_status = UserActiveStatus(user_id=user.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(user)
    return user


async def seed_test_organization(
    session: AsyncSession,
    org_id: UUID | None = None,
    name: str | None = None,
    with_active_status: bool = True,
) -> Organization:
    """
    Create a test organization with optional related records.

    Args:
        session: Database session
        org_id: Organization UUID (auto-generated if not provided)
        name: Organization name (auto-generated if not provided)
        with_active_status: Create OrganizationActiveStatus record

    Returns:
        Organization: Created organization with relations

    Example:
        >>> org = await seed_test_organization(session, name="Test Org")
        >>> assert org.name == "Test Org"
        >>> assert org.active_status is not None
    """
    if org_id is None:
        org_id = uuid4()
    if name is None:
        name = f"Test Organization {org_id.hex[:8]}"

    # Create organization
    org = Organization(id=org_id, name=name)
    session.add(org)
    await session.flush()

    # Create related records
    if with_active_status:
        active_status = OrganizationActiveStatus(organization_id=org.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(org)
    return org


async def seed_test_membership(
    session: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    is_owner: bool = False,
    is_admin: bool = False,
    granted_by: UUID | None = None,
) -> OrganizationMember:
    """
    Create a test membership between user and organization.

    Args:
        session: Database session
        user_id: User UUID
        organization_id: Organization UUID
        is_owner: Create OrganizationOwner record
        is_admin: Create OrganizationAdmin record
        granted_by: User who granted admin privilege (required if is_admin=True)

    Returns:
        OrganizationMember: Created membership record

    Example:
        >>> user = await seed_test_user(session)
        >>> org = await seed_test_organization(session)
        >>> member = await seed_test_membership(
        ...     session, user.id, org.id, is_owner=True
        ... )
    """
    # Create membership
    member = OrganizationMember(organization_id=organization_id, user_id=user_id)
    session.add(member)
    await session.flush()

    # Create role records
    if is_owner:
        owner = OrganizationOwner(organization_id=organization_id, user_id=user_id)
        session.add(owner)

    if is_admin:
        if granted_by is None:
            granted_by = user_id  # Default to self-granted for tests
        admin = OrganizationAdmin(
            organization_id=organization_id, user_id=user_id, granted_by=granted_by
        )
        session.add(admin)

    await session.flush()
    return member


# ============================================================================
# Repository Factory Fixtures
# ============================================================================


@pytest.fixture
def user_repository(test_db_session: AsyncSession) -> UserRepository:
    """
    UserRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserRepository: Repository instance for testing
    """
    return UserRepository(test_db_session)


@pytest.fixture
def user_auth_repository(test_db_session: AsyncSession) -> UserAuthRepository:
    """
    UserAuthRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserAuthRepository: Repository instance for testing
    """
    return UserAuthRepository(test_db_session)


@pytest.fixture
def user_profile_repository(test_db_session: AsyncSession) -> UserProfileRepository:
    """
    UserProfileRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserProfileRepository: Repository instance for testing
    """
    return UserProfileRepository(test_db_session)


@pytest.fixture
def user_status_repository(test_db_session: AsyncSession) -> UserStatusRepository:
    """
    UserStatusRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        UserStatusRepository: Repository instance for testing
    """
    return UserStatusRepository(test_db_session)


@pytest.fixture
def organization_repository(test_db_session: AsyncSession) -> OrganizationRepository:
    """
    OrganizationRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationRepository: Repository instance for testing
    """
    return OrganizationRepository(test_db_session)


@pytest.fixture
def organization_member_repository(
    test_db_session: AsyncSession,
) -> OrganizationMemberRepository:
    """
    OrganizationMemberRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationMemberRepository: Repository instance for testing
    """
    return OrganizationMemberRepository(test_db_session)


@pytest.fixture
def organization_owner_repository(
    test_db_session: AsyncSession,
) -> OrganizationOwnerRepository:
    """
    OrganizationOwnerRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationOwnerRepository: Repository instance for testing
    """
    return OrganizationOwnerRepository(test_db_session)


@pytest.fixture
def organization_admin_repository(
    test_db_session: AsyncSession,
) -> OrganizationAdminRepository:
    """
    OrganizationAdminRepository instance with test database session.

    Args:
        test_db_session: Test database session with transaction rollback

    Returns:
        OrganizationAdminRepository: Repository instance for testing
    """
    return OrganizationAdminRepository(test_db_session)


# ============================================================================
# Phase 7 Repository Factory Fixtures
# ============================================================================


@pytest.fixture
def project_repository(test_db_session: AsyncSession) -> ProjectRepository:
    """ProjectRepository instance with test database session."""
    return ProjectRepository(test_db_session)


@pytest.fixture
def project_owner_repository(test_db_session: AsyncSession) -> ProjectOwnerRepository:
    """ProjectOwnerRepository instance with test database session."""
    return ProjectOwnerRepository(test_db_session)


@pytest.fixture
def project_member_repository(
    test_db_session: AsyncSession,
) -> ProjectMemberRepository:
    """ProjectMemberRepository instance with test database session."""
    return ProjectMemberRepository(test_db_session)


@pytest.fixture
def agent_repository(test_db_session: AsyncSession) -> AgentRepository:
    """AgentRepository instance with test database session."""
    return AgentRepository(test_db_session)


@pytest.fixture
def agent_api_key_repository(
    test_db_session: AsyncSession,
) -> AgentAPIKeyRepository:
    """AgentAPIKeyRepository instance with test database session."""
    return AgentAPIKeyRepository(test_db_session)


@pytest.fixture
def guardrail_repository(test_db_session: AsyncSession) -> GuardrailRepository:
    """GuardrailRepository instance with test database session."""
    return GuardrailRepository(test_db_session)


@pytest.fixture
def guardrail_assignment_repository(
    test_db_session: AsyncSession,
) -> GuardrailAssignmentRepository:
    """GuardrailAssignmentRepository instance with test database session."""
    return GuardrailAssignmentRepository(test_db_session)


@pytest.fixture
def trace_repository(test_db_session: AsyncSession) -> TraceRepository:
    """TraceRepository instance with test database session."""
    return TraceRepository(test_db_session)


@pytest.fixture
def observation_repository(test_db_session: AsyncSession) -> ObservationRepository:
    """ObservationRepository instance with test database session."""
    return ObservationRepository(test_db_session)


# ============================================================================
# Phase 7 Test Data Builders
# ============================================================================


# Project builders
def build_project_data(
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build valid project data dictionary for testing.

    Args:
        project_id: Project UUID (auto-generated if not provided)
        organization_id: Organization UUID (required)
        created_by: User who created the project (required)
        name: Project name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with project data
    """
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Project {project_id.hex[:8]}"

    data = {
        "id": project_id,
        "organization_id": organization_id,
        "created_by": created_by,
        "name": name,
    }
    data.update(overrides)
    return data


def build_project_owner_data(
    project_id: UUID, user_id: UUID, **overrides
) -> dict[str, Any]:
    """Build valid project owner data dictionary for testing."""
    data = {
        "project_id": project_id,
        "user_id": user_id,
    }
    data.update(overrides)
    return data


def build_project_member_data(
    project_id: UUID, user_id: UUID, **overrides
) -> dict[str, Any]:
    """Build valid project member data dictionary for testing."""
    data = {
        "project_id": project_id,
        "user_id": user_id,
    }
    data.update(overrides)
    return data


# Agent builders
def build_agent_data(
    agent_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build valid agent data dictionary for testing.

    Args:
        agent_id: Agent UUID (auto-generated if not provided)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)
        created_by: User who created the agent (required)
        name: Agent name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with agent data
    """
    if agent_id is None:
        agent_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Agent {agent_id.hex[:8]}"

    data = {
        "id": agent_id,
        "project_id": project_id,
        "organization_id": organization_id,
        "created_by": created_by,
        "name": name,
    }
    data.update(overrides)
    return data


def build_agent_api_key_data(
    agent_id: UUID,
    key_prefix: str | None = None,
    key_hash: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """Build valid agent API key data dictionary for testing."""
    if key_prefix is None:
        key_prefix = f"dgsk_{uuid4().hex[:11]}"
    if key_hash is None:
        key_hash = f"hashed_{uuid4().hex}"

    data = {
        "agent_id": agent_id,
        "key_prefix": key_prefix,
        "key_hash": key_hash,
        "name": "Test API Key",
    }
    data.update(overrides)
    return data


# Guardrail builders
def build_guardrail_data(
    guardrail_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build valid guardrail data dictionary for testing.

    Args:
        guardrail_id: Guardrail UUID (auto-generated if not provided)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)
        created_by: User who created the guardrail (required)
        name: Guardrail name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with guardrail data
    """
    if guardrail_id is None:
        guardrail_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Guardrail {guardrail_id.hex[:8]}"

    data = {
        "id": guardrail_id,
        "project_id": project_id,
        "organization_id": organization_id,
        "created_by": created_by,
        "name": name,
        "definition": {"type": "test", "rules": []},
    }
    data.update(overrides)
    return data


def build_guardrail_assignment_data(
    guardrail_id: UUID,
    agent_id: UUID,
    project_id: UUID,
    assigned_by: UUID,
    **overrides,
) -> dict[str, Any]:
    """Build valid guardrail assignment data dictionary for testing."""
    data = {
        "guardrail_id": guardrail_id,
        "agent_id": agent_id,
        "project_id": project_id,
        "assigned_by": assigned_by,
    }
    data.update(overrides)
    return data


# Trace builders
def build_trace_data(
    trace_id: UUID | None = None,
    agent_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build valid trace data dictionary for testing.

    Args:
        trace_id: Trace UUID (auto-generated if not provided)
        agent_id: Agent UUID (required)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)
        **overrides: Override default values

    Returns:
        Dict with trace data
    """
    from datetime import datetime, timezone

    if trace_id is None:
        trace_id = uuid4()
    if agent_id is None:
        agent_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()

    data = {
        "id": trace_id,
        "agent_id": agent_id,
        "project_id": project_id,
        "organization_id": organization_id,
        "status": "pending",
        "started_at": datetime.now(UTC),
        "trace_metadata": {"test": True},
    }
    data.update(overrides)
    return data


def build_observation_data(
    observation_id: UUID | None = None,
    trace_id: UUID | None = None,
    parent_observation_id: UUID | None = None,
    name: str | None = None,
    **overrides,
) -> dict[str, Any]:
    """
    Build valid observation data dictionary for testing.

    Args:
        observation_id: Observation UUID (auto-generated if not provided)
        trace_id: Trace UUID (required)
        parent_observation_id: Parent observation UUID (optional for tree structure)
        name: Observation name (auto-generated if not provided)
        **overrides: Override default values

    Returns:
        Dict with observation data
    """
    from datetime import datetime, timezone

    if observation_id is None:
        observation_id = uuid4()
    if trace_id is None:
        trace_id = uuid4()
    if name is None:
        name = f"Test Observation {observation_id.hex[:8]}"

    data = {
        "id": observation_id,
        "trace_id": trace_id,
        "parent_observation_id": parent_observation_id,
        "name": name,
        "type": "span",
        "status": "pending",
        "started_at": datetime.now(UTC),
        "observation_metadata": {"test": True},
    }
    data.update(overrides)
    return data


# ============================================================================
# Phase 7 Database Seeding Utilities
# ============================================================================


async def seed_test_project(
    session: AsyncSession,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    with_active_status: bool = True,
) -> Project:
    """
    Create a test project with optional related records.

    Args:
        session: Database session
        project_id: Project UUID (auto-generated if not provided)
        organization_id: Organization UUID (required)
        created_by: User who created the project (required)
        name: Project name (auto-generated if not provided)
        with_active_status: Create ProjectActiveStatus record

    Returns:
        Project: Created project with relations
    """
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Project {project_id.hex[:8]}"

    # Create project
    project = Project(
        id=project_id,
        organization_id=organization_id,
        created_by=created_by,
        name=name,
    )
    session.add(project)
    await session.flush()

    # Create related records
    if with_active_status:
        active_status = ProjectActiveStatus(project_id=project.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(project)
    return project


async def seed_test_agent(
    session: AsyncSession,
    agent_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    with_active_status: bool = True,
) -> Agent:
    """
    Create a test agent with optional related records.

    Args:
        session: Database session
        agent_id: Agent UUID (auto-generated if not provided)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)
        created_by: User who created the agent (required)
        name: Agent name (auto-generated if not provided)
        with_active_status: Create AgentActiveStatus record

    Returns:
        Agent: Created agent with relations
    """
    if agent_id is None:
        agent_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Agent {agent_id.hex[:8]}"

    # Create agent
    agent = Agent(
        id=agent_id,
        project_id=project_id,
        organization_id=organization_id,
        created_by=created_by,
        name=name,
    )
    session.add(agent)
    await session.flush()

    # Create related records
    if with_active_status:
        active_status = AgentActiveStatus(agent_id=agent.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(agent)
    return agent


async def seed_test_guardrail(
    session: AsyncSession,
    guardrail_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
    created_by: UUID | None = None,
    name: str | None = None,
    with_active_status: bool = True,
) -> Guardrail:
    """
    Create a test guardrail with optional related records.

    Args:
        session: Database session
        guardrail_id: Guardrail UUID (auto-generated if not provided)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)
        created_by: User who created the guardrail (required)
        name: Guardrail name (auto-generated if not provided)
        with_active_status: Create GuardrailActiveStatus record

    Returns:
        Guardrail: Created guardrail with relations
    """
    if guardrail_id is None:
        guardrail_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()
    if created_by is None:
        created_by = uuid4()
    if name is None:
        name = f"Test Guardrail {guardrail_id.hex[:8]}"

    # Create guardrail
    guardrail = Guardrail(
        id=guardrail_id,
        project_id=project_id,
        organization_id=organization_id,
        created_by=created_by,
        name=name,
        definition={"type": "test", "rules": []},
    )
    session.add(guardrail)
    await session.flush()

    # Create related records
    if with_active_status:
        active_status = GuardrailActiveStatus(guardrail_id=guardrail.id)
        session.add(active_status)

    await session.flush()
    await session.refresh(guardrail)
    return guardrail


async def seed_test_trace(
    session: AsyncSession,
    trace_id: UUID | None = None,
    agent_id: UUID | None = None,
    project_id: UUID | None = None,
    organization_id: UUID | None = None,
) -> Trace:
    """
    Create a test trace.

    Args:
        session: Database session
        trace_id: Trace UUID (auto-generated if not provided)
        agent_id: Agent UUID (required)
        project_id: Project UUID (required)
        organization_id: Organization UUID (required)

    Returns:
        Trace: Created trace
    """
    from datetime import datetime, timezone

    if trace_id is None:
        trace_id = uuid4()
    if agent_id is None:
        agent_id = uuid4()
    if project_id is None:
        project_id = uuid4()
    if organization_id is None:
        organization_id = uuid4()

    # Create trace
    trace = Trace(
        id=trace_id,
        agent_id=agent_id,
        project_id=project_id,
        organization_id=organization_id,
        status="pending",
        started_at=datetime.now(UTC),
        trace_metadata={"test": True},
    )
    session.add(trace)
    await session.flush()
    await session.refresh(trace)
    return trace


async def seed_test_observation(
    session: AsyncSession,
    observation_id: UUID | None = None,
    trace_id: UUID | None = None,
    parent_observation_id: UUID | None = None,
    name: str | None = None,
) -> Observation:
    """
    Create a test observation.

    Args:
        session: Database session
        observation_id: Observation UUID (auto-generated if not provided)
        trace_id: Trace UUID (required)
        parent_observation_id: Parent observation UUID (optional for tree structure)
        name: Observation name (auto-generated if not provided)

    Returns:
        Observation: Created observation
    """
    from datetime import datetime, timezone

    if observation_id is None:
        observation_id = uuid4()
    if trace_id is None:
        trace_id = uuid4()
    if name is None:
        name = f"Test Observation {observation_id.hex[:8]}"

    # Create observation
    observation = Observation(
        id=observation_id,
        trace_id=trace_id,
        parent_observation_id=parent_observation_id,
        name=name,
        type="span",
        status="pending",
        started_at=datetime.now(UTC),
        observation_metadata={"test": True},
    )
    session.add(observation)
    await session.flush()
    await session.refresh(observation)
    return observation
