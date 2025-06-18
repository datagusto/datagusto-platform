import pytest
import uuid
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
async def sample_organization(db_session: Session):
    """Create a sample organization for testing."""
    org_repo = OrganizationRepository(db_session)
    org_data = {
        "id": uuid.uuid4(),
        "name": "Test Organization",
        "slug": "test-organization-12345678",
        "description": "A test organization",
        "is_active": True
    }
    return await org_repo.create_organization(org_data)


@pytest.fixture
async def sample_user(db_session: Session):
    """Create a sample user for testing."""
    user_repo = UserRepository(db_session)
    user_data = {
        "id": uuid.uuid4(),
        "name": "Test User",
        "email": "test@example.com",
        "hashed_password": "hashed_password",
        "is_active": True,
        "email_confirmed": True
    }
    return await user_repo.create_user(user_data)


@pytest.fixture
async def sample_project(db_session: Session, sample_organization):
    """Create a sample project for testing."""
    project_repo = ProjectRepository(db_session)
    project_data = {
        "id": uuid.uuid4(),
        "name": "Test Project",
        "description": "A test project",
        "organization_id": sample_organization.id,
        "platform_type": "langfuse",
        "platform_config": {
            "public_key": "pk_test_123",
            "secret_key": "sk_test_456",
            "url": "https://langfuse.example.com"
        }
    }
    return await project_repo.create_project(project_data)


