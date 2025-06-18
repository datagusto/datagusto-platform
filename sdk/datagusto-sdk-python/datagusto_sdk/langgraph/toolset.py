from langchain_core.tools import tool
import requests
import os
from typing import Optional, Any
from datagusto_sdk.langgraph.filter import incomplete_record_filter


def _get_guardrails_from_api(
    api_key: str, api_url: str = "http://localhost:8000"
) -> Optional[dict]:
    """Fetch guardrail definitions from the backend API.

    Args:
        api_key: The API key for authentication
        api_url: The base URL of the API (default: http://localhost:8000)

    Returns:
        Dictionary containing guardrail definitions or None if failed
    """
    try:
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

        response = requests.get(
            f"{api_url}/api/v1/sdk/guardrails", headers=headers, timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch guardrails: HTTP {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Error fetching guardrails from API: {e}")
        return None


def _apply_guardrails(data: list[dict], guardrails: list[dict]) -> list[dict]:
    """Apply guardrail rules to the input data.

    Args:
        data: Input data to be filtered
        guardrails: List of guardrail definitions

    Returns:
        Filtered data after applying guardrail rules
    """

    if not isinstance(data, list):
        return data

    verified_data = data

    for guardrail in guardrails:
        action_type = guardrail.get("action", {}).get("type", None)

        if action_type == "filter_records":
            verified_data = incomplete_record_filter(verified_data)

    return verified_data


@tool(parse_docstring=True)
def datagusto_guardrail(
    prev_tool_func_name: str,
    prev_tool_func_params: dict,
    prev_tool_func_output_body: Any,
    prev_tool_func_output_payload_key: Optional[str] = None,
) -> Any:
    """MANDATORY: Data guardrail function that MUST be called after EVERY single Tool execution.

    ⚠️  CRITICAL REQUIREMENT: This function MUST be invoked immediately after EACH and EVERY
    Tool execution (excluding datagusto_guardrail itself). DO NOT skip this call or batch
    multiple Tool executions before calling this guardrail. Each Tool → datagusto_guardrail
    pattern must be strictly followed: (1) Execute any Tool, (2) IMMEDIATELY call
    datagusto_guardrail with the Tool's name, parameters, and output, (3) Use the filtered
    result from datagusto_guardrail, (4) Repeat for each Tool execution.

    This function serves as a data quality guardrail that controls AI agents behavior
    and ensures data governance policies are enforced. Failure to call this function
    after every Tool execution will result in data governance violations and may cause
    system errors.

    Args:
        prev_tool_func_name (str): The name of the previously executed Tool function.
            This parameter identifies which Tool was executed before this guardrail
            and helps with audit logging and traceability. This is REQUIRED.
        prev_tool_func_params (dict): The input parameters that were passed to the
            previously executed Tool function. Pass the Tool's parameters as a dictionary.
            This parameter is REQUIRED and helps with comprehensive audit logging.
        prev_tool_func_output_body (Any): The output data from the previously executed Tool.
            Pass the Tool's output directly without any modification or processing.
            This parameter is REQUIRED and accepts any data type returned by Tools.
        prev_tool_func_output_payload_key (Optional[str]): Optional field name (key) within
            prev_tool_func_output_body that contains the payload data to be processed by
            subsequent processes. If provided, the guardrail will specifically target the
            data at this field for processing rather than the entire output structure.
            If None, the entire prev_tool_func_output_body is treated as the payload data.

    Returns:
        Any: Processed data with governance policies applied.
            The returned data maintains quality standards as defined by the guardrail rules.
            The output type matches the input data structure when possible.
    """
    # Get API key from environment variable
    api_key = os.getenv("DATAGUSTO_API_KEY")
    if not api_key:
        print(
            "Warning: DATAGUSTO_API_KEY not found in environment variables. Using default behavior."
        )
        return prev_tool_func_output_body

    # Get API URL from environment variable (with default)
    api_url = os.getenv("DATAGUSTO_API_URL", "http://localhost:8000")

    # Fetch guardrail definitions from backend API
    guardrail_config = _get_guardrails_from_api(api_key, api_url)
    if not guardrail_config:
        # Return the original output if the guardrail configuration is not found
        return prev_tool_func_output_body

    # Extract guardrails list from the response
    guardrails = guardrail_config.get("guardrails", [])
    if not guardrails:
        # Return the original output if no guardrails are found
        return prev_tool_func_output_body

    if prev_tool_func_output_payload_key is not None:
        payload = prev_tool_func_output_body[prev_tool_func_output_payload_key]
    else:
        payload = prev_tool_func_output_body

    # Apply guardrail rules to the data
    payload = _apply_guardrails(payload, guardrails)

    if prev_tool_func_output_payload_key is not None:
        prev_tool_func_output_body[prev_tool_func_output_payload_key] = payload
    else:
        prev_tool_func_output_body = payload

    return prev_tool_func_output_body
