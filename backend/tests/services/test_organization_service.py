"""
OrganizationService unit tests.

Tests organization management service methods with mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException

from tests.services.utils import OrganizationDataFactory, build_mock_organization_model


@pytest.mark.asyncio
async def test_get_organization_success(organization_service, mock_organization_repository):
    """Test successful organization retrieval."""
    # Arrange
    org_id = uuid4()
    org_data = OrganizationDataFactory.build(org_id=org_id, name="Test Org")
    mock_org = build_mock_organization_model(org_data)

    mock_organization_repository.get_by_id_with_relations.return_value = mock_org
    mock_organization_repository.is_active.return_value = True
    mock_organization_repository.is_suspended.return_value = False
    mock_organization_repository.is_archived.return_value = False

    # Act
    result = await organization_service.get_organization(org_id)

    # Assert
    assert result["id"] == str(org_id)
    assert result["name"] == "Test Org"
    assert result["is_active"] is True


@pytest.mark.asyncio
async def test_create_organization_success(organization_service, mock_organization_repository, mock_db_session):
    """Test successful organization creation."""
    # Arrange
    org_id = uuid4()
    org_data = {"name": "New Org"}
    created_org_data = OrganizationDataFactory.build(org_id=org_id, name="New Org")
    mock_org = build_mock_organization_model(created_org_data)

    mock_organization_repository.create.return_value = mock_org
    mock_organization_repository.activate.return_value = AsyncMock()
    mock_organization_repository.get_by_id_with_relations.return_value = mock_org
    mock_organization_repository.is_active.return_value = True
    mock_organization_repository.is_suspended.return_value = False
    mock_organization_repository.is_archived.return_value = False

    # Act
    result = await organization_service.create_organization(org_data, uuid4())

    # Assert
    assert result["name"] == "New Org"
    mock_organization_repository.create.assert_called_once()
    mock_organization_repository.activate.assert_called_once()
    mock_db_session.commit.assert_called_once()