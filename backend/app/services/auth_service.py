from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.schemas.user import UserCreate
from app.repositories.supabase_repository import SupabaseUserRepository
from app.repositories.user_repository import UserRepository
from app.services.organization_service import OrganizationService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    async def register_user(user_in: UserCreate, db: Session):
        """
        Register a new user with Supabase and local database.
        """
        supabase_user = None
        try:
            # Initialize repositories
            supabase_repo = SupabaseUserRepository()
            db_repo = UserRepository(db)
            
            print(f"Creating user with email: {user_in.email}")
            # Register user with Supabase
            supabase_user = await supabase_repo.create_user(user_in.email, user_in.password)
            
            # Create user in local database
            db_user_data = {
                "id": supabase_user.id,
                "email": user_in.email,
                "name": user_in.name,
                "hashed_password": pwd_context.hash(user_in.password),
                "is_active": True,
                "email_confirmed": False  # Default to false, will be updated after email verification
            }
            
            user = await db_repo.create_user(db_user_data)
            
            # Create default organization for the user
            await OrganizationService.create_default_organization(user, db)
            
            return user
        except Exception as e:
            # Rollback local database transaction
            db.rollback()
            
            # Rollback Supabase user creation if it was successful
            if supabase_user:
                try:
                    supabase_repo = SupabaseUserRepository()
                    await supabase_repo.delete_user(supabase_user.id)
                except Exception as delete_error:
                    # Log the error but continue with the main exception
                    print(f"Failed to delete Supabase user during rollback: {delete_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
    
    @staticmethod
    async def login_user(email: str, password: str):
        """
        Login with email and password to get JWT token.
        """
        try:
            # Initialize repository
            supabase_repo = SupabaseUserRepository()
            
            # Authenticate with Supabase
            return await supabase_repo.authenticate_user(email, password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            ) 