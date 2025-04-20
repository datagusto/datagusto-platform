from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class TraceStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class ObservationBase(BaseModel):
    type: Optional[str] = None
    parent_observation_id: Optional[UUID] = None
    name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input: Optional[str] = None
    output: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    usage_details: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    cost_details: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    latency: Optional[float] = None
    observability_id: Optional[UUID] = None


class ObservationCreate(BaseModel):
    type: Optional[str] = None
    parent_observation_id: Optional[UUID] = None
    name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input: Optional[str] = None
    output: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    usage_details: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    cost_details: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    latency: Optional[float] = None
    observability_id: Optional[UUID] = None
    trace_id: UUID


class Observation(ObservationBase):
    id: UUID
    trace_id: UUID

    class Config:
        from_attributes = True


class TraceBase(BaseModel):
    trace_metadata: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    observability_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None
    evaluation_results: Optional[Dict[str, Any]] = None


class TraceCreate(TraceBase):
    # When using SDK endpoints with API key authentication, this field is not required
    # as the agent_id is determined from the API key
    agent_id: Optional[UUID] = None


class TraceUpdate(BaseModel):
    output: Optional[Dict[str, Any]] = None
    status: Optional[TraceStatus] = None
    updated_at: Optional[datetime] = None
    latency: Optional[float] = None
    total_cost: Optional[float] = None


class Trace(TraceBase):
    id: UUID
    agent_id: UUID
    status: TraceStatus = TraceStatus.IN_PROGRESS
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    latency: Optional[float] = None
    total_cost: Optional[float] = None

    class Config:
        from_attributes = True


class TraceWithObservations(Trace):
    observations: List[Observation] = Field(default_factory=list)
