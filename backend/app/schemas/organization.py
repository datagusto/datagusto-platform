from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class Organization(OrganizationBase):
    id: uuid.UUID
    slug: str
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationMemberBase(BaseModel):
    role: str = Field(..., pattern="^(owner|admin|member)$")


class OrganizationMemberCreate(OrganizationMemberBase):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None


class OrganizationMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(owner|admin|member)$")


class OrganizationMember(OrganizationMemberBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithMembers(Organization):
    members: List[OrganizationMember] = []


class UserOrganizationInfo(BaseModel):
    organization: Organization
    membership: OrganizationMember

    class Config:
        from_attributes = True