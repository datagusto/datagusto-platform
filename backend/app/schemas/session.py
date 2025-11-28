"""
Session Pydantic schemas for request/response validation.

This module defines all Pydantic models for Session and SessionAlignmentHistory
API operations, following the existing architecture patterns.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ===== Session Schemas =====


class SessionBase(BaseModel):
    """Base Session schema with common fields."""

    pass  # No shared fields between create/update


class SessionCreate(SessionBase):
    """
    Schema for creating a new session.

    Example:
        >>> session_data = SessionCreate(agent_id=agent_id)

    Note:
        - project_id and organization_id will be derived from agent
        - created_by will be set from authenticated user
        - status defaults to 'active'
    """

    agent_id: UUID = Field(..., description="Agent this session belongs to")


class SessionUpdate(BaseModel):
    """
    Schema for updating an existing session.

    All fields are optional for partial updates.

    Example:
        >>> update_data = SessionUpdate(status="completed")
    """

    status: str | None = Field(
        None, description="Session status (active, completed, expired)"
    )


class SessionResponse(BaseModel):
    """
    Schema for session response data.

    Attributes:
        id: Session UUID
        agent_id: Agent this session belongs to
        project_id: Project (denormalized from agent)
        organization_id: Organization (denormalized from agent)
        status: Session lifecycle status
        created_by: User who created the session
        created_at: Creation timestamp
        updated_at: Last update timestamp
        alignment_history_count: Number of alignment records (computed)
    """

    id: UUID
    agent_id: UUID
    project_id: UUID
    organization_id: UUID
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    alignment_history_count: int = Field(
        default=0, description="Number of alignment records (computed)"
    )

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """
    Schema for paginated session list response.

    Attributes:
        items: List of sessions
        total: Total number of sessions
        page: Current page number
        page_size: Number of items per page
    """

    items: list[SessionResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ===== SessionAlignmentHistory Schemas =====


class SessionAlignmentHistoryBase(BaseModel):
    """Base SessionAlignmentHistory schema with common fields."""

    user_instruction: str = Field(
        ..., min_length=1, description="User instruction for alignment"
    )
    past_instructions_history: str | None = Field(
        None, description="Past instructions history for context"
    )
    previous_extraction_output: str | None = Field(
        None, description="Previous extraction output for iteration"
    )


class SessionAlignmentHistoryCreate(SessionAlignmentHistoryBase):
    """
    Schema for creating a new alignment history record.

    Example:
        >>> alignment_data = SessionAlignmentHistoryCreate(
        ...     session_id=session_id,
        ...     user_instruction="Process orders efficiently",
        ...     past_instructions_history="Previous context...",
        ...     previous_extraction_output='{"key_terms": [...]}',
        ...     alignment_result={
        ...         "key_terms": [...],
        ...         "tool_invocation_rules": [...]
        ...     }
        ... )

    Note:
        - agent_id will be derived from session
        - created_by will be set from authenticated user
    """

    session_id: UUID = Field(..., description="Session this alignment belongs to")
    alignment_result: dict[str, Any] = Field(
        ..., description="Alignment result data (JSONB)"
    )


class SessionAlignmentHistoryResponse(SessionAlignmentHistoryBase):
    """
    Schema for alignment history response data.

    Attributes:
        id: Alignment history UUID
        session_id: Session this alignment belongs to
        agent_id: Agent (denormalized)
        user_instruction: Alignment target instruction
        past_instructions_history: Past instructions history for context
        previous_extraction_output: Previous extraction output for iteration
        alignment_result: JSONB data containing alignment details
        created_by: User who performed the alignment
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    session_id: UUID
    agent_id: UUID
    user_instruction: str
    past_instructions_history: str | None
    previous_extraction_output: str | None
    alignment_result: dict[str, Any] = Field(
        ..., description="Alignment result containing terms, rules, etc."
    )
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionAlignmentHistoryListResponse(BaseModel):
    """Schema for paginated alignment history list response."""

    items: list[SessionAlignmentHistoryResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ===== Dashboard Response Schemas =====


class SessionListItemResponse(BaseModel):
    """
    Dashboard用セッション一覧アイテム.

    フロントエンドの AlignmentSession 型に対応するスキーマ。

    Attributes:
        session_id: セッションUUID
        user_instruction: ユーザー指示テキスト
        ambiguous_terms_count: 曖昧な用語の数
        resolved_terms_count: 解決済み用語の数
        validation_rules_count: バリデーションルールの数
        validation_history_count: バリデーション履歴の数
        has_invalid_validations: 無効なバリデーションがあるかどうか
        created_at: 作成日時
        updated_at: 更新日時
    """

    session_id: str = Field(..., description="Session UUID as string")
    user_instruction: str = Field(default="", description="User instruction text")
    ambiguous_terms_count: int = Field(
        default=0, description="Number of ambiguous terms"
    )
    resolved_terms_count: int = Field(default=0, description="Number of resolved terms")
    validation_rules_count: int = Field(
        default=0, description="Number of validation rules"
    )
    validation_history_count: int = Field(
        default=0, description="Number of validation history entries"
    )
    has_invalid_validations: bool = Field(
        default=False, description="Whether session has invalid validations"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class SessionDashboardListResponse(BaseModel):
    """
    Dashboard用セッション一覧レスポンス.

    フロントエンドの AlignmentSessionListResponse 型に対応。
    """

    sessions: list[SessionListItemResponse] = Field(
        default_factory=list, description="List of sessions"
    )
    total: int = Field(default=0, description="Total number of sessions")


class TermResponse(BaseModel):
    """キーターム（曖昧な用語）."""

    term: str = Field(..., description="Extracted term")
    category: str = Field(..., description="Category (time, location, object, etc.)")


class ResolvedTermResponse(BaseModel):
    """解決済みターム."""

    term: str = Field(..., description="Extracted term")
    category: str = Field(..., description="Category")
    resolved_value: str = Field(..., description="Resolved/interpreted value")
    confidence: str = Field(
        default="LOW", description="Confidence level (HIGH/MEDIUM/LOW)"
    )


class InferenceResultResponse(BaseModel):
    """推論結果."""

    user_instruction: str = Field(default="", description="Original user instruction")
    ambiguous_terms: list[TermResponse] = Field(
        default_factory=list, description="Ambiguous terms requiring clarification"
    )
    resolved_terms: list[ResolvedTermResponse] = Field(
        default_factory=list, description="Resolved terms with interpretations"
    )


class GuardrailConditionResponse(BaseModel):
    """ガードレール条件."""

    field: str = Field(..., description="Field to check (input/output)")
    operator: str = Field(..., description="Operator (llm_judge, etc.)")
    value: str = Field(..., description="Value/prompt for evaluation")


class GuardrailTriggerResponse(BaseModel):
    """ガードレールトリガー."""

    type: str = Field(..., description="Trigger type (on_start/on_end)")
    logic: str = Field(default="and", description="Logic operator (and/or)")
    conditions: list[GuardrailConditionResponse] = Field(
        default_factory=list, description="Trigger conditions"
    )


class GuardrailActionConfigResponse(BaseModel):
    """ガードレールアクション設定."""

    message: str | None = Field(None, description="Message to display")
    allow_proceed: bool | None = Field(
        None, description="Allow proceeding after warning"
    )
    drop_field: str | None = Field(None, description="Field to drop")
    drop_item: dict[str, Any] | None = Field(None, description="Item to drop")


class GuardrailActionResponse(BaseModel):
    """ガードレールアクション."""

    type: str = Field(..., description="Action type (block/warn/modify)")
    priority: int = Field(default=1, description="Execution priority")
    config: GuardrailActionConfigResponse = Field(
        default_factory=GuardrailActionConfigResponse,
        description="Action configuration",
    )


class GuardrailMetadataResponse(BaseModel):
    """ガードレールメタデータ."""

    description: str = Field(default="", description="Human-readable description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    severity: str = Field(default="medium", description="Severity level")


class GuardrailDefinitionResponse(BaseModel):
    """ガードレール定義."""

    version: str = Field(default="1.0", description="Definition version")
    schema_version: str = Field(default="1", description="Schema version")
    trigger: GuardrailTriggerResponse = Field(..., description="Trigger conditions")
    actions: list[GuardrailActionResponse] = Field(
        default_factory=list, description="Actions to execute"
    )
    metadata: GuardrailMetadataResponse | None = Field(
        default=None, description="Metadata"
    )


class ToolInvocationRuleResponse(BaseModel):
    """ツール呼び出しルール."""

    tool_name: str = Field(..., description="Name of the tool")
    condition: str = Field(..., description="Condition for invocation")
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Expected parameter values"
    )
    reasoning: str = Field(default="", description="Reasoning for the rule")
    guardrail_definition: GuardrailDefinitionResponse | None = Field(
        default=None, description="Guardrail definition with trigger and actions"
    )


class ValidationHistoryEntryResponse(BaseModel):
    """Validation history entry response."""

    timestamp: str = Field(..., description="Validation timestamp (ISO 8601)")
    timing: str = Field(..., description="Timing of validation (on_start/on_end)")
    process_name: str = Field(..., description="Process name that was validated")
    process_type: str = Field(
        ..., description="Process type (tool/llm/retrieval/agent)"
    )
    should_proceed: bool = Field(default=True, description="Whether to proceed")
    request_context: dict[str, Any] = Field(
        default_factory=dict, description="Request context with input/output"
    )
    evaluation_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation result with triggered_guardrails and metadata",
    )


class UserInstructionHistoryItem(BaseModel):
    """User instruction history item."""

    user_instruction: str = Field(..., description="User instruction text")
    created_at: str = Field(..., description="Timestamp when instruction was recorded")


class SessionDetailResponse(BaseModel):
    """
    Dashboard用セッション詳細レスポンス.

    フロントエンドの SessionData 型に対応。
    """

    inference_result: InferenceResultResponse = Field(
        ..., description="Inference result with terms"
    )
    validation_rules: list[ToolInvocationRuleResponse] = Field(
        default_factory=list, description="Tool invocation rules"
    )
    validation_history: list[ValidationHistoryEntryResponse] = Field(
        default_factory=list, description="Validation history entries"
    )
    user_instruction_history: list[UserInstructionHistoryItem] = Field(
        default_factory=list, description="History of user instructions in this session"
    )
    disallowed_tools: list[str] = Field(
        default_factory=list, description="Tools that are automatically blocked"
    )
    created_at: str = Field(..., description="Session creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Session last update timestamp (ISO 8601)")


__all__ = [
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    "SessionAlignmentHistoryBase",
    "SessionAlignmentHistoryCreate",
    "SessionAlignmentHistoryResponse",
    "SessionAlignmentHistoryListResponse",
    # Dashboard schemas
    "SessionListItemResponse",
    "SessionDashboardListResponse",
    "TermResponse",
    "ResolvedTermResponse",
    "InferenceResultResponse",
    "ToolInvocationRuleResponse",
    "ValidationHistoryEntryResponse",
    "UserInstructionHistoryItem",
    "SessionDetailResponse",
]
