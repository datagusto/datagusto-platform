"""
Guardrail repositories integration tests.

Tests verify database operations for Guardrail and GuardrailAgentAssignment
models using PostgreSQL test database with transaction rollback for isolation.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail import (
    Guardrail,
    GuardrailActiveStatus,
    GuardrailAgentAssignment,
)
from app.repositories.guardrail_assignment_repository import (
    GuardrailAssignmentRepository,
)
from app.repositories.guardrail_repository import GuardrailRepository
from tests.repositories.conftest import (
    build_guardrail_assignment_data,
    build_guardrail_data,
    seed_test_agent,
    seed_test_guardrail,
    seed_test_organization,
    seed_test_project,
    seed_test_user,
)

# ============================================================================
# GuardrailRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_guardrail_create_with_jsonb_definition(
    test_db_session: AsyncSession,
    guardrail_repository: GuardrailRepository,
):
    """
    Test creating a guardrail with JSONB definition.

    Verifies:
    - Guardrail created successfully
    - JSONB definition field stored correctly
    - created_at and updated_at timestamps set
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    guardrail_id = uuid4()

    definition = {
        "type": "content_filter",
        "rules": [
            {"field": "content", "operator": "contains", "value": "forbidden"},
            {"field": "sentiment", "operator": "less_than", "value": 0.3},
        ],
    }

    guardrail_data = build_guardrail_data(
        guardrail_id=guardrail_id,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
        name="Content Filter",
        definition=definition,
    )

    # Act
    guardrail = await guardrail_repository.create(guardrail_data)
    await test_db_session.flush()

    # Assert
    assert guardrail is not None
    assert guardrail.id == guardrail_id
    assert guardrail.project_id == project.id
    assert guardrail.name == "Content Filter"
    assert guardrail.definition == definition
    assert guardrail.created_at is not None
    assert guardrail.updated_at is not None

    # Verify guardrail exists in database with JSONB
    stmt = select(Guardrail).where(Guardrail.id == guardrail_id)
    result = await test_db_session.execute(stmt)
    db_guardrail = result.scalar_one_or_none()
    assert db_guardrail is not None
    assert db_guardrail.definition["type"] == "content_filter"
    assert len(db_guardrail.definition["rules"]) == 2


@pytest.mark.asyncio
async def test_guardrail_get_by_id_success(
    test_db_session: AsyncSession,
    guardrail_repository: GuardrailRepository,
):
    """
    Test retrieving guardrail by ID.

    Verifies:
    - Guardrail returned when exists
    - JSONB definition accessible
    """
    # Arrange
    org = await seed_test_organization(test_db_session)
    user = await seed_test_user(test_db_session)
    project = await seed_test_project(
        test_db_session, organization_id=org.id, created_by=user.id
    )
    guardrail = await seed_test_guardrail(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
        name="Test Guardrail",
    )
    await test_db_session.flush()

    # Act
    retrieved_guardrail = await guardrail_repository.get_by_id(guardrail.id)

    # Assert
    assert retrieved_guardrail is not None
    assert retrieved_guardrail.id == guardrail.id
    assert retrieved_guardrail.name == "Test Guardrail"
    assert retrieved_guardrail.definition is not None


# ============================================================================
# GuardrailAssignmentRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_guardrail_assignment_assign_success(
    test_db_session: AsyncSession,
    guardrail_assignment_repository: GuardrailAssignmentRepository,
):
    """
    Test assigning guardrail to agent.

    Verifies:
    - GuardrailAgentAssignment record created
    - Assignment relationship established
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
    guardrail = await seed_test_guardrail(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )
    await test_db_session.flush()

    # Act
    assignment = await guardrail_assignment_repository.assign(
        guardrail_id=guardrail.id,
        agent_id=agent.id,
        project_id=project.id,
        assigned_by=user.id,
    )
    await test_db_session.flush()

    # Assert
    assert assignment is not None
    assert assignment.guardrail_id == guardrail.id
    assert assignment.agent_id == agent.id

    # Verify assignment exists in database
    stmt = select(GuardrailAgentAssignment).where(
        GuardrailAgentAssignment.guardrail_id == guardrail.id,
        GuardrailAgentAssignment.agent_id == agent.id,
    )
    result = await test_db_session.execute(stmt)
    db_assignment = result.scalar_one_or_none()
    assert db_assignment is not None


@pytest.mark.asyncio
async def test_guardrail_assignment_is_assigned(
    test_db_session: AsyncSession,
    guardrail_assignment_repository: GuardrailAssignmentRepository,
):
    """
    Test checking if guardrail is assigned to agent.

    Verifies:
    - Returns True when assignment exists
    - Returns False when not assigned
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
    guardrail = await seed_test_guardrail(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )
    unassigned_guardrail = await seed_test_guardrail(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )

    # Assign guardrail to agent
    assignment_data = build_guardrail_assignment_data(
        guardrail_id=guardrail.id,
        agent_id=agent.id,
        project_id=project.id,
        assigned_by=user.id,
    )
    assignment_record = GuardrailAgentAssignment(**assignment_data)
    test_db_session.add(assignment_record)
    await test_db_session.flush()

    # Act
    is_assigned = await guardrail_assignment_repository.is_assigned(
        guardrail_id=guardrail.id, agent_id=agent.id
    )
    is_not_assigned = await guardrail_assignment_repository.is_assigned(
        guardrail_id=unassigned_guardrail.id, agent_id=agent.id
    )

    # Assert
    assert is_assigned is True
    assert is_not_assigned is False


@pytest.mark.asyncio
async def test_guardrail_assignment_duplicate_fails(
    test_db_session: AsyncSession,
    guardrail_assignment_repository: GuardrailAssignmentRepository,
):
    """
    Test assigning same guardrail twice raises IntegrityError.

    Verifies:
    - Cannot assign same guardrail to agent twice
    - Database constraint enforced
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
    guardrail = await seed_test_guardrail(
        test_db_session,
        project_id=project.id,
        organization_id=org.id,
        created_by=user.id,
    )

    # Assign guardrail first time
    await guardrail_assignment_repository.assign(
        guardrail_id=guardrail.id,
        agent_id=agent.id,
        project_id=project.id,
        assigned_by=user.id,
    )
    await test_db_session.flush()

    # Act & Assert - Assigning again should fail
    with pytest.raises(Exception):  # IntegrityError or similar
        await guardrail_assignment_repository.assign(
            guardrail_id=guardrail.id,
            agent_id=agent.id,
            project_id=project.id,
            assigned_by=user.id,
        )
        await test_db_session.flush()
