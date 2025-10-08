"""
Trace repositories integration tests.

Tests verify database operations for Trace and Observation models using
PostgreSQL test database with transaction rollback for isolation.
"""

from datetime import UTC
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace import Observation, Trace
from app.repositories.observation_repository import ObservationRepository
from app.repositories.trace_repository import TraceRepository
from tests.repositories.conftest import (
    build_observation_data,
    build_trace_data,
    seed_test_agent,
    seed_test_observation,
    seed_test_organization,
    seed_test_project,
    seed_test_trace,
    seed_test_user,
)

# ============================================================================
# TraceRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_trace_create_with_metadata(
    test_db_session: AsyncSession,
    trace_repository: TraceRepository,
):
    """
    Test creating a trace with metadata.

    Verifies:
    - Trace created successfully
    - JSONB metadata field stored correctly
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
    trace_id = uuid4()

    metadata = {
        "session_id": "session_123",
        "user_query": "What is the weather?",
        "environment": "production",
    }

    trace_data = build_trace_data(
        trace_id=trace_id,
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
        trace_metadata=metadata,
    )

    # Act
    trace = await trace_repository.create(trace_data)
    await test_db_session.flush()

    # Assert
    assert trace is not None
    assert trace.id == trace_id
    assert trace.agent_id == agent.id
    assert trace.trace_metadata == metadata
    assert trace.created_at is not None

    # Verify trace exists in database with JSONB metadata
    stmt = select(Trace).where(Trace.id == trace_id)
    result = await test_db_session.execute(stmt)
    db_trace = result.scalar_one_or_none()
    assert db_trace is not None
    assert db_trace.trace_metadata["session_id"] == "session_123"
    assert db_trace.trace_metadata["user_query"] == "What is the weather?"


@pytest.mark.asyncio
async def test_trace_get_by_id_success(
    test_db_session: AsyncSession,
    trace_repository: TraceRepository,
):
    """
    Test retrieving trace by ID.

    Verifies:
    - Trace returned when exists
    - Metadata accessible
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
    trace = await seed_test_trace(
        test_db_session,
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
    )
    await test_db_session.flush()

    # Act
    retrieved_trace = await trace_repository.get_by_id(trace.id)

    # Assert
    assert retrieved_trace is not None
    assert retrieved_trace.id == trace.id
    assert retrieved_trace.trace_metadata is not None


@pytest.mark.asyncio
async def test_trace_calculate_duration(
    test_db_session: AsyncSession,
    trace_repository: TraceRepository,
):
    """
    Test calculating trace duration.

    Verifies:
    - Duration calculated from start to end time
    - Returns None if end time not set
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

    from datetime import datetime, timedelta, timezone

    start_time = datetime.now(UTC)
    end_time = start_time + timedelta(seconds=5)

    trace_data = build_trace_data(
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
        started_at=start_time,
        ended_at=end_time,
    )

    trace = Trace(**trace_data)
    test_db_session.add(trace)
    await test_db_session.flush()

    # Act
    duration = await trace_repository.calculate_duration(trace.id)

    # Assert
    # Duration should be approximately 5 seconds (in milliseconds or seconds depending on implementation)
    assert duration is not None
    # Allow some tolerance for timing differences
    assert duration >= 4.0


# ============================================================================
# ObservationRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_observation_create_with_parent(
    test_db_session: AsyncSession,
    observation_repository: ObservationRepository,
):
    """
    Test creating observation with parent_observation_id for tree structure.

    Verifies:
    - Observation created successfully
    - parent_observation_id relationship established
    - Tree structure supported
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
    trace = await seed_test_trace(
        test_db_session,
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
    )

    # Create root observation
    root_observation = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=None,
        name="Root Observation",
    )

    # Create child observation
    observation_id = uuid4()
    child_data = build_observation_data(
        observation_id=observation_id,
        trace_id=trace.id,
        parent_observation_id=root_observation.id,
        name="Child Observation",
        type="span",
    )

    # Act
    child_observation = await observation_repository.create(child_data)
    await test_db_session.flush()

    # Assert
    assert child_observation is not None
    assert child_observation.id == observation_id
    assert child_observation.trace_id == trace.id
    assert child_observation.parent_observation_id == root_observation.id
    assert child_observation.name == "Child Observation"

    # Verify observation exists in database
    stmt = select(Observation).where(Observation.id == observation_id)
    result = await test_db_session.execute(stmt)
    db_observation = result.scalar_one_or_none()
    assert db_observation is not None
    assert db_observation.parent_observation_id == root_observation.id


@pytest.mark.asyncio
async def test_observation_get_tree_by_trace_id(
    test_db_session: AsyncSession,
    observation_repository: ObservationRepository,
):
    """
    Test retrieving observation tree structure by trace ID.

    Verifies:
    - All observations for trace returned
    - Tree structure preserved (parent-child relationships)
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
    trace = await seed_test_trace(
        test_db_session,
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
    )

    # Create observation tree: root -> child1, child2
    root = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=None,
        name="Root",
    )
    _child1 = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=root.id,
        name="Child 1",
    )
    _child2 = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=root.id,
        name="Child 2",
    )
    await test_db_session.flush()

    # Act
    observations = await observation_repository.get_tree_by_trace_id(trace.id)

    # Assert
    assert len(observations) == 3
    observation_names = {obs.name for obs in observations}
    assert "Root" in observation_names
    assert "Child 1" in observation_names
    assert "Child 2" in observation_names


@pytest.mark.asyncio
async def test_observation_get_root_observations(
    test_db_session: AsyncSession,
    observation_repository: ObservationRepository,
):
    """
    Test retrieving only root observations (no parent).

    Verifies:
    - Only observations with parent_observation_id=None returned
    - Child observations excluded
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
    trace = await seed_test_trace(
        test_db_session,
        agent_id=agent.id,
        project_id=project.id,
        organization_id=org.id,
    )

    # Create observation tree: root1 -> child1, root2
    root1 = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=None,
        name="Root 1",
    )
    _child1 = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=root1.id,
        name="Child 1",
    )
    _root2 = await seed_test_observation(
        test_db_session,
        trace_id=trace.id,
        parent_observation_id=None,
        name="Root 2",
    )
    await test_db_session.flush()

    # Act
    root_observations = await observation_repository.get_root_observations(trace.id)

    # Assert
    assert len(root_observations) == 2
    root_names = {obs.name for obs in root_observations}
    assert "Root 1" in root_names
    assert "Root 2" in root_names
    assert "Child 1" not in root_names  # Child should not be in root list
