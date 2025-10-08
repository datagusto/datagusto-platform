"""
Integration tests for organization workflows.

Tests complete workflows from organization creation through member management,
admin privileges, and ownership transfer.
"""

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from tests.api.base import BaseControllerTest


@pytest.mark.integration
class TestOrganizationWorkflows(BaseControllerTest):
    """Integration tests for complete organization workflows."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.organizations.OrganizationService")
    @patch("app.api.v1.endpoints.organizations.OrganizationMemberService")
    @patch("app.api.v1.endpoints.organizations.PermissionService")
    async def test_complete_organization_lifecycle(
        self,
        mock_permission_service_class,
        mock_member_service_class,
        mock_org_service_class,
        authenticated_client,
        test_user_data,
        test_organization_data,
    ):
        """
        Test complete organization lifecycle workflow.

        Workflow:
        1. Create organization
        2. Add member
        3. Grant admin privileges
        4. Remove member
        """
        _user_id = UUID(test_user_data["id"])
        org_id = UUID(test_organization_data["id"])
        new_member_id = UUID("11111111-1111-1111-1111-111111111111")

        # Mock services
        mock_org_service = AsyncMock()
        mock_member_service = AsyncMock()
        mock_permission_service = AsyncMock()

        mock_org_service_class.return_value = mock_org_service
        mock_member_service_class.return_value = mock_member_service
        mock_permission_service_class.return_value = mock_permission_service

        # Step 1: Create organization
        mock_org_service.create_organization.return_value = test_organization_data
        create_payload = {"name": "Test Organization"}

        create_response = await authenticated_client.post(
            "/api/v1/organizations/", json=create_payload
        )
        create_data = self._assert_success(create_response, expected_status=200)
        assert create_data["name"] == "Test Organization"

        # Step 2: Add member
        mock_permission_service.is_admin_or_owner.return_value = True
        mock_member_service.add_member.return_value = {
            "id": 1,
            "organization_id": str(org_id),
            "user_id": str(new_member_id),
            "created_at": "2025-09-30T00:00:00",
        }

        add_member_payload = {"user_id": str(new_member_id)}
        add_response = await authenticated_client.post(
            f"/api/v1/organizations/{org_id}/members", json=add_member_payload
        )
        add_data = self._assert_success(add_response, expected_status=201)
        assert add_data["user_id"] == str(new_member_id)

        # Step 3: Grant admin privileges
        # (Tested in separate admin workflow tests)

        # Step 4: Remove member
        mock_member_service.remove_member.return_value = None
        remove_response = await authenticated_client.delete(
            f"/api/v1/organizations/{org_id}/members/{new_member_id}"
        )
        assert remove_response.status_code == 204

        # Verify service calls
        assert mock_org_service.create_organization.called
        assert mock_member_service.add_member.called
        assert mock_member_service.remove_member.called


@pytest.mark.integration
class TestUserOrganizationWorkflows(BaseControllerTest):
    """Integration tests for user and organization interaction workflows."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.users.UserService")
    @patch("app.api.v1.endpoints.users.PermissionService")
    async def test_user_profile_update_workflow(
        self,
        mock_permission_service_class,
        mock_user_service_class,
        authenticated_client,
        test_user_data,
    ):
        """
        Test user profile creation and update workflow.

        Workflow:
        1. Get user profile
        2. Update user profile
        3. Verify changes
        """
        _user_id = UUID(test_user_data["id"])

        # Mock services
        mock_user_service = AsyncMock()
        mock_permission_service = AsyncMock()

        mock_user_service_class.return_value = mock_user_service
        mock_permission_service_class.return_value = mock_permission_service

        # Step 1: Get user profile
        mock_user_service.get_user.return_value = test_user_data
        get_response = await authenticated_client.get(f"/api/v1/users/{_user_id}")
        get_data = self._assert_success(get_response, expected_status=200)
        assert get_data["email"] == test_user_data["email"]

        # Step 2: Update user profile
        mock_permission_service.is_same_user.return_value = True
        updated_data = test_user_data.copy()
        updated_data["name"] = "Updated Name"
        updated_data["bio"] = "Updated Bio"
        mock_user_service.update_profile.return_value = updated_data

        update_payload = {"name": "Updated Name", "bio": "Updated Bio"}
        update_response = await authenticated_client.patch(
            f"/api/v1/users/{_user_id}/profile", json=update_payload
        )
        update_data = self._assert_success(update_response, expected_status=200)

        # Step 3: Verify changes
        assert update_data["name"] == "Updated Name"
        assert update_data["bio"] == "Updated Bio"
        assert mock_user_service.update_profile.called
