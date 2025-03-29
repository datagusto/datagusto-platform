from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class TraceStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class ObservationType(str, Enum):
    LLM = "LLM"
    RETRIEVER = "RETRIEVER"
    TOOL = "TOOL"
    OTHER = "OTHER"


class ObservationBase(BaseModel):
    type: ObservationType
    name: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    observation_metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[UUID] = None
    run_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class ObservationCreate(BaseModel):
    type: ObservationType
    name: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None
    observation_metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[UUID] = None
    run_id: Optional[str] = None
    trace_id: UUID


class Observation(ObservationBase):
    id: UUID
    trace_id: UUID

    class Config:
        from_attributes = True


class TraceBase(BaseModel):
    user_query: str
    trace_metadata: Optional[Dict[str, Any]] = None


class TraceCreate(TraceBase):
    # When using SDK endpoints with API key authentication, this field is not required
    # as the agent_id is determined from the API key
    agent_id: Optional[UUID] = None


class TraceUpdate(BaseModel):
    final_response: Optional[str] = None
    status: Optional[TraceStatus] = None
    completed_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None


class Trace(TraceBase):
    id: UUID
    agent_id: UUID
    final_response: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TraceStatus
    latency_ms: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None

    class Config:
        from_attributes = True


class TraceWithObservations(Trace):
    observations: List[Observation] = Field(default_factory=list) 