from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.trace import (
    Trace, TraceCreate, TraceUpdate, TraceWithObservations,
    Observation, ObservationCreate
)
from app.services.trace_service import TraceService

router = APIRouter()


@router.post("", response_model=Trace)
async def create_trace(
    agent_id: str = Query(..., description="Agent ID"),
    trace_in: TraceCreate = ...,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Create new trace.
    """
    trace = await TraceService.create_trace(
        agent_id=agent_id,
        user_id=current_user.id,
        trace_data=trace_in.model_dump(exclude={"agent_id"}),
        db=db
    )
    return trace


@router.get("", response_model=List[Trace])
async def get_traces(
    agent_id: Optional[str] = Query(None, description="Agent ID, if not provided returns traces from all accessible agents"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get traces for a specific agent or all accessible agents if no agent_id is provided.
    """
    if agent_id:
        traces = await TraceService.get_traces_by_agent(
            agent_id=agent_id,
            user_id=current_user.id,
            db=db
        )
    else:
        traces = await TraceService.get_traces_for_user(
            user_id=current_user.id,
            db=db
        )
    return traces


@router.get("/{trace_id}", response_model=Trace)
async def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get trace by ID.
    """
    trace = await TraceService.get_trace(
        trace_id=trace_id,
        user_id=current_user.id,
        db=db
    )
    return trace


@router.get("/{trace_id}/with-observations", response_model=TraceWithObservations)
async def get_trace_with_observations(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get trace with its observations.
    """
    result = await TraceService.get_trace_with_observations(
        trace_id=trace_id,
        user_id=current_user.id,
        db=db
    )
    # Format as TraceWithObservations
    return TraceWithObservations(
        **{**result["trace"].__dict__, "observations": result["observations"]}
    )


@router.put("/{trace_id}", response_model=Trace)
async def update_trace(
    trace_id: str,
    trace_in: TraceUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Update trace.
    """
    trace = await TraceService.update_trace(
        trace_id=trace_id,
        user_id=current_user.id,
        trace_data=trace_in.model_dump(exclude_unset=True),
        db=db
    )
    return trace


@router.post("/{trace_id}/observations", response_model=Observation)
async def add_observation(
    trace_id: str,
    observation_in: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Add observation to trace.
    """
    observation = await TraceService.add_observation(
        trace_id=trace_id,
        user_id=current_user.id,
        observation_data=observation_in.model_dump(),
        db=db
    )
    return observation


@router.get("/{trace_id}/observations", response_model=List[Observation])
async def get_observations(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get observations for a specific trace.
    """
    result = await TraceService.get_trace_with_observations(
        trace_id=trace_id,
        user_id=current_user.id,
        db=db
    )
    return result["observations"] 