"""
Condition evaluation engine for guardrail evaluation.

This module provides functionality to evaluate guardrail conditions against
context data. Supports multiple operators including string comparison, numeric
comparison, size comparison, and LLM-based judgment.

Supported operators:
    String: contains, equals, regex
    Numeric: gt, lt, gte, lte
    Size: size_gt, size_lt, size_gte, size_lte
    LLM: llm_judge (implemented in separate module)
"""

import re
from enum import Enum
from typing import Any

from app.services.guardrail_evaluation.exceptions import ConditionEvaluationError
from app.services.guardrail_evaluation.field_resolver import resolve_field_value


class Operator(str, Enum):
    """Supported condition operators."""

    # String operators
    CONTAINS = "contains"
    EQUALS = "equals"
    REGEX = "regex"

    # Numeric operators
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"

    # Size operators
    SIZE_GT = "size_gt"
    SIZE_LT = "size_lt"
    SIZE_GTE = "size_gte"
    SIZE_LTE = "size_lte"

    # LLM operator
    LLM_JUDGE = "llm_judge"


# String comparison operators


def evaluate_contains(field_value: Any, target: str) -> bool:
    """
    Check if field_value contains target substring.

    Args:
        field_value: Value to check (converted to string)
        target: Substring to find

    Returns:
        True if target is found in field_value

    Raises:
        ConditionEvaluationError: If values cannot be compared
    """
    try:
        field_str = str(field_value)
        target_str = str(target)
        return target_str in field_str
    except Exception as e:
        raise ConditionEvaluationError(f"Failed to evaluate 'contains': {str(e)}")


def evaluate_equals(field_value: Any, target: Any) -> bool:
    """
    Check if field_value equals target (exact match).

    Args:
        field_value: Value to compare
        target: Value to compare against

    Returns:
        True if values are equal
    """
    return field_value == target


def evaluate_regex(field_value: Any, pattern: str) -> bool:
    """
    Check if field_value matches regex pattern.

    Args:
        field_value: Value to check (converted to string)
        pattern: Regular expression pattern

    Returns:
        True if pattern matches

    Raises:
        ConditionEvaluationError: If regex is invalid or comparison fails
    """
    try:
        field_str = str(field_value)
        compiled_pattern = re.compile(pattern)
        return compiled_pattern.search(field_str) is not None
    except re.error as e:
        raise ConditionEvaluationError(f"Invalid regex pattern '{pattern}': {str(e)}")
    except Exception as e:
        raise ConditionEvaluationError(f"Failed to evaluate regex: {str(e)}")


# Numeric comparison operators


