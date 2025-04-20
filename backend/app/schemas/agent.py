from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from uuid import UUID


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class LangfuseAuth(BaseModel):
    public_key: str
    secret_key: str
    server: str


class ObservabilityConfig(BaseModel):
    platform_type: Literal["langfuse", "langsmith"]
    auth: Dict[str, Any]


class SafeObservabilityConfig(BaseModel):
    platform_type: Literal["langfuse", "langsmith"]


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    observability_config: Optional[ObservabilityConfig] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    config: Optional[Dict[str, Any]] = None
    observability_config: Optional[ObservabilityConfig] = None


class AgentResponseBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    observability_config: Optional[SafeObservabilityConfig] = None


class Agent(AgentResponseBase):
    id: UUID
    organization_id: UUID
    status: AgentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentWithApiKey(Agent):
    api_key: str


class ApiKeyResponse(BaseModel):
    api_key: str 