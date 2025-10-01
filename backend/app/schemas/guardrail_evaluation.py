"""
Guardrail Evaluation Pydantic schemas for request/response validation.

This module defines all Pydantic models for Guardrail Evaluation API operations.
"""

from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessType(str, Enum):
    """
    Type of process being evaluated.

    Values:
        LLM: Large Language Model call
        TOOL: Tool/function calling
        RETRIEVAL: RAG/retrieval operation
        AGENT: Agent-level execution
    """

    LLM = "llm"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    AGENT = "agent"


class Timing(str, Enum):
    """
    When guardrail evaluation occurs.

    Values:
        ON_START: Before process execution
        ON_END: After process execution
    """

    ON_START = "on_start"
    ON_END = "on_end"


class GuardrailEvaluationRequest(BaseModel):
    """
    Request schema for guardrail evaluation API.

    Attributes:
        trace_id: Optional trace ID from external tracing system (e.g., LangFuse)
        process_name: Name of the process being evaluated (required)
        process_type: Type of process (required)
        timing: When to evaluate - on_start or on_end (required)
        context: Evaluation context data containing input/output (required)

    Context structure:
        - Must always contain "input" key with dict value
        - When timing=on_end, should contain "output" key with dict value

    Example:
        >>> request = GuardrailEvaluationRequest(
        ...     trace_id="langfuse_trace_abc123",
        ...     process_name="get_weather_tool",
        ...     process_type=ProcessType.TOOL,
        ...     timing=Timing.ON_START,
        ...     context={
        ...         "input": {
        ...             "query": "東京の天気を教えて",
        ...             "location": "東京"
        ...         }
        ...     }
        ... )

    Note:
        - trace_id is optional and can be used for correlation with external systems
        - process_name helps identify which tool/LLM/process triggered evaluation
        - context.input is always required
        - context.output is required when timing=on_end
    """

    trace_id: Optional[str] = Field(
        None,
        description="Optional trace ID from external tracing system",
        examples=["langfuse_trace_abc123"],
    )
    process_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the process being evaluated",
        examples=["get_weather_tool", "llm_response", "vector_search"],
    )
    process_type: ProcessType = Field(
        ...,
        description="Type of process",
    )
    timing: Timing = Field(
        ...,
        description="When to evaluate - on_start or on_end",
    )
    context: dict[str, Any] = Field(
        ...,
        description="Evaluation context data containing input/output",
        examples=[
            {
                "input": {
                    "query": "東京の天気を教えて",
                    "location": "東京",
                },
                "output": {},
            }
        ],
    )

    @field_validator("context")
    @classmethod
    def validate_context_has_input(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that context has required 'input' key."""
        if "input" not in v:
            raise ValueError("context must contain 'input' key")
        if not isinstance(v["input"], dict):
            raise ValueError("context.input must be a dictionary")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trace_id": "langfuse_trace_abc123",
                    "process_name": "get_weather_tool",
                    "process_type": "tool",
                    "timing": "on_start",
                    "context": {
                        "input": {
                            "query": "東京の天気を教えて",
                            "location": "東京",
                        }
                    },
                },
                {
                    "process_name": "llm_response",
                    "process_type": "llm",
                    "timing": "on_end",
                    "context": {
                        "input": {"messages": [{"role": "user", "content": "Hello"}]},
                        "output": {"content": "Hi there!"},
                    },
                },
            ]
        }
    )


class ActionResult(BaseModel):
    """
    Base action result schema.

    Attributes:
        action_type: Type of action (block, warn, modify)
        priority: Action priority (lower number = higher priority)
        result: Action-specific result data
    """

    action_type: str = Field(..., description="Type of action executed")
    priority: int = Field(..., description="Action priority")
    result: dict[str, Any] = Field(..., description="Action-specific result data")

    model_config = ConfigDict(from_attributes=True)


class BlockActionResult(BaseModel):
    """
    Block action result schema.

    Attributes:
        should_block: Always True for block actions
        message: User-defined block message
        reason: Generated reason based on matched conditions
    """

    should_block: bool = Field(True, description="Always True for block actions")
    message: str = Field(..., description="User-defined block message")
    reason: str = Field(..., description="Reason for blocking")

    model_config = ConfigDict(from_attributes=True)


class WarnActionResult(BaseModel):
    """
    Warn action result schema.

    Attributes:
        warning_message: Warning message to display
        severity: Severity level (low, medium, high, critical)
    """

    warning_message: str = Field(..., description="Warning message")
    severity: str = Field(..., description="Severity level")

    model_config = ConfigDict(from_attributes=True)


class ModifyActionResult(BaseModel):
    """
    Modify action result schema.

    Attributes:
        modified_data: The modified context data
        modification_type: Type of modification (drop_field, drop_item)
        applied_pattern: Description of what was modified
    """

    modified_data: dict[str, Any] = Field(..., description="Modified context data")
    modification_type: str = Field(..., description="Type of modification")
    applied_pattern: str = Field(..., description="Description of modification")

    model_config = ConfigDict(from_attributes=True)


class TriggeredGuardrail(BaseModel):
    """
    Triggered guardrail result schema.

    Attributes:
        guardrail_id: UUID of the guardrail
        guardrail_name: Name of the guardrail
        triggered: Whether the guardrail was triggered
        error: Whether an error occurred during evaluation
        error_message: Error message if error occurred
        matched_conditions: Indices of matched conditions (0-based)
        actions: List of executed actions
    """

    guardrail_id: UUID = Field(..., description="Guardrail UUID")
    guardrail_name: str = Field(..., description="Guardrail name")
    triggered: bool = Field(..., description="Whether guardrail was triggered")
    error: bool = Field(False, description="Whether error occurred")
    error_message: Optional[str] = Field(None, description="Error message if any")
    matched_conditions: list[int] = Field(
        default_factory=list, description="Indices of matched conditions"
    )
    actions: list[ActionResult] = Field(
        default_factory=list, description="Executed actions"
    )

    model_config = ConfigDict(from_attributes=True)


class EvaluationMetadata(BaseModel):
    """
    Evaluation metadata schema.

    Attributes:
        evaluation_time_ms: Time taken to evaluate in milliseconds
        evaluated_guardrails_count: Total number of guardrails evaluated
        triggered_guardrails_count: Number of guardrails triggered
    """

    evaluation_time_ms: int = Field(..., description="Evaluation time in ms")
    evaluated_guardrails_count: int = Field(
        ..., description="Total guardrails evaluated"
    )
    triggered_guardrails_count: int = Field(
        ..., description="Number of triggered guardrails"
    )

    model_config = ConfigDict(from_attributes=True)


class GuardrailEvaluationResponse(BaseModel):
    """
    Response schema for guardrail evaluation API.

    Attributes:
        request_id: Server-generated unique request ID
        triggered_guardrails: List of evaluation results
        should_proceed: Final decision on whether to proceed
        metadata: Evaluation metadata

    Example:
        >>> {
        ...     "request_id": "req_a1b2c3d4e5f6",
        ...     "triggered_guardrails": [
        ...         {
        ...             "guardrail_id": "123e4567-e89b-12d3-a456-426614174000",
        ...             "guardrail_name": "Block sensitive data",
        ...             "triggered": True,
        ...             "error": False,
        ...             "error_message": None,
        ...             "matched_conditions": [0, 2],
        ...             "actions": [
        ...                 {
        ...                     "action_type": "block",
        ...                     "priority": 1,
        ...                     "result": {
        ...                         "should_block": True,
        ...                         "message": "Sensitive data detected",
        ...                         "reason": "Field 'input.query' contains prohibited keyword"
        ...                     }
        ...                 }
        ...             ]
        ...         }
        ...     ],
        ...     "should_proceed": False,
        ...     "metadata": {
        ...         "evaluation_time_ms": 45,
        ...         "evaluated_guardrails_count": 3,
        ...         "triggered_guardrails_count": 1
        ...     }
        ... }

    Note:
        - request_id can be used to query evaluation logs later
        - should_proceed=False means the process should be blocked
        - triggered_guardrails includes both triggered and error cases
        - metadata provides timing and count information
    """

    request_id: str = Field(..., description="Server-generated unique request ID")
    triggered_guardrails: list[TriggeredGuardrail] = Field(
        default_factory=list, description="List of evaluation results"
    )
    should_proceed: bool = Field(..., description="Whether to proceed with process")
    metadata: EvaluationMetadata = Field(..., description="Evaluation metadata")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "request_id": "req_a1b2c3d4e5f6",
                    "triggered_guardrails": [
                        {
                            "guardrail_id": "123e4567-e89b-12d3-a456-426614174000",
                            "guardrail_name": "Block sensitive data",
                            "triggered": True,
                            "error": False,
                            "error_message": None,
                            "matched_conditions": [0, 2],
                            "actions": [
                                {
                                    "action_type": "block",
                                    "priority": 1,
                                    "result": {
                                        "should_block": True,
                                        "message": "Sensitive data detected",
                                        "reason": "Field 'input.query' contains prohibited keyword",
                                    },
                                }
                            ],
                        }
                    ],
                    "should_proceed": False,
                    "metadata": {
                        "evaluation_time_ms": 45,
                        "evaluated_guardrails_count": 3,
                        "triggered_guardrails_count": 1,
                    },
                }
            ]
        },
    )


__all__ = [
    "ProcessType",
    "Timing",
    "GuardrailEvaluationRequest",
    "ActionResult",
    "BlockActionResult",
    "WarnActionResult",
    "ModifyActionResult",
    "TriggeredGuardrail",
    "EvaluationMetadata",
    "GuardrailEvaluationResponse",
]