def _to_number(value: Any) -> float | int:
    """Convert value to number, raising error if not possible."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            # Try int first, then float
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            raise ConditionEvaluationError(f"Cannot convert '{value}' to number")
    raise ConditionEvaluationError(
        f"Cannot convert type {type(value).__name__} to number"
    )


def evaluate_gt(field_value: Any, target: Any) -> bool:
    """Greater than comparison."""
    field_num = _to_number(field_value)
    target_num = _to_number(target)
    return field_num > target_num


def evaluate_lt(field_value: Any, target: Any) -> bool:
    """Less than comparison."""
    field_num = _to_number(field_value)
    target_num = _to_number(target)
    return field_num < target_num


def evaluate_gte(field_value: Any, target: Any) -> bool:
    """Greater than or equal comparison."""
    field_num = _to_number(field_value)
    target_num = _to_number(target)
    return field_num >= target_num


def evaluate_lte(field_value: Any, target: Any) -> bool:
    """Less than or equal comparison."""
    field_num = _to_number(field_value)
    target_num = _to_number(target)
    return field_num <= target_num


# Size comparison operators


def _get_size(value: Any) -> int:
    """Get size/length of value."""
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return len(value)
    raise ConditionEvaluationError(
        f"Cannot get size of type {type(value).__name__} (must be string or list)"
    )


def evaluate_size_gt(field_value: Any, target: int) -> bool:
    """Size greater than comparison."""
    size = _get_size(field_value)
    target_num = _to_number(target)
    return size > target_num


def evaluate_size_lt(field_value: Any, target: int) -> bool:
    """Size less than comparison."""
    size = _get_size(field_value)
    target_num = _to_number(target)
    return size < target_num


def evaluate_size_gte(field_value: Any, target: int) -> bool:
    """Size greater than or equal comparison."""
    size = _get_size(field_value)
    target_num = _to_number(target)
    return size >= target_num


def evaluate_size_lte(field_value: Any, target: int) -> bool:
    """Size less than or equal comparison."""
    size = _get_size(field_value)
    target_num = _to_number(target)
    return size <= target_num


# Main evaluation functions


OPERATOR_MAP = {
    Operator.CONTAINS: evaluate_contains,
    Operator.EQUALS: evaluate_equals,
    Operator.REGEX: evaluate_regex,
    Operator.GT: evaluate_gt,
    Operator.LT: evaluate_lt,
    Operator.GTE: evaluate_gte,
    Operator.LTE: evaluate_lte,
    Operator.SIZE_GT: evaluate_size_gt,
    Operator.SIZE_LT: evaluate_size_lt,
    Operator.SIZE_GTE: evaluate_size_gte,
    Operator.SIZE_LTE: evaluate_size_lte,
}


def evaluate_condition(context: dict[str, Any], condition: dict[str, Any]) -> bool:
    """
    Evaluate single condition against context.

    Args:
        context: Evaluation context data
        condition: Condition dict with 'field', 'operator', 'value' keys

    Returns:
        True if condition matches, False otherwise

    Raises:
        ConditionEvaluationError: If evaluation fails
        FieldPathResolutionError: If field path cannot be resolved

    Example:
        >>> context = {"input": {"query": "hello world"}}
        >>> condition = {"field": "input.query", "operator": "contains", "value": "world"}
        >>> evaluate_condition(context, condition)
        True
    """
    try:
        field_path = condition.get("field")
        operator = condition.get("operator")
        target_value = condition.get("value")

        if not field_path:
            raise ConditionEvaluationError("Condition missing 'field'")
        if not operator:
            raise ConditionEvaluationError("Condition missing 'operator'")

        # Resolve field value from context
        field_value = resolve_field_value(context, field_path)

        # Handle null/None values
        if field_value is None:
            # Only equals can meaningfully compare with None
            if operator == Operator.EQUALS:
                return target_value is None
            # For other operators, None is treated as error condition
            raise ConditionEvaluationError(
                f"Field '{field_path}' is None, cannot evaluate with operator '{operator}'"
            )

        # LLM judge is handled separately
        if operator == Operator.LLM_JUDGE:
            raise ConditionEvaluationError(
                "LLM judge operator must be handled by llm_judge module"
            )

        # Get evaluation function for operator
        eval_func = OPERATOR_MAP.get(operator)
        if not eval_func:
            raise ConditionEvaluationError(f"Unsupported operator: {operator}")

        # Evaluate condition
        return eval_func(field_value, target_value)

    except ConditionEvaluationError:
        raise
    except Exception as e:
        raise ConditionEvaluationError(
            f"Unexpected error evaluating condition: {str(e)}"
        )


def evaluate_conditions(
    context: dict[str, Any], conditions: list[dict[str, Any]], logic: str
) -> tuple[bool, list[int]]:
    """
    Evaluate multiple conditions with AND/OR logic.

    Args:
        context: Evaluation context data
        conditions: List of condition dicts
        logic: "and" or "or"

    Returns:
        Tuple of (overall_result, matched_indices)
        - overall_result: True if conditions match based on logic
        - matched_indices: List of 0-based indices of matched conditions

    Raises:
        ConditionEvaluationError: If evaluation fails

    Example:
        >>> context = {"input": {"query": "hello", "count": 5}}
        >>> conditions = [
        ...     {"field": "input.query", "operator": "contains", "value": "hello"},
        ...     {"field": "input.count", "operator": "gt", "value": 3}
        ... ]
        >>> evaluate_conditions(context, conditions, "and")
        (True, [0, 1])
    """
    if not conditions:
        return False, []

    if logic not in ["and", "or"]:
        raise ConditionEvaluationError(
            f"Invalid logic '{logic}': must be 'and' or 'or'"
        )

    matched_indices: list[int] = []
    results: list[bool] = []

    for i, condition in enumerate(conditions):
        try:
            result = evaluate_condition(context, condition)
            results.append(result)
            if result:
                matched_indices.append(i)
        except Exception as e:
            # If condition evaluation fails, treat as False
            # Error will be logged by caller
            results.append(False)
            raise ConditionEvaluationError(
                f"Failed to evaluate condition {i}: {str(e)}"
            )

    # Apply logic
    if logic == "and":
        overall_result = all(results)
    else:  # logic == "or"
        overall_result = any(results)

    return overall_result, matched_indices


__all__ = [
    "Operator",
    "evaluate_condition",
    "evaluate_conditions",
    "evaluate_contains",
    "evaluate_equals",
    "evaluate_regex",
    "evaluate_gt",
    "evaluate_lt",
    "evaluate_gte",
    "evaluate_lte",
    "evaluate_size_gt",
    "evaluate_size_lt",
    "evaluate_size_gte",
    "evaluate_size_lte",
]
