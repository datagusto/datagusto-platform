from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class OrganizationBase(BaseModel):
    name: str
    settings: Optional[Dict[str, Any]] = None
    billing_info: Optional[Dict[str, Any]] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    billing_info: Optional[Dict[str, Any]] = None


class Organization(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 