"""
User schemas for API request/response validation.

These schemas align with the ultra-fine-grained data model where
user data is separated across multiple tables.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=8, description="User password (min 8 characters)"
    )
    name: str = Field(..., min_length=1, description="User display name")
    organization_name: Optional[str] = Field(
        None, description="Organization name (creates new org if not provided)"
    )


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=1, description="User display name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")


class UserPasswordChange(BaseModel):
    """Schema for changing user password."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, description="New password (min 8 characters)"
    )


class UserEmailChange(BaseModel):
    """Schema for changing user email."""

    new_email: EmailStr = Field(..., description="New email address")


class UserSuspend(BaseModel):
    """Schema for suspending a user."""

    reason: str = Field(..., description="Reason for suspension")
    suspended_until: Optional[datetime] = Field(
        None, description="Suspension end date (permanent if not provided)"
    )


class UserArchive(BaseModel):
    """Schema for archiving a user."""

    reason: str = Field(..., description="Reason for archiving")


class UserProfile(BaseModel):
    """Schema for user profile data."""

    name: Optional[str] = Field(None, description="User display name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

    class Config:
        from_attributes = True


class User(BaseModel):
    """Schema for user response."""

    id: str = Field(..., description="User UUID")
    email: Optional[str] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    is_active: bool = Field(..., description="Whether user is active")
    is_suspended: bool = Field(..., description="Whether user is suspended")
    is_archived: bool = Field(..., description="Whether user is archived")
    created_at: Optional[str] = Field(None, description="User creation timestamp")

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Schema for list of users."""

    users: list[User] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    limit: int = Field(..., description="Number of users per page")
    offset: int = Field(..., description="Number of users skipped")


class UserAuth(BaseModel):
    """Schema for authentication response."""

    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for JWT token data."""

    sub: str = Field(..., description="User UUID")
    org_id: Optional[str] = Field(None, description="Organization UUID")
    exp: Optional[datetime] = Field(None, description="Token expiration time")


class UserOrganization(BaseModel):
    """Schema for user's organization membership."""

    id: str = Field(..., description="Organization UUID")
    name: str = Field(..., description="Organization name")
    role: str = Field(..., description="User's role (owner, admin, member)")
    joined_at: Optional[str] = Field(None, description="When user joined")

    class Config:
        from_attributes = True


class UserOrganizationList(BaseModel):
    """Schema for list of user's organizations."""

    organizations: list[UserOrganization] = Field(
        ..., description="Organizations user belongs to"
    )
