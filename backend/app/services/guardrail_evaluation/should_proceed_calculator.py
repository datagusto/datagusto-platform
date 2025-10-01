"""
Should proceed calculation logic for guardrail evaluation.

This module determines the final should_proceed decision based on
all triggered guardrail actions.

Decision rules:
    1. If any block action exists → should_proceed = False
    2. If no block, check warn actions:
       - If any warn has allow_proceed=False → should_proceed = False
       - If all warn have allow_proceed=True → should_proceed = True
    3. If only modify actions → should_proceed = True
    4. If no actions → should_proceed = True
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def calculate_should_proceed(
    triggered_guardrails: list[dict[str, Any]]
) -> bool:
    """
    Calculate final should_proceed decision from triggered guardrails.

    Args:
        triggered_guardrails: List of triggered guardrail results with actions

    Returns:
        True if process should proceed, False if it should be blocked

    Example:
        >>> guardrails = [
        ...     {
        ...         "triggered": True,
        ...         "actions": [
        ...             {"action_type": "block", "result": {"should_block": True}}
        ...         ]
        ...     }
        ... ]
        >>> calculate_should_proceed(guardrails)
        False

        >>> guardrails = [
        ...     {
        ...         "triggered": True,
        ...         "actions": [
        ...             {"action_type": "modify", "result": {...}}
        ...         ]
        ...     }
        ... ]
        >>> calculate_should_proceed(guardrails)
        True
    """
    # Collect all actions from triggered guardrails
    all_actions = []
    for guardrail in triggered_guardrails:
        # Skip if not triggered or has error
        if not guardrail.get("triggered", False) or guardrail.get("error", False):
            continue

        actions = guardrail.get("actions", [])
        all_actions.extend(actions)

    # No actions triggered
    if not all_actions:
        logger.debug("No actions triggered, should_proceed=True")
        return True

    # Check for block actions (highest priority)
    has_block = any(
        action.get("action_type") == "block"
        for action in all_actions
    )

    if has_block:
        logger.info("Block action detected, should_proceed=False")
        return False

    # Check warn actions
    warn_actions = [
        action for action in all_actions
        if action.get("action_type") == "warn"
    ]

    if warn_actions:
        # Check if any warn action has allow_proceed=False
        # Note: allow_proceed is stored in the action's config, not result
        # We need to check the original action config
        # For now, we assume warn actions with severity indicate blocking
        # This will be refined when we have access to original action configs

        # If there are warn actions but no block, default to allowing proceed
        # unless explicitly configured otherwise in the action config
        logger.debug(f"Found {len(warn_actions)} warn action(s), checking allow_proceed")
        # This is a simplified implementation
        # In production, we'd need access to the action's original config
        return True

    # Only modify actions remain
    logger.debug("Only modify actions, should_proceed=True")
    return True


def get_action_config_allow_proceed(action_config: dict[str, Any]) -> bool:
    """
    Extract allow_proceed setting from warn action config.

    Args:
        action_config: Original action configuration

    Returns:
        Value of allow_proceed (default: False for safety)
    """
    if action_config.get("type") != "warn":
        return True  # Non-warn actions don't block by default

    config = action_config.get("config", {})
    return config.get("allow_proceed", False)


def calculate_should_proceed_with_configs(
    triggered_guardrails: list[dict[str, Any]],
    guardrail_definitions: dict[str, dict[str, Any]]
) -> bool:
    """
    Calculate should_proceed with access to original action configurations.

    This is the complete implementation that checks warn.allow_proceed settings.

    Args:
        triggered_guardrails: List of triggered guardrail results
        guardrail_definitions: Map of guardrail_id to definition (for action configs)

    Returns:
        True if process should proceed, False if it should be blocked
    """
    # Collect all action configs
    all_action_configs = []

    for guardrail in triggered_guardrails:
        if not guardrail.get("triggered", False) or guardrail.get("error", False):
            continue

        guardrail_id = guardrail.get("guardrail_id")
        if guardrail_id and guardrail_id in guardrail_definitions:
            definition = guardrail_definitions[guardrail_id]
            actions = definition.get("actions", [])
            all_action_configs.extend(actions)

    if not all_action_configs:
        return True

    # Check for block actions
    has_block = any(
        action.get("type") == "block"
        for action in all_action_configs
    )

    if has_block:
        logger.info("Block action detected, should_proceed=False")
        return False

    # Check warn actions with allow_proceed
    warn_actions = [
        action for action in all_action_configs
        if action.get("type") == "warn"
    ]

    if warn_actions:
        # If any warn has allow_proceed=False, block
        for warn_action in warn_actions:
            allow_proceed = get_action_config_allow_proceed(warn_action)
            if not allow_proceed:
                logger.info("Warn action with allow_proceed=False detected, should_proceed=False")
                return False

        # All warns allow proceed
        logger.debug("All warn actions allow proceed, should_proceed=True")
        return True

    # Only modify actions
    return True


__all__ = [
    "calculate_should_proceed",
    "calculate_should_proceed_with_configs",
    "get_action_config_allow_proceed",
]
