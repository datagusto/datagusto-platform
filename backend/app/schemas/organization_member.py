from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class OrganizationRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class OrganizationMemberBase(BaseModel):
    role: OrganizationRole = OrganizationRole.MEMBER


class OrganizationMemberCreate(OrganizationMemberBase):
    user_id: UUID
    organization_id: UUID


class OrganizationMemberUpdate(BaseModel):
    role: Optional[OrganizationRole] = None


class OrganizationMember(OrganizationMemberBase):
    id: UUID
    user_id: UUID
    organization_id: UUID
    joined_at: datetime

    class Config:
        from_attributes = True 