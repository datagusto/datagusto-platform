import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.models.organization_member import OrganizationMember
from app.models.project_member import ProjectMember
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
async def test_user_with_org(db_session: Session):
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
    
    # Create organization membership as admin
    membership_data = {
        "id": uuid.uuid4(),
        "user_id": user.id,
        "organization_id": organization.id,
        "role": "admin"
    }
    await org_member_repo.create_membership(membership_data)
    
    return {"user": user, "organization": organization}


@pytest.fixture
async def test_project(db_session: Session, test_user_with_org):
    """Create a test project with user membership."""
    project_repo = ProjectRepository(db_session)
    project_member_repo = ProjectMemberRepository(db_session)
    
    user = test_user_with_org["user"]
    organization = test_user_with_org["organization"]
    
    # Create project
    project_data = {
        "id": uuid.uuid4(),
        "name": "Test Project",
        "description": "A test project",
        "organization_id": organization.id,
        "platform_type": "langfuse",
        "platform_config": {
            "public_key": "pk_test_123",
            "secret_key": "sk_test_456",
            "url": "https://langfuse.example.com"
        }
    }
    project = await project_repo.create_project(project_data)
    
    # Create project membership as owner
    membership_data = {
        "id": uuid.uuid4(),
        "user_id": user.id,
        "project_id": project.id,
        "role": "owner"
    }
    await project_member_repo.create_membership(membership_data)
    
    return project


