from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.models.user import User as UserModel
from app.schemas.user import UserUpdate
from app.repositories.supabase_repository import SupabaseUserRepository
from app.repositories.user_repository import UserRepository


class UserService:
    @staticmethod
    async def get_user(user_id: str, db: Session):
        """
        Get user by ID from database.
        """
        db_repo = UserRepository(db)
        user = await db_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    @staticmethod
    async def update_user(current_user: UserModel, user_in: UserUpdate, db: Session):
        """
        Update user in Supabase and local database.
        """
        try:
            # Initialize repositories
            supabase_repo = SupabaseUserRepository()
            db_repo = UserRepository(db)
            
            # Update email in Supabase if provided
            if user_in.email is not None and user_in.email != current_user.email:
                await supabase_repo.update_user(
                    current_user.id,
                    {"email": user_in.email}
                )
            
            # Update password in Supabase if provided
            if user_in.password is not None:
                await supabase_repo.update_user(
                    current_user.id,
                    {"password": user_in.password}
                )
            
            # Update user in database
            user_data = user_in.model_dump(exclude_unset=True)
            if "password" in user_data:
                del user_data["password"]  # Skip password as it's already updated in Supabase
            
            updated_user = await db_repo.update_user(current_user.id, user_data)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return updated_user
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update user: {str(e)}"
            )

    @staticmethod
    async def delete_user(current_user: UserModel, db: Session):
        """
        Delete user from Supabase and local database.
        """
        try:
            # Initialize repositories
            supabase_repo = SupabaseUserRepository()
            db_repo = UserRepository(db)
            
            # Delete user from Supabase
            await supabase_repo.delete_user(current_user.id)
            
            # Delete user from database
            success = await db_repo.delete_user(current_user.id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return None
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete user: {str(e)}"
            ) 