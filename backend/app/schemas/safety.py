from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.guardrail_evaluation import ProcessType, Timing


class KeyTerm(BaseModel):
    """Individual key term extracted from user instructions"""

    term: str = Field(description="Extracted key term from user instruction")
    user_provided_context: str | None = Field(
        default=None,
        description="Specific context or concrete information explicitly provided by the user for this term. Must be null if user has not provided specific details.",
    )
    category: Literal[
        "time", "location", "object", "action", "degree", "condition", "reference"
    ] = Field(description="Category of the key term")


class KeyTermsOutput(BaseModel):
    """Output containing all extracted key terms"""

    key_terms: list[KeyTerm] = Field(
        description="List of all extracted key terms from instruction history"
    )


class AlignmentRequest(BaseModel):
    """Schema for aligning a session."""

    session_id: str | None = None
    user_instruction: str


class AlignmentResponse(BaseModel):
    """Schema for aligning a session."""

    session_id: str
    key_terms: list[KeyTerm]


class SessionValidationRequest(BaseModel):
    """
    Request schema for session guardrail validation.

    Combines session_id with guardrail evaluation request parameters.
    Used for validating tool/LLM invocations against session-generated guardrails.

    Attributes:
        session_id: Session ID from POST /sessions/alignment
        trace_id: Optional trace ID from external tracing system
        process_name: Name of the process being evaluated
        process_type: Type of process (llm, tool, retrieval, agent)
        timing: When to evaluate - on_start or on_end
        context: Evaluation context data containing input/output

    Example:
        >>> request = SessionValidationRequest(
        ...     session_id="123e4567-e89b-12d3-a456-426614174000",
        ...     process_name="get_exam_results",
        ...     process_type=ProcessType.TOOL,
        ...     timing=Timing.ON_START,
        ...     context={"input": {"semester": "spring", "year": 2024}}
        ... )
    """

    session_id: str = Field(..., description="Session ID from POST /sessions/alignment")
    trace_id: str | None = Field(
        None, description="Optional trace ID from external tracing system"
    )
    process_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the process being evaluated",
    )
    process_type: ProcessType = Field(
        ..., description="Type of process (llm, tool, retrieval, agent)"
    )
    timing: Timing = Field(..., description="When to evaluate - on_start or on_end")
    context: dict[str, Any] = Field(
        ..., description="Evaluation context data containing input/output"
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
