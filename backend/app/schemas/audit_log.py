from pydantic import BaseModel
from typing import Dict, Any, Literal
from datetime import datetime
from uuid import UUID


class GuardrailExecutionData(BaseModel):
    guardrail_id: UUID
    execution_result: Literal["success", "error", "skip"]
    execution_details: Dict[str, Any] = {}


class AuditLogCreate(BaseModel):
    audit_type: Literal["guardrail_execution"]
    data: GuardrailExecutionData


class AuditLogResponse(BaseModel):
    id: UUID
    project_id: UUID
    audit_type: str
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True