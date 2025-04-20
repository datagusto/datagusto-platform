from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.core.database import get_db
from app.core.auth import get_agent_from_api_key
from app.models.agent import Agent as AgentModel
from app.models.observation import Observation as ObservationModel
from app.schemas.trace import (
    Trace, TraceCreate, TraceUpdate, 
    Observation, ObservationCreate
)
from app.services.trace_service import TraceService
from app.repositories.trace_repository import TraceRepository

router = APIRouter()


@router.post("/traces", response_model=Dict[str, str])
async def create_trace_from_sdk(
    trace_in: TraceCreate,
    agent: AgentModel = Depends(get_agent_from_api_key),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new trace from the SDK.
    
    The agent_id is automatically determined from the API key authentication,
    so it does not need to be included in the request body.
    """
    try:
        # Create trace using the agent's creator as the user
        trace = await TraceService.create_trace(
            agent_id=str(agent.id),
            user_id=agent.creator_id,
            trace_data=trace_in.model_dump(exclude={"agent_id"}),
            db=db
        )
        return {"trace_id": str(trace.id)}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trace: {str(e)}"
        )


@router.post("/observations", response_model=Dict[str, str])
async def add_observation_from_sdk(
    observation_in: ObservationCreate,
    agent: AgentModel = Depends(get_agent_from_api_key),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add an observation to a trace from the SDK.
    
    Parameters:
        observation_in: The observation data including the trace_id
    """
    try:
        # Check if parent_id exists in the database if it's provided
        if observation_in.parent_id is not None:
            # Check if the parent observation exists
            # parent_observation = db.query(ObservationModel).filter(
            #     ObservationModel.id == observation_in.parent_id
            # ).first()
            
            # if not parent_observation:
            #     raise HTTPException(
            #         status_code=status.HTTP_404_NOT_FOUND,
            #         detail=f"Parent observation with id {observation_in.parent_id} not found"
            #     )
            
            # FIXME
            observation_in.parent_id = None
        if observation_in.run_id is not None:
            obs = db.query(ObservationModel).filter(ObservationModel.trace_id == observation_in.trace_id).filter(ObservationModel.run_id == observation_in.run_id).first()
            if obs is not None:
                return {"observation_id": str(obs.id)}
        
        # Add observation using the agent's creator as the user
        observation = await TraceService.add_observation(
            trace_id=str(observation_in.trace_id),
            user_id=agent.creator_id,
            observation_data=observation_in.model_dump(exclude={"trace_id"}),
            db=db
        )
        
        # If the observation has parent_id=None, complete the trace
        if observation_in.parent_id is None and "Chain end" in observation_in.name:
            # Update trace to completed status
            await TraceService.update_trace(
                trace_id=str(observation_in.trace_id),
                user_id=agent.creator_id,
                trace_data={"status": "COMPLETED"},
                db=db
            )
        
        return {"observation_id": str(observation.id)}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add observation: {str(e)}"
        )


@router.put("/traces/{trace_id}/complete", response_model=Dict[str, bool])
async def complete_trace_from_sdk(
    trace_id: str,
    trace_update: TraceUpdate,
    agent: AgentModel = Depends(get_agent_from_api_key),
    db: Session = Depends(get_db)
) -> Any:
    """
    Complete a trace from the SDK.
    """
    try:
        # Set status to COMPLETED if not specified
        if trace_update.status is None:
            trace_update_dict = trace_update.model_dump()
            trace_update_dict["status"] = "COMPLETED"
        else:
            trace_update_dict = trace_update.model_dump()
        
        # Update trace using the agent's creator as the user
        await TraceService.update_trace(
            trace_id=trace_id,
            user_id=agent.creator_id,
            trace_data=trace_update_dict,
            db=db
        )
        return {"success": True}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete trace: {str(e)}"
        ) 