from typing import Dict, Any, Optional
from app.core.supabase import supabase


class SupabaseUserRepository:
    """Repository for Supabase user operations."""
    
    @staticmethod
    async def create_user(email: str, password: str) -> Any:
        """
        Create a new user in Supabase.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Created user object
        """
        print(f"Creating user with email: {email} and password: {password}")
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print(f"User created: {response}")
        return response.user
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Dict[str, str]:
        """
        Authenticate a user with Supabase.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication token
        """
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def update_user(user_id: str, data: Dict[str, Any]) -> Any:
        """
        Update a user in Supabase.
        
        Args:
            user_id: User ID
            data: User data to update
            
        Returns:
            Updated user object
        """
        return supabase.auth.admin.update_user_by_id(user_id, data)
    
    @staticmethod
    async def delete_user(user_id: str) -> None:
        """
        Delete a user from Supabase.
        
        Args:
            user_id: User ID
        """
        supabase.auth.admin.delete_user(user_id)
    
    @staticmethod
    async def get_user(token: str) -> Any:
        """
        Get user by JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            User object
        """
        return supabase.auth.get_user(token) 