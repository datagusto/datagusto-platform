"""
PermissionService unit tests.

Tests permission checking logic with mocked repositories.
"""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_is_owner_returns_true_for_owner(
    permission_service, mock_organization_owner_repository
):
    """Test is_owner check returns True for organization owner."""
    # Arrange
    org_id = uuid4()
    user_id = uuid4()
    mock_organization_owner_repository.is_owner.return_value = True

    # Act
    result = await permission_service.is_owner(org_id, user_id)

    # Assert
    assert result is True
    mock_organization_owner_repository.is_owner.assert_called_once_with(org_id, user_id)


@pytest.mark.asyncio
async def test_is_admin_or_owner_returns_true_for_admin(
    permission_service,
    mock_organization_admin_repository,
    mock_organization_owner_repository,
):
    """Test is_admin_or_owner returns True for admin."""
    # Arrange
    org_id = uuid4()
    user_id = uuid4()
    mock_organization_owner_repository.is_owner.return_value = False
    mock_organization_admin_repository.is_admin.return_value = True

    # Act
    result = await permission_service.is_admin_or_owner(org_id, user_id)

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_is_member_or_above_returns_false_for_non_member(
    permission_service,
    mock_organization_member_repository,
    mock_organization_owner_repository,
    mock_organization_admin_repository,
):
    """Test is_member_or_above returns False for non-member."""
    # Arrange
    org_id = uuid4()
    user_id = uuid4()
    mock_organization_owner_repository.is_owner.return_value = False
    mock_organization_admin_repository.is_admin.return_value = False
    mock_organization_member_repository.is_member.return_value = False

    # Act
    result = await permission_service.is_member_or_above(org_id, user_id)

    # Assert
    assert result is False
