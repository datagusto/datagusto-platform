from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.agent import Agent, AgentCreate, AgentUpdate, AgentWithApiKey, ApiKeyResponse, SafeObservabilityConfig
from app.schemas.trace import Trace
from app.services.agent_service import AgentService
from app.services.trace_service import TraceService

router = APIRouter()


@router.post("", response_model=AgentWithApiKey)
async def create_agent(
    organization_id: str = Query(..., description="Organization ID"),
    agent_in: AgentCreate = ...,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Create new agent.
    """
    agent = await AgentService.create_agent(
        user_id=current_user.id,
        organization_id=organization_id,
        agent_data=agent_in.model_dump(),
        db=db
    )
    
    safe_observability = None
    if agent.observability_config:
        safe_observability = SafeObservabilityConfig(
            platform_type=agent.observability_config.get("platform_type")
        )
    
    return AgentWithApiKey(
        id=str(agent.id),
        organization_id=str(agent.organization_id),
        name=agent.name,
        description=agent.description,
        status=agent.status,
        config=agent.config,
        observability_config=safe_observability,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        api_key=agent.api_key
    )


@router.get("", response_model=List[Agent])
async def get_agents(
    organization_id: str = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get all agents for an organization.
    """
    agents = await AgentService.get_agents(
        user_id=current_user.id,
        organization_id=organization_id,
        db=db
    )
    return agents


@router.get("/{agent_id}", response_model=AgentWithApiKey)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get agent by ID.
    """
    agent = await AgentService.get_agent(
        agent_id=agent_id,
        user_id=current_user.id,
        db=db
    )
    
    # 認証情報を除いた安全なObservabilityConfigを作成
    safe_observability = None
    if agent.observability_config:
        safe_observability = SafeObservabilityConfig(
            platform_type=agent.observability_config.get("platform_type")
        )
    
    return AgentWithApiKey(
        id=str(agent.id),
        organization_id=str(agent.organization_id),
        name=agent.name,
        description=agent.description,
        status=agent.status,
        config=agent.config,
        observability_config=safe_observability,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        api_key=agent.api_key
    )


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    agent_in: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Update agent.
    """
    agent = await AgentService.update_agent(
        agent_id=agent_id,
        user_id=current_user.id,
        agent_data=agent_in.model_dump(exclude_unset=True),
        db=db
    )
    
    # 認証情報を除いた安全なObservabilityConfigを作成
    safe_observability = None
    if agent.observability_config:
        safe_observability = SafeObservabilityConfig(
            platform_type=agent.observability_config.get("platform_type")
        )
    
    return Agent(
        id=str(agent.id),
        organization_id=str(agent.organization_id),
        name=agent.name,
        description=agent.description,
        status=agent.status,
        config=agent.config,
        observability_config=safe_observability,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> None:
    """
    Delete agent.
    """
    await AgentService.delete_agent(
        agent_id=agent_id,
        user_id=current_user.id,
        db=db
    )


@router.post("/{agent_id}/regenerate-api-key", response_model=ApiKeyResponse)
async def regenerate_api_key(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Regenerate API key for agent.
    """
    result = await AgentService.regenerate_api_key(
        agent_id=agent_id,
        user_id=current_user.id,
        db=db
    )
    return result


@router.get("/{agent_id}/traces", response_model=List[Trace])
async def get_agent_traces(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Get all traces for a specific agent.
    """
    traces = await TraceService.get_traces_by_agent(
        agent_id=agent_id,
        user_id=current_user.id,
        db=db
    )
    return traces 


@router.post("/{agent_id}/sync")
async def sync_traces(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> Any:
    """
    Regenerate API key for agent.
    """
    await TraceService.sync_traces(
        agent_id=agent_id,
        user_id=current_user.id,
        db=db
    )
    return {"message": "Traces synced successfully"}