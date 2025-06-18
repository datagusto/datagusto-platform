from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.sdk_auth import get_project_from_api_key
from app.models import Project, Guardrail, AuditLog
from app.schemas.guardrail import GuardrailSDKResponse
from app.schemas.audit_log import AuditLogCreate, AuditLogResponse

router = APIRouter()


@router.get("/guardrails", response_model=List[GuardrailSDKResponse])
async def get_guardrails_for_sdk(
    project: Project = Depends(get_project_from_api_key),
    db: Session = Depends(get_db)
):
    """Get active guardrail definitions for SDK."""
    
    guardrails = db.query(Guardrail).filter(
        Guardrail.project_id == project.id,
        Guardrail.is_active == True
    ).all()
    
    return [
        GuardrailSDKResponse(
            id=guardrail.id,
            name=guardrail.name,
            trigger_condition=guardrail.trigger_condition,
            check_config=guardrail.check_config,
            action=guardrail.action
        )
        for guardrail in guardrails
    ]


@router.post("/audit/", response_model=AuditLogResponse)
async def create_audit_log(
    audit_data: AuditLogCreate,
    project: Project = Depends(get_project_from_api_key),
    db: Session = Depends(get_db)
):
    """Create audit log entry from SDK."""
    
    # Validate guardrail exists for this project when audit_type is guardrail_execution
    if audit_data.audit_type == "guardrail_execution":
        guardrail_id = audit_data.data.guardrail_id
        guardrail = db.query(Guardrail).filter(
            Guardrail.id == guardrail_id,
            Guardrail.project_id == project.id
        ).first()
        
        if not guardrail:
            raise HTTPException(
                status_code=404,
                detail="Guardrail not found for this project"
            )
        
        # Update guardrail execution statistics
        guardrail.execution_count += 1
        if audit_data.data.execution_result == "success":
            guardrail.applied_count += 1
    
    # Create audit log
    audit_log = AuditLog(
        project_id=project.id,
        audit_type=audit_data.audit_type,
        data=audit_data.data.dict()
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log