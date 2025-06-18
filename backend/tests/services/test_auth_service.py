import pytest
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository


class TestAuthService:
    """Test AuthService functionality."""
    
    def test_generate_organization_slug(self):
        """Test organization slug generation."""
        # Test normal name
        slug = AuthService._generate_organization_slug("My Test Organization")
        assert slug.startswith("my-test-organization-")
        assert len(slug.split("-")[-1]) == 8  # UUID suffix
        
        # Test name with special characters
        slug = AuthService._generate_organization_slug("Test@#$%Organization!")
        assert slug.startswith("testorganization-")
        
        # Test empty name
        slug = AuthService._generate_organization_slug("")
        assert slug.startswith("-")
        assert len(slug.split("-")[-1]) == 8
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: Session):
        """Test successful user registration with organization creation."""
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="testpassword123"
        )
        
        user = await AuthService.register_user(user_data, db_session)
        
        # Check user was created
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.email_confirmed is True
        
        # Check organization was created
        org_repo = OrganizationRepository(db_session)
        user_orgs = await org_repo.get_organizations_for_user(user.id)
        assert len(user_orgs) == 1
        organization = user_orgs[0]
        assert organization is not None
        assert organization.name == "Test User's Organization"
        assert organization.slug.startswith("test-users-organization-")
        assert organization.description == "Default organization for Test User"
        assert organization.is_active is True
        
        # Check membership was created
        org_member_repo = OrganizationMemberRepository(db_session)
        membership = await org_member_repo.get_membership(user.id, organization.id)
        assert membership is not None
        assert membership.role == "owner"
        assert membership.user_id == user.id
        assert membership.organization_id == organization.id
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, db_session: Session):
        """Test registration with duplicate email."""
        user_data = UserCreate(
            name="First User",
            email="duplicate@example.com",
            password="testpassword123"
        )
        
        # First registration should succeed
        await AuthService.register_user(user_data, db_session)
        
        # Second registration with same email should fail
        user_data2 = UserCreate(
            name="Second User",
            email="duplicate@example.com",
            password="anotherpassword123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.register_user(user_data2, db_session)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, db_session: Session):
        """Test successful user login."""
        # First register a user
        user_data = UserCreate(
            name="Login Test User",
            email="login@example.com",
            password="loginpassword123"
        )
        
        user = await AuthService.register_user(user_data, db_session)
        
        # Now test login
        login_result = await AuthService.login_user("login@example.com", "loginpassword123", db_session)
        
        assert "access_token" in login_result
        assert "token_type" in login_result
        assert login_result["token_type"] == "bearer"
        assert isinstance(login_result["access_token"], str)
        assert len(login_result["access_token"]) > 0
    
    @pytest.mark.asyncio
    async def test_login_user_wrong_email(self, db_session: Session):
        """Test login with non-existent email."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login_user("nonexistent@example.com", "anypassword", db_session)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_login_user_wrong_password(self, db_session: Session):
        """Test login with wrong password."""
        # First register a user
        user_data = UserCreate(
            name="Wrong Password Test",
            email="wrongpass@example.com",
            password="correctpassword123"
        )
        
        await AuthService.register_user(user_data, db_session)
        
        # Try to login with wrong password
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login_user("wrongpass@example.com", "wrongpassword", db_session)
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_multiple_users_unique_organizations(self, db_session: Session):
        """Test that multiple users get unique organizations."""
        user1_data = UserCreate(
            name="User One",
            email="user1@example.com",
            password="password123"
        )
        
        user2_data = UserCreate(
            name="User Two",
            email="user2@example.com",
            password="password123"
        )
        
        user1 = await AuthService.register_user(user1_data, db_session)
        user2 = await AuthService.register_user(user2_data, db_session)
        
        # Check organization details
        org_repo = OrganizationRepository(db_session)
        user1_orgs = await org_repo.get_organizations_for_user(user1.id)
        user2_orgs = await org_repo.get_organizations_for_user(user2.id)
        
        assert len(user1_orgs) == 1
        assert len(user2_orgs) == 1
        
        org1 = user1_orgs[0]
        org2 = user2_orgs[0]
        
        # Check that users have different organizations
        assert org1.id != org2.id
        
        assert org1.name == "User One's Organization"
        assert org2.name == "User Two's Organization"
        assert org1.slug != org2.slug
        
        # Check memberships
        org_member_repo = OrganizationMemberRepository(db_session)
        
        membership1 = await org_member_repo.get_membership(user1.id, org1.id)
        membership2 = await org_member_repo.get_membership(user2.id, org2.id)
        
        assert membership1.role == "owner"
        assert membership2.role == "owner"
        
        # Check cross-membership doesn't exist
        cross_membership1 = await org_member_repo.get_membership(user1.id, org2.id)
        cross_membership2 = await org_member_repo.get_membership(user2.id, org1.id)
        
        assert cross_membership1 is None
        assert cross_membership2 is None