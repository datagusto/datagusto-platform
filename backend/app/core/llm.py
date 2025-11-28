from langchain_core.language_models import BaseChatModel

from app.core.config import settings


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
        raise Exception(
            "LLM_PROVIDER environment variable is not set. "
            "Must be one of: openai, anthropic, ollama"
        )

    if provider not in ["openai", "anthropic", "ollama"]:
        raise Exception(
            f"Invalid LLM_PROVIDER: {provider}. "
            "Must be one of: openai, anthropic, ollama"
        )

    if not model:
        raise Exception("LLM_MODEL environment variable is not set")

    # Check provider-specific requirements
    if provider in ["openai", "anthropic"] and not api_key:
        raise Exception(f"LLM_API_KEY is required for provider: {provider}")

    if provider == "ollama" and not endpoint:
        raise Exception(
            "LLM_ENDPOINT is required for provider: ollama "
            "(e.g., http://localhost:11434)"
        )

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "endpoint": endpoint,
    }


def create_llm_client(config_key: str | None = None) -> BaseChatModel:
    """
    Create LLM client based on configuration.
    """
    try:
        config = get_llm_config()
        provider = config["provider"]
        model = config["model"]
        api_key = config["api_key"]
        endpoint = config["endpoint"]
        max_tokens = config.get("max_tokens", 64000)

        if provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model,
                api_key=api_key,
                temperature=0.0,  # Deterministic output
                max_tokens=max_tokens,
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model,
                api_key=api_key,
                temperature=0.0,
                max_tokens=max_tokens,
            )

        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama

            return ChatOllama(
                model=model,
                base_url=endpoint,
                temperature=0.0,
            )

        else:
            raise Exception(f"Unsupported provider: {provider}")

    except ImportError as e:
        raise Exception(
            f"Failed to import LangChain module: {str(e)}. "
            "Make sure required packages are installed."
        )
    except Exception as e:
        raise Exception(f"Failed to create LLM client: {str(e)}")
