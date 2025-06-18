from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ObservationBase(BaseModel):
    """Base schema for Observation with minimal fields."""
    external_id: str
    platform_type: str
    start_time: datetime


class ObservationCreate(ObservationBase):
    """Schema for creating an Observation."""
    trace_id: UUID
    parent_observation_id: Optional[UUID] = None
    raw_data: Dict[str, Any]


class Observation(ObservationBase):
    """Schema for Observation with all fields."""
    id: UUID
    trace_id: UUID
    parent_observation_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    raw_data: Dict[str, Any]
    
    class Config:
        from_attributes = True


class TraceBase(BaseModel):
    """Base schema for Trace with minimal fields."""
    external_id: str
    platform_type: str
    timestamp: datetime


class TraceCreate(TraceBase):
    """Schema for creating a Trace."""
    project_id: UUID
    raw_data: Dict[str, Any]


class TraceUpdate(BaseModel):
    """Schema for updating a Trace."""
    quality_score: Optional[float] = None
    quality_issues: Optional[List[Dict[str, Any]]] = None


class Trace(TraceBase):
    """Schema for Trace with all fields."""
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime
    quality_score: Optional[float] = None
    quality_issues: Optional[List[Dict[str, Any]]] = None
    raw_data: Dict[str, Any]
    
    class Config:
        from_attributes = True


class TraceWithObservations(Trace):
    """Schema for Trace with its observations."""
    observations: List[Observation] = []


class TraceSyncStatus(BaseModel):
    """Schema for trace sync status."""
    project_id: UUID
    total_traces: int
    new_traces: int
    updated_traces: int
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None
    error: Optional[str] = None


class TraceDetail(BaseModel):
    """Rich trace view with parsed platform-specific data."""
    # Core trace info
    id: UUID
    external_id: str
    platform_type: str
    timestamp: datetime
    project_id: UUID
    
    # Parsed data using platform adapters
    name: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    tags: Optional[List[str]] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    end_time: Optional[datetime] = None
    latency_ms: Optional[float] = None
    total_tokens: Optional[float] = None
    total_cost: Optional[float] = None
    
    # Quality analysis
    quality_score: Optional[float] = None
    quality_issues: Optional[List[Dict[str, Any]]] = None
    
    # System info
    created_at: datetime
    last_synced_at: datetime


class ObservationDetail(BaseModel):
    """Rich observation view with parsed platform-specific data."""
    # Core observation info
    id: UUID
    external_id: str
    platform_type: str
    trace_id: UUID
    parent_observation_id: Optional[UUID] = None
    start_time: datetime
    
    # Parsed data using platform adapters
    name: Optional[str] = None
    type: Optional[str] = None
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    usage_metrics: Optional[Dict[str, Any]] = None
    level: Optional[str] = None
    status_message: Optional[str] = None
    
    # System info
    created_at: datetime