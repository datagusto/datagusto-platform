import pytest
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from unittest.mock import patch

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.core.security import verify_password


class TestAuthService:
    """Test AuthService functionality."""
    
    def test_generate_organization_slug(self):
        """Test organization slug generation with various inputs."""
        # Test normal name
        slug = AuthService._generate_organization_slug("My Test Organization")
        assert slug.startswith("my-test-organization-")
        assert len(slug.split("-")[-1]) == 8  # UUID suffix
        
        # Test name with special characters
        slug = AuthService._generate_organization_slug("Test@#$%Organization!")
        assert slug.startswith("testorganization-")
        assert len(slug.split("-")[-1]) == 8
        
        # Test empty name
        slug = AuthService._generate_organization_slug("")
        assert slug.startswith("-")
        assert len(slug.split("-")[-1]) == 8
        
        # Test name with multiple spaces
        slug = AuthService._generate_organization_slug("  Multiple   Spaces  Organization  ")
        assert slug.startswith("multiple-spaces-organization-")
        
        # Test very long name
        long_name = "A" * 100
        slug = AuthService._generate_organization_slug(long_name)
        assert slug.startswith("a" * 100 + "-")
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: Session, sample_user_data: UserCreate):
        """Test successful user registration with organization creation."""
        user = await AuthService.register_user(sample_user_data, db_session)
        
        # Check user was created with correct data
        assert user.name == sample_user_data.name
        assert user.email == sample_user_data.email
        assert user.is_active is True
        assert user.email_confirmed is True
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
        
        # Verify password was hashed correctly
        assert user.hashed_password != sample_user_data.password
        assert verify_password(sample_user_data.password, user.hashed_password)
        
        # Check organization was created
        org_repo = OrganizationRepository(db_session)
        organizations = await org_repo.get_organizations_for_user(user.id)
        assert len(organizations) == 1
        
        org = organizations[0]
        assert org.name == f"{sample_user_data.name}'s Organization"
        assert org.slug.startswith("test-users-organization-")
        assert org.description == f"Default organization for {sample_user_data.name}"
        assert org.is_active is True
        
        # Check organization membership was created with owner role
        org_member_repo = OrganizationMemberRepository(db_session)
        membership = await org_member_repo.get_membership(user.id, org.id)
        assert membership is not None
        assert membership.role == "owner"
        assert membership.user_id == user.id
        assert membership.organization_id == org.id
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, db_session: Session, sample_user_data: UserCreate):
        """Test registration failure with duplicate email."""
        # Register user first time - should succeed
        await AuthService.register_user(sample_user_data, db_session)
        
        # Try to register same email again - should fail
        duplicate_user_data = UserCreate(
            name="Different User",
            email=sample_user_data.email,  # Same email
            password="differentpassword"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.register_user(duplicate_user_data, db_session)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_user_rollback_on_failure(self, db_session: Session, sample_user_data: UserCreate):
        """Test transaction rollback when organization creation fails."""
        with patch('app.repositories.organization_repository.OrganizationRepository.create_organization') as mock_create_org:
            # Make organization creation fail
            mock_create_org.side_effect = Exception("Organization creation failed")
            
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.register_user(sample_user_data, db_session)
            
            assert exc_info.value.status_code == 400
            assert "Registration failed" in str(exc_info.value.detail)
            
            # Verify user was not created (transaction rolled back)
            user_repo = UserRepository(db_session)
            user = await user_repo.get_user_by_email(sample_user_data.email)
            assert user is None
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, db_session: Session, sample_user_data: UserCreate):
        """Test successful user login."""
        # Register user first
        user = await AuthService.register_user(sample_user_data, db_session)
        
        # Login with correct credentials
        login_result = await AuthService.login_user(
            sample_user_data.email, sample_user_data.password, db_session
        )
        
        # Check response structure
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert login_result["token_type"] == "bearer"
        
        # Verify tokens are not empty
        assert len(login_result["access_token"]) > 0
        assert len(login_result["refresh_token"]) > 0
        assert login_result["access_token"] != login_result["refresh_token"]
    
    @pytest.mark.asyncio
    async def test_login_user_wrong_password(self, db_session: Session, sample_user_data: UserCreate):
        """Test login failure with wrong password."""
        # Register user first
        await AuthService.register_user(sample_user_data, db_session)
        
        # Try login with wrong password
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login_user(
                sample_user_data.email, "wrongpassword", db_session
            )
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)
        assert "WWW-Authenticate" in exc_info.value.headers
    
    @pytest.mark.asyncio
    async def test_login_user_nonexistent_email(self, db_session: Session):
        """Test login failure with non-existent email."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login_user(
                "nonexistent@example.com", "anypassword", db_session
            )
        
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)
        assert "WWW-Authenticate" in exc_info.value.headers
    
    @pytest.mark.asyncio
    async def test_login_user_empty_credentials(self, db_session: Session):
        """Test login with empty credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login_user("", "", db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_register_user_with_various_names(self, db_session: Session):
        """Test user registration with various name formats."""
        test_cases = [
            ("John Doe", "john@example.com"),
            ("Mary Jane Smith", "mary@example.com"),
            ("José María González", "jose@example.com"),
            ("李小明", "li@example.com"),
            ("A", "a@example.com"),  # Single character
            ("A" * 50, "long@example.com"),  # Long name
        ]
        
        for name, email in test_cases:
            user_data = UserCreate(name=name, email=email, password="password123")
            user = await AuthService.register_user(user_data, db_session)
            
            assert user.name == name
            assert user.email == email
            
            # Check organization name is correctly generated
            expected_org_name = f"{name}'s Organization"
            org_repo = OrganizationRepository(db_session)
            organizations = await org_repo.get_organizations_for_user(user.id)
            assert len(organizations) == 1
            assert organizations[0].name == expected_org_name
    
    @pytest.mark.asyncio
    async def test_concurrent_user_registration(self, db_session: Session):
        """Test handling of concurrent registration attempts with same email."""
        user_data_1 = UserCreate(name="User 1", email="concurrent@example.com", password="pass1")
        user_data_2 = UserCreate(name="User 2", email="concurrent@example.com", password="pass2")
        
        # Register first user
        user1 = await AuthService.register_user(user_data_1, db_session)
        assert user1.name == "User 1"
        
        # Second registration should fail
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.register_user(user_data_2, db_session)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio 
    async def test_organization_slug_uniqueness(self, db_session: Session):
        """Test that organization slugs are unique even with similar names."""
        user_data_1 = UserCreate(name="Test User", email="user1@example.com", password="pass1")
        user_data_2 = UserCreate(name="Test User", email="user2@example.com", password="pass2")
        
        # Register both users
        user1 = await AuthService.register_user(user_data_1, db_session)
        user2 = await AuthService.register_user(user_data_2, db_session)
        
        # Get their organizations
        org_repo = OrganizationRepository(db_session)
        orgs1 = await org_repo.get_organizations_for_user(user1.id)
        orgs2 = await org_repo.get_organizations_for_user(user2.id)
        
        # Both should have organizations with different slugs
        assert len(orgs1) == 1
        assert len(orgs2) == 1
        assert orgs1[0].slug != orgs2[0].slug
        assert orgs1[0].slug.startswith("test-users-organization-")
        assert orgs2[0].slug.startswith("test-users-organization-")
    
    @pytest.mark.asyncio
    async def test_password_security_requirements(self, db_session: Session):
        """Test password handling and security."""
        user_data = UserCreate(
            name="Security Test User",
            email="security@example.com", 
            password="securepassword123"
        )
        
        user = await AuthService.register_user(user_data, db_session)
        
        # Password should be hashed, not stored in plain text
        assert user.hashed_password != user_data.password
        assert len(user.hashed_password) > 50  # bcrypt hashes are long
        assert user.hashed_password.startswith("$2b$")  # bcrypt prefix
        
        # Verify password verification works
        assert verify_password(user_data.password, user.hashed_password)
        assert not verify_password("wrongpassword", user.hashed_password)
        assert not verify_password("", user.hashed_password)
        
        # Check organization was created
        org_repo = OrganizationRepository(db_session)
        user_orgs = await org_repo.get_organizations_for_user(user.id)
        assert len(user_orgs) == 1
        organization = user_orgs[0]
        assert organization is not None
        assert organization.name == "Security Test User's Organization"
        assert organization.slug.startswith("security-test-users-organization-")
        assert organization.description == "Default organization for Security Test User"
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