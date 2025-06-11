from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    platform_type: str = Field(default="langfuse")
    platform_config: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    organization_id: uuid.UUID


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    platform_type: Optional[str] = None
    platform_config: Optional[Dict[str, Any]] = None


class Project(ProjectBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    api_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectWithoutApiKey(BaseModel):
    """Project schema without sensitive API key for public responses."""
    id: uuid.UUID
    name: str
    description: Optional[str]
    organization_id: uuid.UUID
    platform_type: str
    platform_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberBase(BaseModel):
    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


class ProjectMemberCreate(ProjectMemberBase):
    user_id: uuid.UUID
    project_id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None


class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(owner|admin|member|viewer)$")


class ProjectMember(ProjectMemberBase):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None
    joined_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectWithMembers(ProjectWithoutApiKey):
    members: List[ProjectMember] = []


class UserProjectInfo(BaseModel):
    project: ProjectWithoutApiKey
    membership: ProjectMember

    class Config:
        from_attributes = True


class ApiKeyResponse(BaseModel):
    api_key: str
    message: str = "API key generated successfully"