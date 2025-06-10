import pytest
import uuid
from sqlalchemy.orm import Session

from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
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


class TestOrganizationRepository:
    """Test OrganizationRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_organization(self, db_session: Session):
        """Test creating an organization."""
        org_repo = OrganizationRepository(db_session)
        org_data = {
            "id": uuid.uuid4(),
            "name": "New Organization",
            "slug": "new-organization-87654321",
            "description": "A new test organization",
            "avatar_url": "https://example.com/avatar.jpg",
            "settings": {"theme": "dark"},
            "is_active": True
        }
        
        organization = await org_repo.create_organization(org_data)
        
        assert organization.id == org_data["id"]
        assert organization.name == "New Organization"
        assert organization.slug == "new-organization-87654321"
        assert organization.description == "A new test organization"
        assert organization.avatar_url == "https://example.com/avatar.jpg"
        assert organization.settings == {"theme": "dark"}
        assert organization.is_active is True
        assert organization.created_at is not None
        assert organization.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, db_session: Session, sample_organization):
        """Test getting organization by ID."""
        org_repo = OrganizationRepository(db_session)
        
        # Test existing organization
        organization = await org_repo.get_organization_by_id(sample_organization.id)
        assert organization is not None
        assert organization.id == sample_organization.id
        assert organization.name == sample_organization.name
        
        # Test non-existing organization
        non_existing_id = uuid.uuid4()
        organization = await org_repo.get_organization_by_id(non_existing_id)
        assert organization is None
    
    @pytest.mark.asyncio
    async def test_get_organization_by_slug(self, db_session: Session, sample_organization):
        """Test getting organization by slug."""
        org_repo = OrganizationRepository(db_session)
        
        # Test existing organization
        organization = await org_repo.get_organization_by_slug(sample_organization.slug)
        assert organization is not None
        assert organization.slug == sample_organization.slug
        assert organization.name == sample_organization.name
        
        # Test non-existing slug
        organization = await org_repo.get_organization_by_slug("non-existing-slug")
        assert organization is None
    
    @pytest.mark.asyncio
    async def test_get_organizations_for_user(self, db_session: Session, sample_organization, sample_user):
        """Test getting organizations for a user."""
        org_repo = OrganizationRepository(db_session)
        org_member_repo = OrganizationMemberRepository(db_session)
        
        # Create membership
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "organization_id": sample_organization.id,
            "role": "member"
        }
        await org_member_repo.create_membership(membership_data)
        
        # Test getting organizations for user
        organizations = await org_repo.get_organizations_for_user(sample_user.id)
        assert len(organizations) == 1
        assert organizations[0].id == sample_organization.id
        
        # Test getting organizations for user with no memberships
        other_user_id = uuid.uuid4()
        organizations = await org_repo.get_organizations_for_user(other_user_id)
        assert len(organizations) == 0
    
    @pytest.mark.asyncio
    async def test_update_organization(self, db_session: Session, sample_organization):
        """Test updating an organization."""
        org_repo = OrganizationRepository(db_session)
        
        update_data = {
            "name": "Updated Organization",
            "description": "Updated description",
            "avatar_url": "https://example.com/new-avatar.jpg",
            "settings": {"theme": "light", "notifications": True}
        }
        
        updated_org = await org_repo.update_organization(sample_organization.id, update_data)
        
        assert updated_org is not None
        assert updated_org.name == "Updated Organization"
        assert updated_org.description == "Updated description"
        assert updated_org.avatar_url == "https://example.com/new-avatar.jpg"
        assert updated_org.settings == {"theme": "light", "notifications": True}
        assert updated_org.id == sample_organization.id  # ID should remain same
        
        # Test updating non-existing organization
        non_existing_id = uuid.uuid4()
        result = await org_repo.update_organization(non_existing_id, {"name": "Should not work"})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_organization(self, db_session: Session, sample_organization):
        """Test soft deleting an organization."""
        org_repo = OrganizationRepository(db_session)
        
        # Test successful deletion
        result = await org_repo.delete_organization(sample_organization.id)
        assert result is True
        
        # Check that organization is marked as inactive
        organization = await org_repo.get_organization_by_id(sample_organization.id)
        assert organization is not None
        assert organization.is_active is False
        
        # Test deleting non-existing organization
        non_existing_id = uuid.uuid4()
        result = await org_repo.delete_organization(non_existing_id)
        assert result is False


class TestOrganizationMemberRepository:
    """Test OrganizationMemberRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_membership(self, db_session: Session, sample_organization, sample_user):
        """Test creating organization membership."""
        org_member_repo = OrganizationMemberRepository(db_session)
        
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "organization_id": sample_organization.id,
            "role": "admin",
            "invited_by": None
        }
        
        membership = await org_member_repo.create_membership(membership_data)
        
        assert membership.id == membership_data["id"]
        assert membership.user_id == sample_user.id
        assert membership.organization_id == sample_organization.id
        assert membership.role == "admin"
        assert membership.invited_by is None
        assert membership.joined_at is not None
        assert membership.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_membership(self, db_session: Session, sample_organization, sample_user):
        """Test getting membership."""
        org_member_repo = OrganizationMemberRepository(db_session)
        
        # Create membership first
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "organization_id": sample_organization.id,
            "role": "member"
        }
        created_membership = await org_member_repo.create_membership(membership_data)
        
        # Test getting existing membership
        membership = await org_member_repo.get_membership(sample_user.id, sample_organization.id)
        assert membership is not None
        assert membership.id == created_membership.id
        assert membership.role == "member"
        
        # Test getting non-existing membership
        other_user_id = uuid.uuid4()
        membership = await org_member_repo.get_membership(other_user_id, sample_organization.id)
        assert membership is None
    
    @pytest.mark.asyncio
    async def test_role_checking_methods(self, db_session: Session, sample_organization, sample_user):
        """Test role checking methods."""
        org_member_repo = OrganizationMemberRepository(db_session)
        
        # Test with owner role
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "organization_id": sample_organization.id,
            "role": "owner"
        }
        await org_member_repo.create_membership(membership_data)
        
        assert await org_member_repo.is_owner(sample_user.id, sample_organization.id) is True
        assert await org_member_repo.is_admin_or_owner(sample_user.id, sample_organization.id) is True
        assert await org_member_repo.has_access(sample_user.id, sample_organization.id) is True
        
        # Test with admin role
        await org_member_repo.update_membership_role(sample_user.id, sample_organization.id, "admin")
        
        assert await org_member_repo.is_owner(sample_user.id, sample_organization.id) is False
        assert await org_member_repo.is_admin_or_owner(sample_user.id, sample_organization.id) is True
        assert await org_member_repo.has_access(sample_user.id, sample_organization.id) is True
        
        # Test with member role
        await org_member_repo.update_membership_role(sample_user.id, sample_organization.id, "member")
        
        assert await org_member_repo.is_owner(sample_user.id, sample_organization.id) is False
        assert await org_member_repo.is_admin_or_owner(sample_user.id, sample_organization.id) is False
        assert await org_member_repo.has_access(sample_user.id, sample_organization.id) is True
        
        # Test with no membership
        other_user_id = uuid.uuid4()
        assert await org_member_repo.is_owner(other_user_id, sample_organization.id) is False
        assert await org_member_repo.is_admin_or_owner(other_user_id, sample_organization.id) is False
        assert await org_member_repo.has_access(other_user_id, sample_organization.id) is False
    
    @pytest.mark.asyncio
    async def test_delete_membership(self, db_session: Session, sample_organization, sample_user):
        """Test deleting membership."""
        org_member_repo = OrganizationMemberRepository(db_session)
        
        # Create membership first
        membership_data = {
            "id": uuid.uuid4(),
            "user_id": sample_user.id,
            "organization_id": sample_organization.id,
            "role": "member"
        }
        await org_member_repo.create_membership(membership_data)
        
        # Test successful deletion
        result = await org_member_repo.delete_membership(sample_user.id, sample_organization.id)
        assert result is True
        
        # Verify membership is deleted
        membership = await org_member_repo.get_membership(sample_user.id, sample_organization.id)
        assert membership is None
        
        # Test deleting non-existing membership
        result = await org_member_repo.delete_membership(sample_user.id, sample_organization.id)
        assert result is False