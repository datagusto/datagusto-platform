from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_sync
from app.models.user import User
from app.models.project import Project
from app.repositories.guardrail_repository import GuardrailRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.guardrail import (
    GuardrailCreate,
    GuardrailUpdate, 
    GuardrailResponse,
    GuardrailStatsUpdate,
    GuardrailSDKResponse
)

router = APIRouter()


def get_guardrail_repository(db: Session = Depends(get_db)) -> GuardrailRepository:
    return GuardrailRepository(db)


def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)


def verify_project_access(
    project_id: UUID,
    current_user: User,
    project_repo: ProjectRepository
) -> Project:
    """プロジェクトアクセス権限を確認"""
    project = project_repo.get_user_project(current_user.id, project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found or access denied"
        )
    return project


@router.get("/projects/{project_id}/guardrails", response_model=List[GuardrailResponse])
def get_guardrails(
    project_id: UUID,
    current_user: User = Depends(get_current_user_sync),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """プロジェクトのガードレール一覧を取得"""
    verify_project_access(project_id, current_user, project_repo)
    
    guardrails = guardrail_repo.get_by_project_id(project_id)
    return guardrails


@router.post("/projects/{project_id}/guardrails", response_model=GuardrailResponse)
def create_guardrail(
    project_id: UUID,
    guardrail_data: GuardrailCreate,
    current_user: User = Depends(get_current_user_sync),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """ガードレールを作成"""
    verify_project_access(project_id, current_user, project_repo)
    
    guardrail = guardrail_repo.create(project_id, guardrail_data)
    return guardrail


@router.get("/projects/{project_id}/guardrails/{guardrail_id}", response_model=GuardrailResponse)
def get_guardrail(
    project_id: UUID,
    guardrail_id: UUID,
    current_user: User = Depends(get_current_user_sync),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """ガードレール詳細を取得"""
    verify_project_access(project_id, current_user, project_repo)
    
    guardrail = guardrail_repo.get_by_id(guardrail_id)
    if not guardrail or guardrail.project_id != project_id:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    return guardrail


@router.put("/projects/{project_id}/guardrails/{guardrail_id}", response_model=GuardrailResponse)
def update_guardrail(
    project_id: UUID,
    guardrail_id: UUID,
    guardrail_data: GuardrailUpdate,
    current_user: User = Depends(get_current_user_sync),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """ガードレールを更新"""
    verify_project_access(project_id, current_user, project_repo)
    
    # ガードレールの存在とプロジェクト所有権を確認
    existing_guardrail = guardrail_repo.get_by_id(guardrail_id)
    if not existing_guardrail or existing_guardrail.project_id != project_id:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    guardrail = guardrail_repo.update(guardrail_id, guardrail_data)
    if not guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    return guardrail


@router.delete("/projects/{project_id}/guardrails/{guardrail_id}")
def delete_guardrail(
    project_id: UUID,
    guardrail_id: UUID,
    current_user: User = Depends(get_current_user_sync),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    """ガードレールを削除"""
    verify_project_access(project_id, current_user, project_repo)
    
    # ガードレールの存在とプロジェクト所有権を確認
    existing_guardrail = guardrail_repo.get_by_id(guardrail_id)
    if not existing_guardrail or existing_guardrail.project_id != project_id:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    success = guardrail_repo.delete(guardrail_id)
    if not success:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    return {"message": "Guardrail deleted successfully"}


# SDK用エンドポイント
@router.get("/sdk/guardrails")
def get_guardrails_for_sdk(
    api_key: str = Header(..., alias="X-API-Key"),
    project_repo: ProjectRepository = Depends(get_project_repository),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository)
):
    """SDK用ガードレール設定取得"""
    project = project_repo.get_by_api_key(api_key)
    if not project:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    guardrails = guardrail_repo.get_active_by_project_id(project.id)
    
    return {
        "project_id": str(project.id),
        "guardrails": [
            GuardrailSDKResponse(
                id=g.id,
                name=g.name,
                trigger_condition=g.trigger_condition,
                check_config=g.check_config,
                action=g.action
            )
            for g in guardrails
        ]
    }


@router.post("/sdk/guardrails/stats")
def update_guardrail_stats(
    stats: GuardrailStatsUpdate,
    api_key: str = Header(..., alias="X-API-Key"),
    project_repo: ProjectRepository = Depends(get_project_repository),
    guardrail_repo: GuardrailRepository = Depends(get_guardrail_repository)
):
    """SDK用統計更新"""
    project = project_repo.get_by_api_key(api_key)
    if not project:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    guardrail = guardrail_repo.update_execution_stats(
        stats.guardrail_id, 
        stats.executed, 
        stats.applied
    )
    
    if not guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    return {"message": "Stats updated successfully"}