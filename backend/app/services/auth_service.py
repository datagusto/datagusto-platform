from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import uuid
import re

from app.schemas.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    @staticmethod
    def _generate_organization_slug(name: str) -> str:
        """
        Generate a URL-friendly slug from organization name.
        """
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        # Add random suffix to ensure uniqueness
        return f"{slug}-{str(uuid.uuid4())[:8]}"
    
    @staticmethod
    async def register_user(user_in: UserCreate, db: Session):
        """
        Register a new user and create their default organization.
        """
        try:
            # Initialize repositories
            user_repo = UserRepository(db)
            org_repo = OrganizationRepository(db)
            org_member_repo = OrganizationMemberRepository(db)
            
            # Check if user already exists
            existing_user = await user_repo.get_user_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create organization first
            org_name = f"{user_in.name}'s Organization"
            org_data = {
                "id": uuid.uuid4(),
                "name": org_name,
                "slug": AuthService._generate_organization_slug(org_name),
                "description": f"Default organization for {user_in.name}",
                "is_active": True
            }
            
            organization = await org_repo.create_organization(org_data)
            
            # Create user
            db_user_data = {
                "id": uuid.uuid4(),
                "email": user_in.email,
                "name": user_in.name,
                "hashed_password": get_password_hash(user_in.password),
                "is_active": True,
                "email_confirmed": True
            }
            
            user = await user_repo.create_user(db_user_data)
            
            # Create organization membership with owner role
            membership_data = {
                "id": uuid.uuid4(),
                "user_id": user.id,
                "organization_id": organization.id,
                "role": "owner"
            }
            
            await org_member_repo.create_membership(membership_data)
            
            return user
        except HTTPException:
            raise
        except Exception as e:
            # Rollback local database transaction
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(email: str, password: str, db: Session):
        """
        Login with email and password to get JWT token.
        """
        # Initialize repository
        db_repo = UserRepository(db)
        
        # Get user from database
        user = await db_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        } 