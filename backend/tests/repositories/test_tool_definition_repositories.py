"""
Tool Definition repositories integration tests.

Tests verify database operations for ToolDefinition and ToolDefinitionRevision
models using PostgreSQL test database with transaction rollback for isolation.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_definition import ToolDefinition, ToolDefinitionRevision
from app.repositories.tool_definition_repository import (
    ToolDefinitionRepository,
    ToolDefinitionRevisionRepository,
)
from tests.repositories.conftest import seed_test_agent, seed_test_organization, seed_test_project, seed_test_user


# ============================================================================
# ToolDefinitionRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_tool_definition_create_success(
    test_db_session: AsyncSession,
):
    """
    Test creating a tool definition.

    Verifies:
    - ToolDefinition created successfully
    - agent_id and created_by set correctly
    - latest_revision_id is initially None
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

    repo = ToolDefinitionRepository(test_db_session)

    # Act
    tool_def = await repo.get_or_create_by_agent(
        agent_id=agent.id, created_by=user.id
    )
    await test_db_session.flush()

    # Assert
    assert tool_def is not None
    assert tool_def.agent_id == agent.id
    assert tool_def.created_by == user.id
    assert tool_def.latest_revision_id is None
    assert tool_def.created_at is not None


@pytest.mark.asyncio
async def test_tool_definition_get_by_agent_id(
    test_db_session: AsyncSession,
):
    """
    Test retrieving tool definition by agent ID.

    Verifies:
    - ToolDefinition returned when exists
    - Returns None when doesn't exist
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

    repo = ToolDefinitionRepository(test_db_session)
    await repo.get_or_create_by_agent(agent_id=agent.id, created_by=user.id)
    await test_db_session.flush()

    # Act
    tool_def = await repo.get_by_agent_id(agent.id)

    # Assert
    assert tool_def is not None
    assert tool_def.agent_id == agent.id

    # Test non-existent agent
    non_existent_id = uuid4()
    result = await repo.get_by_agent_id(non_existent_id)
    assert result is None


# ============================================================================
# ToolDefinitionRevisionRepository Tests
# ============================================================================


@pytest.mark.asyncio
async def test_revision_create_with_jsonb_tools_data(
    test_db_session: AsyncSession,
):
    """
    Test creating a revision with JSONB tools data.

    Verifies:
    - Revision created successfully
    - JSONB tools_data field stored correctly
    - previous_revision_id is None for first revision
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

    tools_data = {
        "tools": [
            {
                "name": "get_weather",
                "description": "Get weather information",
                "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}},
                "output_schema": {"type": "object"},
            }
        ]
    }

    repo = ToolDefinitionRevisionRepository(test_db_session)

    # Act
    revision = await repo.create_revision(
        agent_id=agent.id,
        tools_data=tools_data,
        previous_revision_id=None,
        created_by=user.id,
    )
    await test_db_session.flush()

    # Assert
    assert revision is not None
    assert revision.agent_id == agent.id
    assert revision.tools_data == tools_data
    assert revision.tools_data["tools"][0]["name"] == "get_weather"
    assert revision.previous_revision_id is None
    assert revision.created_at is not None

    # Verify revision exists in database with JSONB
    stmt = select(ToolDefinitionRevision).where(
        ToolDefinitionRevision.id == revision.id
    )
    result = await test_db_session.execute(stmt)
    db_revision = result.scalar_one_or_none()
    assert db_revision is not None
    assert db_revision.tools_data["tools"][0]["name"] == "get_weather"


@pytest.mark.asyncio
async def test_revision_linked_list_structure(
    test_db_session: AsyncSession,
):
    """
    Test revision linked list structure.

    Verifies:
    - Second revision links to first via previous_revision_id
    - Linked list structure maintained correctly
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

    repo = ToolDefinitionRevisionRepository(test_db_session)

    # Act - Create first revision
    revision1 = await repo.create_revision(
        agent_id=agent.id,
        tools_data={"tools": [{"name": "tool1"}]},
        previous_revision_id=None,
        created_by=user.id,
    )
    await test_db_session.flush()

    # Act - Create second revision
    revision2 = await repo.create_revision(
        agent_id=agent.id,
        tools_data={"tools": [{"name": "tool1"}, {"name": "tool2"}]},
        previous_revision_id=revision1.id,
        created_by=user.id,
    )
    await test_db_session.flush()

    # Assert
    assert revision1.previous_revision_id is None
    assert revision2.previous_revision_id == revision1.id

    # Verify linked list
    revisions = await repo.get_by_agent_id(agent.id, limit=10)
    assert len(revisions) == 2
    # Check both revisions are present (order may vary if created_at is identical)
    revision_ids = {r.id for r in revisions}
    assert revision1.id in revision_ids
    assert revision2.id in revision_ids


@pytest.mark.asyncio
async def test_update_latest_revision_id(
    test_db_session: AsyncSession,
):
    """
    Test updating latest_revision_id in ToolDefinition.

    Verifies:
    - latest_revision_id updated successfully
    - Points to correct revision
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

    tool_def_repo = ToolDefinitionRepository(test_db_session)
    revision_repo = ToolDefinitionRevisionRepository(test_db_session)

    # Create tool definition and revision
    tool_def = await tool_def_repo.get_or_create_by_agent(
        agent_id=agent.id, created_by=user.id
    )
    revision = await revision_repo.create_revision(
        agent_id=agent.id,
        tools_data={"tools": []},
        previous_revision_id=None,
        created_by=user.id,
    )
    await test_db_session.flush()

    # Act
    updated_tool_def = await tool_def_repo.update_latest_revision_id(
        tool_definition_id=tool_def.id, revision_id=revision.id
    )
    await test_db_session.flush()

    # Assert
    assert updated_tool_def is not None
    assert updated_tool_def.latest_revision_id == revision.id

    # Verify in database
    stmt = select(ToolDefinition).where(ToolDefinition.id == tool_def.id)
    result = await test_db_session.execute(stmt)
    db_tool_def = result.scalar_one_or_none()
    assert db_tool_def.latest_revision_id == revision.id
