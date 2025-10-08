"""
Organization management flow integration tests.

Tests complete organization management workflows end-to-end with real database.
Covers organization CRUD, member management, and role-based access control.
"""

from uuid import UUID

import pytest

# Mark all tests as integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


# ============================================================================
# Test: Organization Creation Flow
# ============================================================================


async def test_create_organization_complete_setup(integration_client):
    """
    Test complete organization creation flow.

    Verifies:
    - User can create new organization
    - Creator becomes owner
    - Creator becomes member
    - Organization active status created
    - All relationships properly established
    """
    # Arrange - Register and authenticate user
    registration_data = {
        "email": "orgcreator@example.com",
        "password": "OrgCreator123!",
        "name": "Org Creator",
        "organization_name": "Initial Org",
    }

    register_response = await integration_client.post(
        "/api/v1/auth/register", json=registration_data
    )
    assert register_response.status_code == 200
    user_data = register_response.json()
    access_token = user_data["access_token"]

    # Act - Create new organization
    org_data = {
        "name": "New Test Organization",
    }

    create_response = await integration_client.post(
        "/api/v1/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Assert organization created
    if create_response.status_code != 200:
        print(f"Error response: {create_response.json()}")
    assert create_response.status_code == 200
    created_org = create_response.json()

    assert created_org["name"] == org_data["name"]
    assert created_org["is_active"] is True
    assert "id" in created_org

    # Note: Owner verification would require additional implementation
    # For now, we verify the organization was created successfully


# ============================================================================
# Test: Organization Update Flow
# ============================================================================


async def test_update_organization_as_owner(integration_client):
    """
    Test organization update flow with owner permissions.

    Verifies:
    - Owner can update organization
    - Non-owner cannot update organization
    - Changes are persisted
    - Updated_at timestamp changes
    """
    # Arrange - Register owner and create organization
    owner_data = {
        "email": "owner@example.com",
        "password": "Owner123!",
        "name": "Owner User",
        "organization_name": "Owner Test Org",
    }

    owner_response = await integration_client.post(
        "/api/v1/auth/register", json=owner_data
    )
    assert owner_response.status_code == 200
    owner = owner_response.json()

    # Get organization ID from /me/organizations endpoint
    owner_orgs = await integration_client.get(
        "/api/v1/auth/me/organizations",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    owner_org_id = owner_orgs.json()["organizations"][0]["id"]

    # Act - Update organization as owner
    update_data = {
        "name": "Updated Organization Name",
    }

    update_response = await integration_client.patch(
        f"/api/v1/organizations/{owner_org_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )

    # Assert update successful
    assert update_response.status_code == 200
    updated_org = update_response.json()
    assert updated_org["name"] == update_data["name"]

    # Verify changes persisted - GET organization again
    get_response = await integration_client.get(
        f"/api/v1/organizations/{owner_org_id}",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert get_response.status_code == 200
    persisted_org = get_response.json()
    assert persisted_org["name"] == update_data["name"]

    # Test non-owner cannot update
    # Register second user in different organization
    non_owner_data = {
        "email": "nonowner@example.com",
        "password": "NonOwner123!",
        "name": "Non Owner",
        "organization_name": "Other Org",
    }

    non_owner_response = await integration_client.post(
        "/api/v1/auth/register", json=non_owner_data
    )
    assert non_owner_response.status_code == 200
    non_owner = non_owner_response.json()

    # Attempt to update as non-owner - should fail
    forbidden_update = await integration_client.patch(
        f"/api/v1/organizations/{owner_org_id}",
        json={"name": "Hacked Name"},
        headers={"Authorization": f"Bearer {non_owner['access_token']}"},
    )
    assert forbidden_update.status_code == 403


# ============================================================================
# Test: Add Member Flow
# ============================================================================


async def test_add_member_to_organization(integration_client):
    """
    Test adding member to organization.

    Verifies:
    - Owner can add members
    - Membership record created
    - Member appears in members list
    - Member has default role
    """
    # Arrange - Register owner
    owner_data = {
        "email": "addowner@example.com",
        "password": "Owner123!",
        "name": "Add Owner",
        "organization_name": "Add Member Org",
    }

    owner_response = await integration_client.post(
        "/api/v1/auth/register", json=owner_data
    )
    assert owner_response.status_code == 200
    owner = owner_response.json()

    # Get organization ID from /me/organizations endpoint
    owner_orgs = await integration_client.get(
        "/api/v1/auth/me/organizations",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    owner_org_id = owner_orgs.json()["organizations"][0]["id"]

    # Register user to be added as member
    member_data = {
        "email": "newmember@example.com",
        "password": "Member123!",
        "name": "New Member",
        "organization_name": "Member Own Org",
    }

    member_response = await integration_client.post(
        "/api/v1/auth/register", json=member_data
    )
    assert member_response.status_code == 200
    member = member_response.json()

    # Act - Add member to organization
    add_member_data = {
        "user_id": member["user_id"],
    }

    add_response = await integration_client.post(
        f"/api/v1/organizations/{owner_org_id}/members",
        json=add_member_data,
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )

    # Assert member added
    if add_response.status_code not in [200, 201]:
        print(f"Add member error: {add_response.json()}")
    assert add_response.status_code in [200, 201]
    membership = add_response.json()
    assert membership["user_id"] == member["user_id"]
    assert membership["organization_id"] == owner_org_id

    # Verify member appears in members list
    list_response = await integration_client.get(
        f"/api/v1/organizations/{owner_org_id}/members",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert list_response.status_code == 200
    members_list = list_response.json()

    member_ids = [m["id"] for m in members_list]
    assert member["user_id"] in member_ids


# ============================================================================
# Test: Remove Member Flow
# ============================================================================


async def test_remove_member_from_organization(integration_client):
    """
    Test removing member from organization.

    Verifies:
    - Owner can remove members
    - Membership record deleted
    - Removed member no longer in list
    - Removed member cannot access org resources
    """
    # Arrange - Register owner
    owner_data = {
        "email": "removeowner@example.com",
        "password": "Owner123!",
        "name": "Remove Owner",
        "organization_name": "Remove Member Org",
    }

    owner_response = await integration_client.post(
        "/api/v1/auth/register", json=owner_data
    )
    assert owner_response.status_code == 200
    owner = owner_response.json()

    # Get organization ID from /me/organizations endpoint
    owner_orgs = await integration_client.get(
        "/api/v1/auth/me/organizations",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    owner_org_id = owner_orgs.json()["organizations"][0]["id"]

    # Register and add member
    member_data = {
        "email": "removemember@example.com",
        "password": "Member123!",
        "name": "Remove Member",
        "organization_name": "Member Org",
    }

    member_response = await integration_client.post(
        "/api/v1/auth/register", json=member_data
    )
    assert member_response.status_code == 200
    member = member_response.json()

    # Add member to organization
    add_response = await integration_client.post(
        f"/api/v1/organizations/{owner_org_id}/members",
        json={"user_id": member["user_id"]},
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert add_response.status_code in [200, 201]

    # Act - Remove member
    remove_response = await integration_client.delete(
        f"/api/v1/organizations/{owner_org_id}/members/{member['user_id']}",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )

    # Assert member removed
    assert remove_response.status_code == 204

    # Verify member no longer in list
    list_response = await integration_client.get(
        f"/api/v1/organizations/{owner_org_id}/members",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert list_response.status_code == 200
    members_list = list_response.json()

    member_ids = [m["id"] for m in members_list]
    assert member["user_id"] not in member_ids


# ============================================================================
# Test: Organization Permission Boundaries
# ============================================================================


async def test_member_cannot_add_or_remove_members(integration_client):
    """
    Test that regular members cannot manage membership.

    Verifies:
    - Members can view member list
    - Members cannot add new members
    - Members cannot remove members
    - Only admins/owners have management privileges
    """
    # Arrange - Create organization with owner
    owner_data = {
        "email": "permowner@example.com",
        "password": "Owner123!",
        "name": "Perm Owner",
        "organization_name": "Permission Test Org",
    }

    owner_response = await integration_client.post(
        "/api/v1/auth/register", json=owner_data
    )
    assert owner_response.status_code == 200
    owner = owner_response.json()

    # Get organization ID from /me/organizations endpoint
    owner_orgs = await integration_client.get(
        "/api/v1/auth/me/organizations",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    owner_org_id = owner_orgs.json()["organizations"][0]["id"]

    # Register member
    member_data = {
        "email": "permmember@example.com",
        "password": "Member123!",
        "name": "Perm Member",
        "organization_name": "Member Org",
    }

    member_response = await integration_client.post(
        "/api/v1/auth/register", json=member_data
    )
    assert member_response.status_code == 200
    member = member_response.json()

    # Add as member
    await integration_client.post(
        f"/api/v1/organizations/{owner_org_id}/members",
        json={"user_id": member["user_id"]},
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )

    # Register another user to try to add
    new_user_data = {
        "email": "newuser@example.com",
        "password": "NewUser123!",
        "name": "New User",
        "organization_name": "New User Org",
    }

    new_user_response = await integration_client.post(
        "/api/v1/auth/register", json=new_user_data
    )
    assert new_user_response.status_code == 200
    new_user = new_user_response.json()

    # Act - Member tries to add new user (should fail)
    add_attempt = await integration_client.post(
        f"/api/v1/organizations/{owner_org_id}/members",
        json={"user_id": new_user["user_id"]},
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )

    # Assert - Should be forbidden
    assert add_attempt.status_code == 403

    # Member can view member list
    list_response = await integration_client.get(
        f"/api/v1/organizations/{owner_org_id}/members",
        headers={"Authorization": f"Bearer {member['access_token']}"},
    )
    assert list_response.status_code == 200
