"""
Organization management endpoint tests.

Tests for organization CRUD operations, member management, and permissions.
"""

from unittest.mock import AsyncMock, patch

import pytest

from tests.api.base import BaseControllerTest


class TestOrganizationEndpoints(BaseControllerTest):
    """Test cases for organization management endpoints."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationService")
    async def test_get_organization_success(
        self,
        mock_org_service_class,
        authenticated_client,
        test_organization_data,
        test_organization_id,
    ):
        """Test successful organization retrieval."""
        # Mock OrganizationService
        mock_service = AsyncMock()
        mock_service.get_organization.return_value = test_organization_data
        mock_org_service_class.return_value = mock_service

        # Make request
        response = await authenticated_client.get(
            f"/api/v1/organizations/{test_organization_id}"
        )

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert data["id"] == test_organization_data["id"]
        assert data["name"] == test_organization_data["name"]
        assert data["is_active"] == test_organization_data["is_active"]
        assert mock_service.get_organization.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationService")
    async def test_create_organization_success(
        self,
        mock_org_service_class,
        authenticated_client,
        test_organization_data,
    ):
        """Test successful organization creation."""
        # Mock OrganizationService
        mock_service = AsyncMock()
        mock_service.create_organization.return_value = test_organization_data
        mock_org_service_class.return_value = mock_service

        # Make request
        payload = {
            "name": test_organization_data["name"],
        }
        response = await authenticated_client.post(
            "/api/v1/organizations/", json=payload
        )

        # Assertions
        data = self._assert_success(response, expected_status=200)
        assert data["name"] == test_organization_data["name"]
        assert mock_service.create_organization.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_update_organization_permission_denied(
        self,
        mock_permission_service_class,
        authenticated_client,
        test_organization_id,
    ):
        """Test organization update without admin/owner permission."""
        # Mock PermissionService to deny permission
        mock_service = AsyncMock()
        mock_service.is_admin_or_owner.return_value = False
        mock_permission_service_class.return_value = mock_service

        # Make request
        payload = {
            "name": "Hacked Organization",
        }
        response = await authenticated_client.patch(
            f"/api/v1/organizations/{test_organization_id}", json=payload
        )

        # Assertions
        self._assert_error(
            response,
            expected_status=403,
            expected_detail="admin",
        )

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationMemberService")
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_add_member_success(
        self,
        mock_permission_service_class,
        mock_member_service_class,
        authenticated_client,
        test_organization_id,
        test_user_id,
    ):
        """Test successful member addition to organization."""
        # Mock PermissionService to grant permission
        mock_permission = AsyncMock()
        mock_permission.is_admin_or_owner.return_value = True
        mock_permission_service_class.return_value = mock_permission

        # Mock OrganizationMemberService
        mock_service = AsyncMock()
        mock_service.add_member.return_value = {
            "organization_id": str(test_organization_id),
            "user_id": str(test_user_id),
            "added_by": str(test_user_id),
            "joined_at": "2024-01-01T00:00:00",
        }
        mock_member_service_class.return_value = mock_service

        # Make request
        payload = {
            "user_id": str(test_user_id),
        }
        response = await authenticated_client.post(
            f"/api/v1/organizations/{test_organization_id}/members", json=payload
        )

        # Assertions
        self._assert_success(response, expected_status=201)
        assert mock_service.add_member.called

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_remove_member_permission_denied(
        self,
        mock_permission_service_class,
        authenticated_client,
        test_organization_id,
        test_user_id,
    ):
        """Test member removal without admin/owner permission."""
        # Mock PermissionService to deny permission
        mock_service = AsyncMock()
        mock_service.is_admin_or_owner.return_value = False
        mock_permission_service_class.return_value = mock_service

        # Make request
        response = await authenticated_client.delete(
            f"/api/v1/organizations/{test_organization_id}/members/{test_user_id}"
        )

        # Assertions
        self._assert_error(
            response,
            expected_status=403,
            expected_detail="admin",
        )
