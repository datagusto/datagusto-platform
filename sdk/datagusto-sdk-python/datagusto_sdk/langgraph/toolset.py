from langchain_core.tools import tool
import requests
import os
from typing import Optional
from datagusto_sdk.langgraph.filter import incomplete_record_filter


def _get_guardrails_from_api(
    api_key: str, api_url: str = "http://localhost:8000"
) -> Optional[dict]:
    """
    Fetch guardrail definitions from the backend API.

    Args:
        api_key: The API key for authentication
        api_url: The base URL of the API (default: http://localhost:8000)

    Returns:
        Dictionary containing guardrail definitions or None if failed
    """
    try:
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

        response = requests.get(
            f"{api_url}/api/v1/guardrails/sdk/guardrails", headers=headers, timeout=10
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
    """
    Apply guardrail rules to the input data.

    Args:
        data: Input data to be filtered
        guardrails: List of guardrail definitions

    Returns:
        Filtered data after applying guardrail rules
    """
    filtered_data = data

    for guardrail in guardrails:
        action_type = guardrail.get("action", {}).get("type", None)

        if action_type == "filter_records":
            filtered_data = incomplete_record_filter(filtered_data)

    return filtered_data


@tool(parse_docstring=True)
def datagusto_guardrail(
    prev_tool_func_name: str, prev_tool_output: list[dict]
) -> list[dict]:
    """Data guardrail function that must be called after any Tool execution.

    This function serves as a data quality guardrail that controls AI agents behavior.
    It must be invoked immediately after any Tool execution, excluding datagusto_guardrail,
    to ensure data quality with data governance policies.

    Args:
        prev_tool_func_name (str): The name of the previously executed Tool function.
            This parameter identifies which Tool was executed before this guardrail
            and helps with audit logging and traceability.
        prev_tool_output (list[dict]): The output data from the previously executed
            Tool. Expected to be a list of dictionaries containing customer or
            business data that may include null values requiring filtration.

    Returns:
        list[dict]: Filtered data with all entries containing null values removed.
            The returned list maintains the same dictionary structure as the input
            but excludes any dictionaries that contain None/null values.

    Note:
        This function is mandatory in the data processing pipeline and must be
        called after every Tool execution, excluding datagusto_guardrail, to
        maintain data quality standards.
    """

    # Get API key from environment variable
    api_key = os.getenv("DATAGUSTO_API_KEY")
    if not api_key:
        print(
            "Warning: DATAGUSTO_API_KEY not found in environment variables. Using default behavior."
        )
        return prev_tool_output

    # Get API URL from environment variable (with default)
    api_url = os.getenv("DATAGUSTO_API_URL", "http://localhost:8000")

    # Fetch guardrail definitions from backend API
    guardrail_config = _get_guardrails_from_api(api_key, api_url)
    if not guardrail_config:
        # Return the original output if the guardrail configuration is not found
        return prev_tool_output

    # Extract guardrails list from the response
    guardrails = guardrail_config.get("guardrails", [])
    if not guardrails:
        # Return the original output if no guardrails are found
        return prev_tool_output

    # Apply guardrail rules to the data
    filtered_output = _apply_guardrails(prev_tool_output, guardrails)

    return filtered_output
