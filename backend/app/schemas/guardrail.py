from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class TriggerCondition(BaseModel):
    type: str  # "always", "specific_tool", "tool_regex"
    tool_name: Optional[str] = None
    tool_regex: Optional[str] = None


class CheckConfig(BaseModel):
    type: str  # "missing_values_any", "missing_values_column", "old_date_records"
    target_column: Optional[str] = None
    date_threshold_days: Optional[int] = 365


class GuardrailAction(BaseModel):
    type: str  # "filter_records", "interrupt_agent"


class GuardrailCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_condition: TriggerCondition
    check_config: CheckConfig
    action: GuardrailAction
    is_active: bool = True


class GuardrailUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_condition: Optional[TriggerCondition] = None
    check_config: Optional[CheckConfig] = None
    action: Optional[GuardrailAction] = None
    is_active: Optional[bool] = None


class GuardrailResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    trigger_condition: TriggerCondition
    check_config: CheckConfig
    action: GuardrailAction
    is_active: bool
    execution_count: int
    applied_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuardrailStatsUpdate(BaseModel):
    guardrail_id: UUID
    executed: bool
    applied: bool


# SDK用の簡略化されたレスポンス
class GuardrailSDKResponse(BaseModel):
    id: UUID
    name: str
    trigger_condition: Dict[str, Any]
    check_config: Dict[str, Any]
    action: Dict[str, Any]