class TestProjectRepository:
    """Test ProjectRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, db_session: Session, sample_organization):
        """Test creating a project."""
        project_repo = ProjectRepository(db_session)
        project_data = {
            "id": uuid.uuid4(),
            "name": "New Project",
            "description": "A new test project",
            "organization_id": sample_organization.id,
            "platform_type": "langsmith",
            "platform_config": {
                "api_key": "ls_test_123",
                "project_name": "my-project"
            }
        }
        
        project = await project_repo.create_project(project_data)
        
        assert project.id == project_data["id"]
        assert project.name == "New Project"
        assert project.description == "A new test project"
        assert project.organization_id == sample_organization.id
        assert project.platform_type == "langsmith"
        assert project.platform_config["api_key"] == "ls_test_123"
        assert project.api_key is not None
        assert project.api_key.startswith("dg_")
        assert project.created_at is not None
        assert project.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_project_auto_generates_api_key(self, db_session: Session, sample_organization):
        """Test that API key is auto-generated if not provided."""
        project_repo = ProjectRepository(db_session)
        project_data = {
            "id": uuid.uuid4(),
            "name": "Auto API Key Project",
            "organization_id": sample_organization.id
        }
        
        project = await project_repo.create_project(project_data)
        
        assert project.api_key is not None
        assert project.api_key.startswith("dg_")
        assert len(project.api_key) > 10  # Should be sufficiently long

    @pytest.mark.asyncio
    async def test_get_project_by_id(self, db_session: Session, sample_project):
        """Test getting project by ID."""
        project_repo = ProjectRepository(db_session)
        
        # Test existing project
        project = await project_repo.get_project_by_id(sample_project.id)
        assert project is not None
        assert project.id == sample_project.id
        assert project.name == sample_project.name
        
        # Test non-existing project
        non_existing_id = uuid.uuid4()
        project = await project_repo.get_project_by_id(non_existing_id)
        assert project is None

    @pytest.mark.asyncio
    async def test_get_project_by_api_key(self, db_session: Session, sample_project):
        """Test getting project by API key."""
        project_repo = ProjectRepository(db_session)
        
        # Test existing project
        project = await project_repo.get_project_by_api_key(sample_project.api_key)
        assert project is not None
        assert project.api_key == sample_project.api_key
        assert project.name == sample_project.name
        
        # Test non-existing API key
        project = await project_repo.get_project_by_api_key("invalid_api_key")
        assert project is None

    @pytest.mark.asyncio
    async def test_get_projects_for_organization(self, db_session: Session, sample_organization, sample_project):
        """Test getting projects for an organization."""
        project_repo = ProjectRepository(db_session)
        
        # Create another project in the same organization
        project2_data = {
            "id": uuid.uuid4(),
            "name": "Second Project",
            "organization_id": sample_organization.id
        }
        project2 = await project_repo.create_project(project2_data)
        
        # Test getting projects for organization
        projects = await project_repo.get_projects_for_organization(sample_organization.id)
        assert len(projects) == 2
        project_ids = [p.id for p in projects]
        assert sample_project.id in project_ids
        assert project2.id in project_ids
        
        # Test getting projects for organization with no projects
        other_org_id = uuid.uuid4()
        projects = await project_repo.get_projects_for_organization(other_org_id)
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_update_project(self, db_session: Session, sample_project):
        """Test updating a project."""
        project_repo = ProjectRepository(db_session)
        
        update_data = {
            "name": "Updated Project",
            "description": "Updated description",
            "platform_type": "custom",
            "platform_config": {"custom_endpoint": "https://api.example.com"}
        }
        
        updated_project = await project_repo.update_project(sample_project.id, update_data)
        
        assert updated_project is not None
        assert updated_project.name == "Updated Project"
        assert updated_project.description == "Updated description"
        assert updated_project.platform_type == "custom"
        assert updated_project.platform_config["custom_endpoint"] == "https://api.example.com"
        assert updated_project.id == sample_project.id  # ID should remain same
        
        # Test updating non-existing project
        non_existing_id = uuid.uuid4()
        result = await project_repo.update_project(non_existing_id, {"name": "Should not work"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_project(self, db_session: Session, sample_project):
        """Test deleting a project."""
        project_repo = ProjectRepository(db_session)
        
        # Test successful deletion
        result = await project_repo.delete_project(sample_project.id)
        assert result is True
        
        # Check that project is deleted
        project = await project_repo.get_project_by_id(sample_project.id)
        assert project is None
        
        # Test deleting non-existing project
        non_existing_id = uuid.uuid4()
        result = await project_repo.delete_project(non_existing_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_regenerate_api_key(self, db_session: Session, sample_project):
        """Test regenerating API key for a project."""
        project_repo = ProjectRepository(db_session)
        
        original_api_key = sample_project.api_key
        
        # Test successful regeneration
        new_api_key = await project_repo.regenerate_api_key(sample_project.id)
        assert new_api_key is not None
        assert new_api_key != original_api_key
        assert new_api_key.startswith("dg_")
        
        # Verify the project has the new API key
        updated_project = await project_repo.get_project_by_id(sample_project.id)
        assert updated_project.api_key == new_api_key
        
        # Test regenerating for non-existing project
        non_existing_id = uuid.uuid4()
        result = await project_repo.regenerate_api_key(non_existing_id)
        assert result is None


class TestProjectMemberRepository:
    """Test ProjectMemberRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_membership(self, db_session: Session, sample_project, sample_user):
        """Test creating project membership."""
        project_member_repo = ProjectMemberRepository(db_session)
        
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "project_id": sample_project.id,
            "role": "admin",
            "invited_by": None
        }
        
        membership = await project_member_repo.create_membership(membership_data)
        
        assert membership.id == membership_data["id"]
        assert membership.user_id == sample_user.id
        assert membership.project_id == sample_project.id
        assert membership.role == "admin"
        assert membership.invited_by is None
        assert membership.joined_at is not None
        assert membership.created_at is not None

    @pytest.mark.asyncio
    async def test_get_membership(self, db_session: Session, sample_project, sample_user):
        """Test getting membership."""
        project_member_repo = ProjectMemberRepository(db_session)
        
        # Create membership first
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "project_id": sample_project.id,
            "role": "member"
        }
        created_membership = await project_member_repo.create_membership(membership_data)
        
        # Test getting existing membership
        membership = await project_member_repo.get_membership(sample_user.id, sample_project.id)
        assert membership is not None
        assert membership.id == created_membership.id
        assert membership.role == "member"
        
        # Test getting non-existing membership
        other_user_id = uuid.uuid4()
        membership = await project_member_repo.get_membership(other_user_id, sample_project.id)
        assert membership is None

    @pytest.mark.asyncio
    async def test_role_checking_methods(self, db_session: Session, sample_project, sample_user):
        """Test role checking methods."""
        project_member_repo = ProjectMemberRepository(db_session)
        
        # Test with owner role
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "project_id": sample_project.id,
            "role": "owner"
        }
        await project_member_repo.create_membership(membership_data)
        
        assert await project_member_repo.is_owner(sample_user.id, sample_project.id) is True
        assert await project_member_repo.is_admin_or_owner(sample_user.id, sample_project.id) is True
        assert await project_member_repo.can_edit(sample_user.id, sample_project.id) is True
        assert await project_member_repo.has_access(sample_user.id, sample_project.id) is True
        
        # Test with admin role
        await project_member_repo.update_membership_role(sample_user.id, sample_project.id, "admin")
        
        assert await project_member_repo.is_owner(sample_user.id, sample_project.id) is False
        assert await project_member_repo.is_admin_or_owner(sample_user.id, sample_project.id) is True
        assert await project_member_repo.can_edit(sample_user.id, sample_project.id) is True
        assert await project_member_repo.has_access(sample_user.id, sample_project.id) is True
        
        # Test with member role
        await project_member_repo.update_membership_role(sample_user.id, sample_project.id, "member")
        
        assert await project_member_repo.is_owner(sample_user.id, sample_project.id) is False
        assert await project_member_repo.is_admin_or_owner(sample_user.id, sample_project.id) is False
        assert await project_member_repo.can_edit(sample_user.id, sample_project.id) is True
        assert await project_member_repo.has_access(sample_user.id, sample_project.id) is True
        
        # Test with viewer role
        await project_member_repo.update_membership_role(sample_user.id, sample_project.id, "viewer")
        
        assert await project_member_repo.is_owner(sample_user.id, sample_project.id) is False
        assert await project_member_repo.is_admin_or_owner(sample_user.id, sample_project.id) is False
        assert await project_member_repo.can_edit(sample_user.id, sample_project.id) is False
        assert await project_member_repo.has_access(sample_user.id, sample_project.id) is True
        
        # Test with no membership
        other_user_id = uuid.uuid4()
        assert await project_member_repo.is_owner(other_user_id, sample_project.id) is False
        assert await project_member_repo.is_admin_or_owner(other_user_id, sample_project.id) is False
        assert await project_member_repo.can_edit(other_user_id, sample_project.id) is False
        assert await project_member_repo.has_access(other_user_id, sample_project.id) is False

    @pytest.mark.asyncio
    async def test_delete_membership(self, db_session: Session, sample_project, sample_user):
        """Test deleting membership."""
        project_member_repo = ProjectMemberRepository(db_session)
        
        # Create membership first
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "project_id": sample_project.id,
            "role": "member"
        }
        await project_member_repo.create_membership(membership_data)
        
        # Test successful deletion
        result = await project_member_repo.delete_membership(sample_user.id, sample_project.id)
        assert result is True
        
        # Verify membership is deleted
        membership = await project_member_repo.get_membership(sample_user.id, sample_project.id)
        assert membership is None
        
        # Test deleting non-existing membership
        result = await project_member_repo.delete_membership(sample_user.id, sample_project.id)
        assert result is False