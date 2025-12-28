"""LLM configuration for CrewAI agents.

This module provides centralized LLM configuration for all agents,
loading settings from config/llm.yaml.
"""

from crewai import LLM

from src.app.agents.config import get_llm_profile


def get_default_llm() -> LLM:
    """Get the default LLM configuration for agents.

    Returns:
        A configured LLM instance using the default profile from llm.yaml.
    """
    config = get_llm_profile("default")
    return LLM(
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )


def get_llm(
    profile: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLM:
    """Get a customized LLM configuration.

    Args:
        profile: Named profile from llm.yaml (e.g., 'fast', 'creative', 'precise').
                 Overrides are applied on top of the profile settings.
        model: Override the model identifier.
        max_tokens: Override maximum tokens for the response.
        temperature: Override sampling temperature (0.0-1.0).

    Returns:
        A configured LLM instance.
    """
    # Start with profile or default config
    config = get_llm_profile(profile or "default")

    # Apply overrides
    return LLM(
        model=model or config.model,
        max_tokens=max_tokens or config.max_tokens,
        temperature=temperature if temperature is not None else config.temperature,
    )
