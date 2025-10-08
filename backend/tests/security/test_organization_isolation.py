"""
Security tests for organization data isolation.

Tests to ensure users cannot access data from organizations they don't belong to.
"""

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from tests.api.base import BaseControllerTest


@pytest.mark.security
class TestOrganizationIsolation(BaseControllerTest):
    """Security tests for multi-tenant organization isolation."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationService")
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_cannot_modify_other_organization_data(
        self,
        mock_permission_service_class,
        mock_org_service_class,
        authenticated_client,
    ):
        """
        Test that users cannot modify organization data they don't belong to.

        Security check: Organization modification isolation enforcement.
        """
        _own_org_id = UUID("12345678-1234-1234-1234-123456789abc")
        other_org_id = UUID("87654321-4321-4321-4321-cba987654321")

        # Mock services
        mock_permission_service = AsyncMock()
        mock_org_service = AsyncMock()

        mock_permission_service_class.return_value = mock_permission_service
        mock_org_service_class.return_value = mock_org_service

        # User tries to modify organization they don't belong to
        mock_permission_service.is_admin_or_owner.return_value = False

        update_payload = {"name": "Hacked Organization"}
        response = await authenticated_client.patch(
            f"/api/v1/organizations/{other_org_id}", json=update_payload
        )

        # Should return 403 Forbidden
        self._assert_error(response, expected_status=403)

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.users.UserService")
    @patch("app.api.v1.endpoints.users.PermissionService")
    async def test_cannot_modify_other_user_profile(
        self,
        mock_permission_service_class,
        mock_user_service_class,
        authenticated_client,
    ):
        """
        Test that users cannot modify profiles of other users.

        Security check: User data protection.
        """
        _own_user_id = UUID("12345678-1234-1234-1234-123456789abc")
        other_user_id = UUID("87654321-4321-4321-4321-cba987654321")

        # Mock services
        mock_permission_service = AsyncMock()
        mock_user_service = AsyncMock()

        mock_permission_service_class.return_value = mock_permission_service
        mock_user_service_class.return_value = mock_user_service

        # User tries to update another user's profile
        mock_permission_service.is_same_user.return_value = False

        update_payload = {"name": "Hacked Name"}
        response = await authenticated_client.patch(
            f"/api/v1/users/{other_user_id}/profile", json=update_payload
        )

        # Should return 403 Forbidden
        self._assert_error(response, expected_status=403)


@pytest.mark.security
class TestAuthorizationChecks(BaseControllerTest):
    """Security tests for authorization enforcement."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationMemberService")
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_non_admin_cannot_add_members(
        self,
        mock_permission_service_class,
        mock_member_service_class,
        authenticated_client,
        test_organization_data,
    ):
        """
        Test that non-admin users cannot add members to organization.

        Security check: Admin privilege enforcement.
        """
        org_id = UUID(test_organization_data["id"])
        new_member_id = UUID("11111111-1111-1111-1111-111111111111")

        # Mock services
        mock_permission_service = AsyncMock()
        mock_member_service = AsyncMock()

        mock_permission_service_class.return_value = mock_permission_service
        mock_member_service_class.return_value = mock_member_service

        # User is not an admin
        mock_permission_service.is_admin_or_owner.return_value = False

        add_payload = {"user_id": str(new_member_id)}
        response = await authenticated_client.post(
            f"/api/v1/organizations/{org_id}/members", json=add_payload
        )

        # Should return 403 Forbidden
        self._assert_error(response, expected_status=403)
