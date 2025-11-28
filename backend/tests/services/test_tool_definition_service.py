"""
Tool Definition service unit tests.

Tests verify service layer business logic for tool registration
using mocked repositories.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.tool_definition import ToolRegistrationRequest
from app.services.tool_definition_service import ToolDefinitionService


@pytest.mark.asyncio
async def test_register_tools_first_registration():
    """
    Test registering tools for the first time.

    Verifies:
    - ToolDefinition created
    - First revision created with previous_revision_id=None
    - Response contains correct data
    """
    # Arrange
    agent_id = uuid4()
    user_id = uuid4()
    tool_def_id = uuid4()
    revision_id = uuid4()

    # Mock database session
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    # Mock repositories
    service = ToolDefinitionService(mock_db)

    # Mock tool definition (first time, no existing definition)
    mock_tool_def = MagicMock()
    mock_tool_def.id = tool_def_id
    mock_tool_def.latest_revision_id = None  # No previous revisions

    service.tool_def_repo.get_or_create_by_agent = AsyncMock(return_value=mock_tool_def)

    # Mock revision creation
    mock_revision = MagicMock()
    mock_revision.id = revision_id
    mock_revision.created_at = MagicMock()
    mock_revision.created_at.isoformat = MagicMock(return_value="2025-11-18T16:00:00Z")

    service.revision_repo.create_revision = AsyncMock(return_value=mock_revision)
    service.tool_def_repo.update_latest_revision_id = AsyncMock(return_value=mock_tool_def)

    request = ToolRegistrationRequest(
        tools=[
            {
                "name": "get_weather",
                "description": "Get weather info",
                "input_schema": {},
                "output_schema": {},
            }
        ]
    )

    # Act
    response = await service.register_tools(
        agent_id=agent_id, created_by=user_id, request=request
    )

    # Assert
    assert response.agent_id == str(agent_id)
    assert response.tool_definition_id == str(tool_def_id)
    assert response.revision_id == str(revision_id)
    assert response.tools_count == 1
    assert response.previous_revision_id is None  # First registration

    # Verify repository calls
    service.tool_def_repo.get_or_create_by_agent.assert_called_once_with(
        agent_id=agent_id, created_by=user_id
    )
    service.revision_repo.create_revision.assert_called_once()
    service.tool_def_repo.update_latest_revision_id.assert_called_once_with(
        tool_definition_id=tool_def_id, revision_id=revision_id
    )
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_register_tools_second_registration():
    """
    Test registering tools when previous revision exists.

    Verifies:
    - New revision links to previous via previous_revision_id
    - Response shows previous revision ID
    """
    # Arrange
    agent_id = uuid4()
    user_id = uuid4()
    tool_def_id = uuid4()
    previous_revision_id = uuid4()
    new_revision_id = uuid4()

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    service = ToolDefinitionService(mock_db)

    # Mock tool definition with existing revision
    mock_tool_def = MagicMock()
    mock_tool_def.id = tool_def_id
    mock_tool_def.latest_revision_id = previous_revision_id  # Has previous revision

    service.tool_def_repo.get_or_create_by_agent = AsyncMock(return_value=mock_tool_def)

    # Mock new revision creation
    mock_revision = MagicMock()
    mock_revision.id = new_revision_id
    mock_revision.created_at = MagicMock()
    mock_revision.created_at.isoformat = MagicMock(return_value="2025-11-18T16:00:00Z")

    service.revision_repo.create_revision = AsyncMock(return_value=mock_revision)
    service.tool_def_repo.update_latest_revision_id = AsyncMock(return_value=mock_tool_def)

    request = ToolRegistrationRequest(
        tools=[
            {"name": "get_weather"},
            {"name": "search"},
        ]
    )

    # Act
    response = await service.register_tools(
        agent_id=agent_id, created_by=user_id, request=request
    )

    # Assert
    assert response.tools_count == 2
    assert response.previous_revision_id == str(previous_revision_id)
    assert response.revision_id == str(new_revision_id)

    # Verify revision created with correct previous_revision_id
    call_kwargs = service.revision_repo.create_revision.call_args.kwargs
    assert call_kwargs["previous_revision_id"] == previous_revision_id
    assert call_kwargs["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_register_tools_rollback_on_error():
    """
    Test that transaction rolls back on error.

    Verifies:
    - Exception is raised
    - Database rollback is called
    """
    # Arrange
    agent_id = uuid4()
    user_id = uuid4()

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
    mock_db.rollback = AsyncMock()

    service = ToolDefinitionService(mock_db)

    mock_tool_def = MagicMock()
    mock_tool_def.id = uuid4()
    mock_tool_def.latest_revision_id = None

    service.tool_def_repo.get_or_create_by_agent = AsyncMock(return_value=mock_tool_def)

    mock_revision = MagicMock()
    mock_revision.id = uuid4()
    mock_revision.created_at = MagicMock()
    mock_revision.created_at.isoformat = MagicMock(return_value="2025-11-18T16:00:00Z")

    service.revision_repo.create_revision = AsyncMock(return_value=mock_revision)
    service.tool_def_repo.update_latest_revision_id = AsyncMock(return_value=mock_tool_def)

    request = ToolRegistrationRequest(tools=[{"name": "test"}])

    # Act & Assert
    with pytest.raises(Exception):
        await service.register_tools(
            agent_id=agent_id, created_by=user_id, request=request
        )

    # Verify rollback was called
    mock_db.rollback.assert_called_once()
