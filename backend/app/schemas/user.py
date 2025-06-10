from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: UUID
    is_active: bool
    email_confirmed: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True 