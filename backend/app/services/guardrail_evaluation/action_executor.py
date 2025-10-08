"""
Action execution engine for guardrail evaluation.

This module provides functionality to execute guardrail actions when conditions
are triggered. Supports three action types: block, warn, and modify.

Action types:
    - block: Block process execution (should_proceed=False)
    - warn: Issue warning with configurable allow_proceed
    - modify: Modify data (drop_field or drop_item)
"""

import copy
from typing import Any

from app.services.guardrail_evaluation.exceptions import ActionExecutionError
from app.services.guardrail_evaluation.field_resolver import (
    parse_field_path,
    resolve_field_value,
)


def execute_block_action(
    action_config: dict[str, Any],
    context: dict[str, Any],
    matched_conditions: list[int],
    conditions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute block action.

    Args:
        action_config: Action configuration with 'config.message'
        context: Evaluation context (not used for block)
        matched_conditions: Indices of matched conditions
        conditions: List of all conditions (for generating reason)

    Returns:
        Action result dict with should_block, message, reason

    Example:
        >>> config = {"type": "block", "priority": 1, "config": {"message": "Blocked"}}
        >>> result = execute_block_action(config, {}, [0], [{"field": "input.query"}])
        >>> result["result"]["should_block"]
        True
    """
    message = action_config.get("config", {}).get("message", "Process blocked")
    priority = action_config.get("priority", 1)

    # Generate reason from matched conditions
    if matched_conditions and conditions:
        first_matched = matched_conditions[0]
        if first_matched < len(conditions):
            condition = conditions[first_matched]
            field = condition.get("field", "unknown")
            operator = condition.get("operator", "unknown")
            reason = f"Field '{field}' matched condition (operator: {operator})"
        else:
            reason = "Condition matched"
    else:
        reason = "Guardrail triggered"

    return {
        "action_type": "block",
        "priority": priority,
        "result": {
            "should_block": True,
            "message": message,
            "reason": reason,
        },
    }


def execute_warn_action(action_config: dict[str, Any]) -> dict[str, Any]:
    """
    Execute warn action.

    Args:
        action_config: Action configuration with config.message, severity, allow_proceed

    Returns:
        Action result dict with warning_message, severity

    Example:
        >>> config = {
        ...     "type": "warn",
        ...     "priority": 1,
        ...     "config": {
        ...         "message": "Warning",
        ...         "severity": "medium",
        ...         "allow_proceed": False
        ...     }
        ... }
        >>> result = execute_warn_action(config)
        >>> result["result"]["severity"]
        'medium'
    """
    config = action_config.get("config", {})
    message = config.get("message", "Warning")
    severity = config.get("severity", "medium")
    priority = action_config.get("priority", 1)

    return {
        "action_type": "warn",
        "priority": priority,
        "result": {
            "warning_message": message,
            "severity": severity,
        },
    }


def evaluate_modify_condition(value: Any, operator: str, target: Any) -> bool:
    """
    Evaluate condition for modify actions.

    Args:
        value: Value to check
        operator: Condition operator (is_null, is_empty, equals)
        target: Target value (for equals operator)

    Returns:
        True if condition matches

    Raises:
        ActionExecutionError: If operator is not supported
    """
    if operator == "is_null":
        return value is None
    elif operator == "is_empty":
        if isinstance(value, str):
            return value == ""
        elif isinstance(value, list):
            return len(value) == 0
        else:
            return False
    elif operator == "equals":
        return value == target
    else:
        raise ActionExecutionError(f"Unsupported modify condition operator: {operator}")


def execute_modify_drop_field(
    config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Execute modify action with drop_field modification type.

    Removes fields from an object based on condition.

    Args:
        config: Modification config with target, condition
        context: Evaluation context data

    Returns:
        Modified context data

    Raises:
        ActionExecutionError: If modification fails

    Example:
        >>> config = {
        ...     "target": "input.user_data",
        ...     "condition": {"fields": ["email"], "operator": "is_null"}
        ... }
        >>> context = {"input": {"user_data": {"name": "Alice", "email": None}}}
        >>> result = execute_modify_drop_field(config, context)
        >>> "email" in result["input"]["user_data"]
        False
    """
    target_path = config.get("target")
    condition = config.get("condition", {})
    fields = condition.get("fields", [])
    operator = condition.get("operator", "is_null")
    target_value = condition.get("value")

    if not target_path:
        raise ActionExecutionError("Modify action missing 'target' path")

    # Resolve target object (validation only)
    try:
        _ = resolve_field_value(context, target_path)
    except Exception as e:
        raise ActionExecutionError(
            f"Failed to resolve target path '{target_path}': {str(e)}"
        )

    # Create deep copy for modification
    modified_context = copy.deepcopy(context)

    # Get the parent object to modify
    segments = parse_field_path(target_path)
    current = modified_context
    for segment in segments[:-1]:
        if isinstance(segment, str):
            current = current[segment]
        else:
            current = current[segment]

    last_segment = segments[-1]
    if isinstance(last_segment, str):
        target_to_modify = current[last_segment]
    else:
        target_to_modify = current[last_segment]

    # Handle dictionary
    if isinstance(target_to_modify, dict):
        fields_to_drop = []

        # Determine which fields to check
        if "*" in fields:
            check_fields = list(target_to_modify.keys())
        else:
            check_fields = fields

        # Check each field
        for field in check_fields:
            if field in target_to_modify:
                field_value = target_to_modify[field]
                if evaluate_modify_condition(field_value, operator, target_value):
                    fields_to_drop.append(field)

        # Drop matching fields
        for field in fields_to_drop:
            del target_to_modify[field]

        applied_pattern = f"{len(fields_to_drop)} field(s) dropped ({operator})"

    # Handle array of dictionaries
    elif isinstance(target_to_modify, list):
        total_dropped = 0
        for item in target_to_modify:
            if isinstance(item, dict):
                fields_to_drop = []

                if "*" in fields:
                    check_fields = list(item.keys())
                else:
                    check_fields = fields

                for field in check_fields:
                    if field in item:
                        field_value = item[field]
                        if evaluate_modify_condition(
                            field_value, operator, target_value
                        ):
                            fields_to_drop.append(field)

                for field in fields_to_drop:
                    del item[field]
                    total_dropped += 1

        applied_pattern = (
            f"{total_dropped} field(s) dropped from array items ({operator})"
        )

    else:
        raise ActionExecutionError(
            f"Target must be dict or list, got {type(target_to_modify).__name__}"
        )

    return {
        "modified_context": modified_context,
        "applied_pattern": applied_pattern,
    }


def execute_modify_drop_item(
    config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Execute modify action with drop_item modification type.

    Removes items from an array based on condition.

    Args:
        config: Modification config with target, condition
        context: Evaluation context data

    Returns:
        Modified context data

    Raises:
        ActionExecutionError: If modification fails

    Example:
        >>> config = {
        ...     "target": "input.items",
        ...     "condition": {"fields": ["status"], "operator": "equals", "value": "deleted"}
        ... }
        >>> context = {"input": {"items": [{"id": 1, "status": "active"}, {"id": 2, "status": "deleted"}]}}
        >>> result = execute_modify_drop_item(config, context)
        >>> len(result["input"]["items"])
        1
    """
    target_path = config.get("target")
    condition = config.get("condition", {})
    fields = condition.get("fields", [])
    operator = condition.get("operator", "is_null")
    target_value = condition.get("value")

    if not target_path:
        raise ActionExecutionError("Modify action missing 'target' path")

    # Resolve target array
    try:
        target_array = resolve_field_value(context, target_path)
    except Exception as e:
        raise ActionExecutionError(
            f"Failed to resolve target path '{target_path}': {str(e)}"
        )

    if not isinstance(target_array, list):
        raise ActionExecutionError(
            f"Target must be a list for drop_item, got {type(target_array).__name__}"
        )

    # Create deep copy for modification
    modified_context = copy.deepcopy(context)

    # Get the parent to modify
    segments = parse_field_path(target_path)
    current = modified_context
    for segment in segments[:-1]:
        if isinstance(segment, str):
            current = current[segment]
        else:
            current = current[segment]

    last_segment = segments[-1]
    if isinstance(last_segment, str):
        array_to_modify = current[last_segment]
    else:
        array_to_modify = current[last_segment]

    # Filter items
    items_to_keep = []
    dropped_count = 0

    for item in array_to_modify:
        should_drop = False

        if isinstance(item, dict):
            # Determine which fields to check
            if "*" in fields:
                check_fields = list(item.keys())
            else:
                check_fields = fields

            # Check if any field matches condition
            for field in check_fields:
                if field in item:
                    field_value = item[field]
                    if evaluate_modify_condition(field_value, operator, target_value):
                        should_drop = True
                        break

        if not should_drop:
            items_to_keep.append(item)
        else:
            dropped_count += 1

    # Update array
    if isinstance(last_segment, str):
        current[last_segment] = items_to_keep
    else:
        current[last_segment] = items_to_keep

    applied_pattern = f"{dropped_count} item(s) dropped from array ({operator})"

    return {
        "modified_context": modified_context,
        "applied_pattern": applied_pattern,
    }


def execute_modify_action(
    action_config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Execute modify action.

    Args:
        action_config: Action configuration with modification_type and config
        context: Evaluation context data

    Returns:
        Action result dict with modified_data, modification_type, applied_pattern

    Raises:
        ActionExecutionError: If modification fails
    """
    config = action_config.get("config", {})
    modification_type = config.get("modification_type")
    priority = action_config.get("priority", 1)

    if modification_type == "drop_field":
        result = execute_modify_drop_field(config, context)
    elif modification_type == "drop_item":
        result = execute_modify_drop_item(config, context)
    else:
        raise ActionExecutionError(
            f"Unsupported modification_type: {modification_type}"
        )

    return {
        "action_type": "modify",
        "priority": priority,
        "result": {
            "modified_data": result["modified_context"],
            "modification_type": modification_type,
            "applied_pattern": result["applied_pattern"],
        },
    }


def apply_multiple_modify_actions(
    modify_actions: list[dict[str, Any]], context: dict[str, Any]
) -> dict[str, Any]:
    """
    Apply multiple modify actions in sequence.

    Actions are applied in the order they appear in the list.
    Each action's output becomes the input for the next action.

    Args:
        modify_actions: List of modify action results
        context: Initial context data

    Returns:
        Final modified context after all modifications

    Example:
        >>> actions = [action1_result, action2_result]
        >>> final_context = apply_multiple_modify_actions(actions, context)
    """
    current_context = context

    for action in modify_actions:
        if action.get("action_type") == "modify":
            result = action.get("result", {})
            modified_data = result.get("modified_data")
            if modified_data:
                current_context = modified_data

    return current_context


__all__ = [
    "execute_block_action",
    "execute_warn_action",
    "execute_modify_action",
    "execute_modify_drop_field",
    "execute_modify_drop_item",
    "apply_multiple_modify_actions",
]
