"""
Custom exceptions for guardrail evaluation.

This module defines all custom exception types used throughout the
guardrail evaluation engine.
"""


class GuardrailEvaluationError(Exception):
    """Base exception for all guardrail evaluation errors."""

    pass


class FieldPathResolutionError(GuardrailEvaluationError):
    """
    Exception raised when field path resolution fails.

    This occurs when:
    - Path syntax is invalid
    - Field/key doesn't exist in the data
    - Array index is out of range
    - Type mismatch (accessing dict key on array, or vice versa)
    """

    def __init__(self, message: str, path: str, segment: str | int | None = None):
        """
        Initialize field path resolution error.

        Args:
            message: Error description
            path: The full field path that failed
            segment: The specific path segment that caused the error
        """
        self.path = path
        self.segment = segment
        super().__init__(f"{message} (path: {path}, segment: {segment})")


class ConditionEvaluationError(GuardrailEvaluationError):
    """Exception raised when condition evaluation fails."""

    pass


class ActionExecutionError(GuardrailEvaluationError):
    """Exception raised when action execution fails."""

    pass


class LLMJudgeError(GuardrailEvaluationError):
    """Exception raised when LLM judge API call fails."""

    pass


__all__ = [
    "GuardrailEvaluationError",
    "FieldPathResolutionError",
    "ConditionEvaluationError",
    "ActionExecutionError",
    "LLMJudgeError",
]
