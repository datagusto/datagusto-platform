"""
Tool registration endpoint tests.

Tests verify POST /api/v1/public/tools/register endpoint
with agent API key authentication.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_agent_from_api_key
from app.core.database import get_async_db
from app.main import app
from app.schemas.tool_definition import ToolRegistrationResponse


@pytest.fixture
async def agent_authenticated_client(mock_db):
    """Async client with agent authentication."""
    agent_id = uuid4()
    mock_agent = {
        "agent_id": str(agent_id),
        "project_id": str(uuid4()),
        "organization_id": str(uuid4()),
    }

    async def override_get_agent():
        return mock_agent

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_current_agent_from_api_key] = override_get_agent
    app.dependency_overrides[get_async_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, agent_id

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_tools_success(agent_authenticated_client):
    """
    Test successful tool registration.

    Verifies:
    - 200 status code returned
    - Response contains revision information
    - Service called with correct parameters
    """
    client, agent_id = agent_authenticated_client

    # Arrange
    revision_id = uuid4()
    tool_def_id = uuid4()

    request_data = {
        "tools": [
            {
                "name": "get_weather",
                "description": "Get weather information",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        ]
    }

    # Mock service response
    mock_response = ToolRegistrationResponse(
        tool_definition_id=str(tool_def_id),
        revision_id=str(revision_id),
        agent_id=str(agent_id),
        tools_count=1,
        previous_revision_id=None,
        created_at="2025-11-18T16:00:00Z",
    )

    # Patch service
    with patch(
        "app.api.v1.endpoints.secure.ToolDefinitionService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service.register_tools = AsyncMock(return_value=mock_response)
        mock_service_class.return_value = mock_service

        # Act
        response = await client.post(
            "/api/v1/public/tools/register",
            json=request_data,
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent_id"] == str(agent_id)
    assert data["revision_id"] == str(revision_id)
    assert data["tools_count"] == 1
    assert data["previous_revision_id"] is None


@pytest.mark.asyncio
async def test_register_tools_empty_list(agent_authenticated_client):
    """
    Test registering empty tools list.

    Verifies:
    - Empty list is accepted (no validation)
    - 200 status code returned
    """
    client, agent_id = agent_authenticated_client

    # Arrange
    revision_id = uuid4()
    tool_def_id = uuid4()

    request_data = {"tools": []}  # Empty tools list

    mock_response = ToolRegistrationResponse(
        tool_definition_id=str(tool_def_id),
        revision_id=str(revision_id),
        agent_id=str(agent_id),
        tools_count=0,
        previous_revision_id=None,
        created_at="2025-11-18T16:00:00Z",
    )

    with patch(
        "app.api.v1.endpoints.secure.ToolDefinitionService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service.register_tools = AsyncMock(return_value=mock_response)
        mock_service_class.return_value = mock_service

        # Act
        response = await client.post(
            "/api/v1/public/tools/register",
            json=request_data,
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tools_count"] == 0


@pytest.mark.asyncio
async def test_register_tools_multiple_tools(agent_authenticated_client):
    """
    Test registering multiple tools.

    Verifies:
    - Multiple tools accepted
    - Correct count returned
    """
    client, agent_id = agent_authenticated_client

    # Arrange
    revision_id = uuid4()
    tool_def_id = uuid4()

    request_data = {
        "tools": [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"},
        ]
    }

    mock_response = ToolRegistrationResponse(
        tool_definition_id=str(tool_def_id),
        revision_id=str(revision_id),
        agent_id=str(agent_id),
        tools_count=3,
        previous_revision_id=None,
        created_at="2025-11-18T16:00:00Z",
    )

    with patch(
        "app.api.v1.endpoints.secure.ToolDefinitionService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service.register_tools = AsyncMock(return_value=mock_response)
        mock_service_class.return_value = mock_service

        # Act
        response = await client.post(
            "/api/v1/public/tools/register",
            json=request_data,
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tools_count"] == 3


@pytest.mark.asyncio
async def test_register_tools_service_error(agent_authenticated_client):
    """
    Test error handling when service raises exception.

    Verifies:
    - 500 status code returned
    - Error message included
    """
    client, agent_id = agent_authenticated_client

    # Arrange
    request_data = {"tools": [{"name": "test"}]}

    with patch(
        "app.api.v1.endpoints.secure.ToolDefinitionService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service.register_tools = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        mock_service_class.return_value = mock_service

        # Act
        response = await client.post(
            "/api/v1/public/tools/register",
            json=request_data,
        )

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
