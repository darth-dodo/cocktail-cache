"""LLM configuration for CrewAI agents.

This module provides centralized LLM configuration for all agents,
using Claude Haiku from Anthropic as the default model.
"""

from crewai import LLM

# Default LLM configuration using Claude Haiku
# Claude Haiku is fast and cost-effective for agent tasks
DEFAULT_MODEL = "anthropic/claude-3-5-haiku-20241022"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7


def get_default_llm() -> LLM:
    """Get the default LLM configuration for agents.

    Returns:
        A configured LLM instance using Claude Haiku.
    """
    return LLM(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
    )


def get_llm(
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLM:
    """Get a customized LLM configuration.

    Args:
        model: The model identifier (e.g., "anthropic/claude-3-5-haiku-20241022").
               Defaults to Claude Haiku.
        max_tokens: Maximum tokens for the response. Required for Anthropic models.
        temperature: Sampling temperature (0.0-1.0). Higher = more creative.

    Returns:
        A configured LLM instance.
    """
    return LLM(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        temperature=temperature or DEFAULT_TEMPERATURE,
    )
