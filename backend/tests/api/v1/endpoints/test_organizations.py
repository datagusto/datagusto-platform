import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def test_user(db_session: Session):
    """Create a test user with organization."""
    user_repo = UserRepository(db_session)
    org_repo = OrganizationRepository(db_session)
    org_member_repo = OrganizationMemberRepository(db_session)
    
    # Create organization first
    org_data = {
        "id": uuid.uuid4(),
        "name": "Test Organization",
        "slug": "test-org-12345678",
        "description": "Test organization description",
        "is_active": True
    }
    organization = await org_repo.create_organization(org_data)
    
    # Create user
    user_data = {
        "id": uuid.uuid4(),
        "name": "Test User",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpassword"),
        "is_active": True,
        "email_confirmed": True
    }
    user = await user_repo.create_user(user_data)
    
    # Create membership
    membership_data = {
        "id": uuid.uuid4(),
        "user_id": user.id,
        "organization_id": organization.id,
        "role": "owner"
    }
    await org_member_repo.create_membership(membership_data)
    
    return {"user": user, "organization": organization}


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers for test user."""
    user = test_user["user"]
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestOrganizationEndpoints:
    """Test Organization API endpoints."""
    
    def test_get_user_organizations(self, client: TestClient, test_user, auth_headers):
        """Test getting user organizations."""
        response = client.get("/api/v1/organizations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["organization"]["name"] == "Test Organization"
        assert data[0]["membership"]["role"] == "owner"
    
    
    def test_get_organization_details(self, client: TestClient, test_user, auth_headers):
        """Test getting organization details."""
        org_id = test_user["organization"].id
        response = client.get(f"/api/v1/organizations/{org_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Organization"
        assert "members" in data
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "owner"
    
    @pytest.mark.asyncio
    async def test_get_organization_details_no_access(self, client: TestClient, test_user, auth_headers, db_session: Session):
        """Test getting organization details without access."""
        # Create organization without membership
        org_repo = OrganizationRepository(db_session)
        org_data = {
            "id": uuid.uuid4(),
            "name": "No Access Organization",
            "slug": "no-access-org-22222222",
            "description": "Organization without access",
            "is_active": True
        }
        org = await org_repo.create_organization(org_data)
        
        response = client.get(f"/api/v1/organizations/{org.id}", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Access denied to this organization" in response.json()["detail"]
    
    def test_update_organization_as_owner(self, client: TestClient, test_user, auth_headers):
        """Test updating organization as owner."""
        org_id = test_user["organization"].id
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/organizations/{org_id}", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Organization Name"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_update_organization_as_member(self, client: TestClient, db_session: Session):
        """Test updating organization as member (should fail)."""
        # Create user with member role
        user_repo = UserRepository(db_session)
        org_repo = OrganizationRepository(db_session)
        org_member_repo = OrganizationMemberRepository(db_session)
        
        # Create organization
        org_data = {
            "id": uuid.uuid4(),
            "name": "Member Test Organization",
            "slug": "member-test-org-33333333",
            "description": "Test organization for member",
            "is_active": True
        }
        organization = await org_repo.create_organization(org_data)
        
        # Create user
        user_data = {
            "id": uuid.uuid4(),
            "name": "Member User",
            "email": "member@example.com",
            "hashed_password": get_password_hash("testpassword"),
            "is_active": True,
            "email_confirmed": True
        }
        user = await user_repo.create_user(user_data)
        
        # Create membership with member role
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": user.id,
            "organization_id": organization.id,
            "role": "member"
        }
        await org_member_repo.create_membership(membership_data)
        
        access_token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        update_data = {
            "name": "Should Not Update"
        }
        
        response = client.put(f"/api/v1/organizations/{organization.id}", headers=headers, json=update_data)
        
        assert response.status_code == 403
        assert "Admin or owner access required" in response.json()["detail"]
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing endpoints without authentication."""
        response = client.get("/api/v1/organizations/")
        assert response.status_code == 401