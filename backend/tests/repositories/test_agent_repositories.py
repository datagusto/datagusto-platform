"""
Agent repositories integration tests.

Tests verify database operations for Agent and AgentAPIKey models using
PostgreSQL test database with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentActiveStatus, AgentAPIKey
from app.repositories.agent_api_key_repository import AgentAPIKeyRepository
from app.repositories.agent_repository import AgentRepository
from tests.repositories.conftest import (
    build_agent_api_key_data,
    build_agent_data,
    seed_test_agent,
    seed_test_organization,
    seed_test_project,
    seed_test_user,
)

# ============================================================================
# AgentRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_agent_create_success(
    test_db_session: AsyncSession,
    agent_repository: AgentRepository,
):
    """
    Test creating an agent using repository.

    Verifies:
    - Agent created successfully
    - Agent exists in database with correct fields
    - created_at and updated_at timestamps set
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent_id = uuid4()
    agent_data = build_agent_data(
        agent_id=agent_id,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
        name="Test Agent",
    )

    # Act
    agent = await agent_repository.create(agent_data)
    await test_db_session.flush()

    # Assert
    assert agent is not None
    assert agent.id == agent_id
    assert agent.project_id == project.id
    assert agent.organization_id == org.id
    assert agent.created_by == user.id
    assert agent.name == "Test Agent"
    assert agent.created_at is not None
    assert agent.updated_at is not None

    # Verify agent exists in database
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await test_db_session.execute(stmt)
    db_agent = result.scalar_one_or_none()
    assert db_agent is not None
    assert db_agent.name == "Test Agent"


@pytest.mark.asyncio
async def test_agent_get_by_id_success(
    test_db_session: AsyncSession,
    agent_repository: AgentRepository,
):
    """
    Test retrieving agent by ID.

    Verifies:
    - Agent returned when exists
    - All fields accessible
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent = await seed_test_agent(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
        name="Get Test Agent",
    )
    await test_db_session.flush()

    # Act
    retrieved_agent = await agent_repository.get_by_id(agent.id)

    # Assert
    assert retrieved_agent is not None
    assert retrieved_agent.id == agent.id
    assert retrieved_agent.name == "Get Test Agent"


@pytest.mark.asyncio
async def test_agent_get_by_id_not_found(
    test_db_session: AsyncSession,
    agent_repository: AgentRepository,
):
    """
    Test retrieving non-existent agent returns None.

    Verifies:
    - None returned when agent doesn't exist
    """
    # Arrange
    non_existent_id = uuid4()

    # Act
    result = await agent_repository.get_by_id(non_existent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_agent_is_active_and_activate(
    test_db_session: AsyncSession,
    agent_repository: AgentRepository,
):
    """
    Test agent active status check and activation.

    Verifies:
    - is_active returns True when AgentActiveStatus exists
    - activate creates AgentActiveStatus record
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent = await seed_test_agent(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
        with_active_status=False,
    )
    await test_db_session.flush()

    # Act - Check initially not active
    is_active_before = await agent_repository.is_active(agent.id)

    # Act - Activate agent
    await agent_repository.activate(agent.id)
    await test_db_session.flush()

    # Act - Check active after activation
    is_active_after = await agent_repository.is_active(agent.id)

    # Assert
    assert is_active_before is False
    assert is_active_after is True

    # Verify AgentActiveStatus record exists
    stmt = select(AgentActiveStatus).where(AgentActiveStatus.agent_id == agent.id)
    result = await test_db_session.execute(stmt)
    active_status = result.scalar_one_or_none()
    assert active_status is not None


# ============================================================================
# AgentAPIKeyRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_agent_api_key_create_with_prefix_and_hash(
    test_db_session: AsyncSession,
    agent_api_key_repository: AgentAPIKeyRepository,
):
    """
    Test creating agent API key with prefix and hash.

    Verifies:
    - API key created with prefix and hash
    - Prefix and hash stored correctly
    - created_at timestamp set
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent = await seed_test_agent(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )

    key_prefix = f"dgsk_{uuid4().hex[:11]}"
    key_hash = f"hashed_{uuid4().hex}"

    # Act
    api_key = await agent_api_key_repository.create(
        agent_id=agent.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by=user.id,
        name="Test API Key",
    )
    await test_db_session.flush()

    # Assert
    assert api_key is not None
    assert api_key.agent_id == agent.id
    assert api_key.key_prefix == key_prefix
    assert api_key.key_hash == key_hash
    assert api_key.name == "Test API Key"
    assert api_key.created_at is not None

    # Verify API key exists in database
    stmt = select(AgentAPIKey).where(AgentAPIKey.key_prefix == key_prefix)
    result = await test_db_session.execute(stmt)
    db_api_key = result.scalar_one_or_none()
    assert db_api_key is not None
    assert db_api_key.key_hash == key_hash


@pytest.mark.asyncio
async def test_agent_api_key_get_by_key_prefix(
    test_db_session: AsyncSession,
    agent_api_key_repository: AgentAPIKeyRepository,
):
    """
    Test retrieving API key by prefix for authentication.

    Verifies:
    - API key found by prefix
    - Used for authentication flow
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent = await seed_test_agent(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )

    key_prefix = f"dgsk_{uuid4().hex[:11]}"
    key_hash = f"hashed_{uuid4().hex}"
    api_key_data = build_agent_api_key_data(
        agent_id=agent.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by=user.id,
    )

    api_key_record = AgentAPIKey(**api_key_data)
    test_db_session.add(api_key_record)
    await test_db_session.flush()

    # Act
    retrieved_key = await agent_api_key_repository.get_by_key_prefix(key_prefix)

    # Assert
    assert retrieved_key is not None
    assert retrieved_key.key_prefix == key_prefix
    assert retrieved_key.key_hash == key_hash
    assert retrieved_key.agent_id == agent.id


@pytest.mark.asyncio
async def test_agent_api_key_update_last_used(
    test_db_session: AsyncSession,
    agent_api_key_repository: AgentAPIKeyRepository,
):
    """
    Test updating last_used_at timestamp for API key.

    Verifies:
    - last_used_at timestamp updated
    - Timestamp changes after update
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    agent = await seed_test_agent(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )

    key_prefix = f"dgsk_{uuid4().hex[:11]}"
    key_hash = f"hashed_{uuid4().hex}"
    api_key_data = build_agent_api_key_data(
        agent_id=agent.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by=user.id,
    )

    api_key_record = AgentAPIKey(**api_key_data)
    test_db_session.add(api_key_record)
    await test_db_session.flush()

    initial_last_used = api_key_record.last_used_at

    # Act
    await agent_api_key_repository.update_last_used(api_key_record.id)
    await test_db_session.flush()
    await test_db_session.refresh(api_key_record)

    # Assert
    assert api_key_record.last_used_at is not None
    if initial_last_used is not None:
        assert api_key_record.last_used_at >= initial_last_used
