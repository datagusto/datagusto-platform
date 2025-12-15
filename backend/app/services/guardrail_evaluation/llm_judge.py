"""
LLM as a Judge implementation for guardrail evaluation.

This module provides functionality to use LLMs (Large Language Models) for
natural language-based condition evaluation. Uses LangChain for provider abstraction.

Supported providers:
    - OpenAI (gpt-4, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-opus, claude-3-sonnet, etc.)
    - Ollama (local models)

Environment variables required:
    LLM_PROVIDER: "openai" | "anthropic" | "ollama"
    LLM_MODEL: Model name (e.g., "gpt-4", "claude-3-sonnet-20240229")
    LLM_API_KEY: API key (required for openai and anthropic)
    LLM_ENDPOINT: Endpoint URL (required for ollama only)
"""

import logging
from functools import lru_cache
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.services.guardrail_evaluation.exceptions import LLMJudgeError

logger = logging.getLogger(__name__)


def get_llm_config() -> dict[str, str]:
    """
    Get LLM configuration from environment variables.

    Returns:
        Configuration dict with provider, model, api_key, endpoint

    Raises:
        LLMJudgeError: If required configuration is missing

    Example:
        >>> config = get_llm_config()
        >>> config['provider']
        'openai'
    """
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    api_key = settings.LLM_API_KEY
    endpoint = settings.LLM_ENDPOINT

    if not provider:
        raise LLMJudgeError(
            "LLM_PROVIDER environment variable is not set. "
            "Must be one of: openai, anthropic, ollama"
        )

    if provider not in ["openai", "anthropic", "ollama"]:
        raise LLMJudgeError(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Must be one of: openai, anthropic, ollama"
        )

    if not model:
        raise LLMJudgeError("LLM_MODEL environment variable is not set")

    # Check provider-specific requirements
    if provider in ["openai", "anthropic"] and not api_key:
        raise LLMJudgeError(f"LLM_API_KEY is required for provider: {provider}")

    if provider == "ollama" and not endpoint:
        raise LLMJudgeError(
            "LLM_ENDPOINT is required for provider: ollama "
            "(e.g., http://localhost:11434)"
        )

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "endpoint": endpoint,
    }


@lru_cache(maxsize=1)
def create_llm_client(config_key: str | None = None) -> BaseChatModel:
    """
    Create LLM client based on configuration.

    Uses functools.lru_cache to reuse the same client instance.
    The config_key parameter is only used for cache invalidation.

    Args:
        config_key: Optional cache key (defaults to provider:model)

    Returns:
        Configured LLM client instance

    Raises:
        LLMJudgeError: If client creation fails

    Example:
        >>> client = create_llm_client()
        >>> # Subsequent calls return the same instance
        >>> client2 = create_llm_client()
        >>> assert client is client2
    """
    try:
        config = get_llm_config()
        provider = config["provider"]
        model = config["model"]
        api_key = config["api_key"]
        endpoint = config["endpoint"]

        if provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=0.0,  # Deterministic output
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=0.0,
            )

        elif provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model,
                base_url=endpoint,
                temperature=0.0,
            )

        else:
            raise LLMJudgeError(f"Unsupported provider: {provider}")

    except ImportError as e:
        raise LLMJudgeError(
            f"Failed to import LangChain module: {str(e)}. "
            "Make sure required packages are installed."
        )
    except Exception as e:
        raise LLMJudgeError(f"Failed to create LLM client: {str(e)}")


def evaluate_with_llm(field_value: Any, criteria: str, timeout: int = 30) -> bool:
    """
    Evaluate field value using LLM judge.

    Sends field value and criteria to LLM and expects "true" or "false" response.

    Args:
        field_value: The value to judge (converted to string)
        criteria: Natural language criteria for judgment
        timeout: Timeout in seconds (default: 30)

    Returns:
        True if LLM judges the criteria is met, False otherwise

    Raises:
        LLMJudgeError: If LLM call fails or returns invalid response

    Example:
        >>> value = "This is spam content with promotional links"
        >>> criteria = "Is this content spam or promotional?"
        >>> evaluate_with_llm(value, criteria)
        True
    """
    try:
        # Create LLM client
        llm = create_llm_client()

        # Convert field value to string
        field_str = str(field_value)

        # Truncate very long content
        max_length = 2000
        if len(field_str) > max_length:
            field_str = field_str[:max_length] + "... (truncated)"
            logger.warning(
                f"Field value truncated to {max_length} characters for LLM judge"
            )

        # Construct prompt
        system_prompt = (
            "You are a content judge. Answer with only 'true' or 'false' "
            "based on the following criteria. Do not provide explanations."
        )

        user_prompt = f"""Criteria: {criteria}

Content to judge: {field_str}

Answer (true/false):"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Log the request
        logger.info(
            f"LLM judge request - Criteria: {criteria[:100]}..., "
            f"Content length: {len(field_str)}"
        )

        # Call LLM with timeout
        # Note: LangChain timeout is set via model config
        response = llm.invoke(messages, config={"timeout": timeout})

        # Extract response content
        response_text = response.content.strip().lower()

        logger.info(f"LLM judge response: {response_text}")

        # Parse response
        if "true" in response_text:
            return True
        elif "false" in response_text:
            return False
        else:
            raise LLMJudgeError(
                f"LLM returned invalid response: {response_text}. "
                "Expected 'true' or 'false'"
            )

    except LLMJudgeError:
        raise
    except TimeoutError:
        raise LLMJudgeError(f"LLM judge request timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"LLM judge error: {str(e)}")
        raise LLMJudgeError(f"LLM judge failed: {str(e)}")


__all__ = [
    "get_llm_config",
    "create_llm_client",
    "evaluate_with_llm",
]