@pytest.fixture
def auth_headers(test_user_with_org):
    """Create authorization headers for test user."""
    user = test_user_with_org["user"]
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestProjectEndpoints:
    """Test Project API endpoints."""
    
    def test_get_user_projects(self, client: TestClient, test_user_with_org, test_project, auth_headers):
        """Test getting user projects."""
        response = client.get("/api/v1/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["project"]["name"] == "Test Project"
        assert data[0]["membership"]["role"] == "owner"
        assert "api_key" not in data[0]["project"]  # API key should not be in public response

    def test_get_organization_projects(self, client: TestClient, test_user_with_org, test_project, auth_headers):
        """Test getting organization projects."""
        org_id = test_user_with_org["organization"].id
        response = client.get(f"/api/v1/projects/organization/{org_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"
        assert "api_key" not in data[0]  # API key should not be in public response

    def test_get_organization_projects_no_access(self, client: TestClient, auth_headers, db_session: Session):
        """Test getting organization projects without access."""
        # Create organization without membership
        org_repo = OrganizationRepository(db_session)
        org_data = {
            "id": uuid.uuid4(),
            "name": "No Access Organization",
            "slug": "no-access-org-11111111",
            "description": "Organization without access",
            "is_active": True
        }
        org = await org_repo.create_organization(org_data)
        
        response = client.get(f"/api/v1/projects/organization/{org.id}", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Access denied to this organization" in response.json()["detail"]

    def test_create_project(self, client: TestClient, test_user_with_org, auth_headers):
        """Test creating a project."""
        org_id = test_user_with_org["organization"].id
        project_data = {
            "name": "New Project",
            "description": "A new project",
            "organization_id": str(org_id),
            "platform_type": "langsmith",
            "platform_config": {
                "api_key": "ls_test_123",
                "project_name": "my-project"
            }
        }
        
        response = client.post("/api/v1/projects/", headers=auth_headers, json=project_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Project"
        assert data["platform_type"] == "langsmith"
        assert data["platform_config"]["api_key"] == "ls_test_123"
        assert "api_key" not in data  # API key should not be in public response

    def test_create_project_no_org_access(self, client: TestClient, auth_headers, db_session: Session):
        """Test creating project without organization access."""
        # Create organization without admin membership
        org_repo = OrganizationRepository(db_session)
        org_data = {
            "id": uuid.uuid4(),
            "name": "No Admin Access Organization",
            "slug": "no-admin-access-org-22222222",
            "description": "Organization without admin access",
            "is_active": True
        }
        org = await org_repo.create_organization(org_data)
        
        project_data = {
            "name": "Should Not Create",
            "organization_id": str(org.id)
        }
        
        response = client.post("/api/v1/projects/", headers=auth_headers, json=project_data)
        
        assert response.status_code == 403
        assert "Admin or owner access required" in response.json()["detail"]

    def test_get_project_details(self, client: TestClient, test_project, auth_headers):
        """Test getting project details."""
        response = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert "members" in data
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "owner"
        assert "api_key" not in data  # API key should not be in public response

    def test_get_project_details_no_access(self, client: TestClient, auth_headers, db_session: Session):
        """Test getting project details without access."""
        # Create project without membership
        org_repo = OrganizationRepository(db_session)
        project_repo = ProjectRepository(db_session)
        
        org_data = {
            "id": uuid.uuid4(),
            "name": "Other Organization",
            "slug": "other-org-33333333",
            "is_active": True
        }
        org = await org_repo.create_organization(org_data)
        
        project_data = {
            "id": uuid.uuid4(),
            "name": "No Access Project",
            "organization_id": org.id
        }
        project = await project_repo.create_project(project_data)
        
        response = client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Access denied to this project" in response.json()["detail"]

    def test_update_project(self, client: TestClient, test_project, auth_headers):
        """Test updating project."""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "platform_type": "custom"
        }
        
        response = client.put(f"/api/v1/projects/{test_project.id}", headers=auth_headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["description"] == "Updated description"
        assert data["platform_type"] == "custom"

    def test_update_project_no_access(self, client: TestClient, auth_headers, db_session: Session):
        """Test updating project without edit access."""
        # Create user with viewer role only
        user_repo = UserRepository(db_session)
        org_repo = OrganizationRepository(db_session)
        project_repo = ProjectRepository(db_session)
        project_member_repo = ProjectMemberRepository(db_session)
        
        # Create organization and project
        org_data = {
            "id": uuid.uuid4(),
            "name": "Viewer Test Organization",
            "slug": "viewer-test-org-44444444",
            "is_active": True
        }
        organization = await org_repo.create_organization(org_data)
        
        project_data = {
            "id": uuid.uuid4(),
            "name": "Viewer Test Project",
            "organization_id": organization.id
        }
        project = await project_repo.create_project(project_data)
        
        # Create user
        user_data = {
            "id": uuid.uuid4(),
            "name": "Viewer User",
            "email": "viewer@example.com",
            "hashed_password": get_password_hash("testpassword"),
            "is_active": True,
            "email_confirmed": True
        }
        user = await user_repo.create_user(user_data)
        
        # Create project membership with viewer role
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": user.id,
            "project_id": project.id,
            "role": "viewer"
        }
        await project_member_repo.create_membership(membership_data)
        
        access_token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        update_data = {
            "name": "Should Not Update"
        }
        
        response = client.put(f"/api/v1/projects/{project.id}", headers=headers, json=update_data)
        
        assert response.status_code == 403
        assert "Edit access required" in response.json()["detail"]

    def test_delete_project(self, client: TestClient, test_project, auth_headers):
        """Test deleting project as owner."""
        response = client.delete(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Project deleted successfully" in response.json()["message"]

    def test_get_project_api_key(self, client: TestClient, test_project, auth_headers):
        """Test getting project API key."""
        response = client.get(f"/api/v1/projects/{test_project.id}/api-key", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("dg_")
        assert "API key retrieved successfully" in data["message"]

    def test_regenerate_api_key(self, client: TestClient, test_project, auth_headers):
        """Test regenerating project API key."""
        # Get original API key
        original_response = client.get(f"/api/v1/projects/{test_project.id}/api-key", headers=auth_headers)
        original_api_key = original_response.json()["api_key"]
        
        # Regenerate API key
        response = client.post(f"/api/v1/projects/{test_project.id}/regenerate-api-key", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("dg_")
        assert data["api_key"] != original_api_key
        assert "API key generated successfully" in data["message"]

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing endpoints without authentication."""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401
        
        fake_project_id = uuid.uuid4()
        response = client.get(f"/api/v1/projects/{fake_project_id}")
        assert response.status_code == 401