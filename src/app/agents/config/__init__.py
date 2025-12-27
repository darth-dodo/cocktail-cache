"""Agent configuration loader.

Loads agent and LLM configurations from YAML files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_agents_config() -> dict[str, Any]:
    """Load agent configurations from YAML.

    Returns:
        Dictionary of agent configurations keyed by agent name.
    """
    config_path = CONFIG_DIR / "agents.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_llm_config() -> dict[str, Any]:
    """Load LLM configurations from YAML.

    Returns:
        Dictionary of LLM configurations keyed by profile name.
    """
    config_path = CONFIG_DIR / "llm.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_agent_config(agent_name: str) -> dict[str, Any]:
    """Get configuration for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'drink_recommender', 'bottle_advisor')

    Returns:
        Agent configuration dictionary with role, goal, backstory, etc.

    Raises:
        KeyError: If agent_name is not found in configuration.
    """
    configs = load_agents_config()
    if agent_name not in configs:
        raise KeyError(
            f"Unknown agent: {agent_name}. Available: {list(configs.keys())}"
        )
    return configs[agent_name]


def get_llm_profile(profile: str = "default") -> dict[str, Any]:
    """Get LLM configuration for a specific profile.

    Args:
        profile: Name of the LLM profile (e.g., 'default', 'fast', 'creative')

    Returns:
        LLM configuration dictionary with model, max_tokens, temperature.

    Raises:
        KeyError: If profile is not found in configuration.
    """
    configs = load_llm_config()
    if profile not in configs:
        raise KeyError(
            f"Unknown LLM profile: {profile}. Available: {list(configs.keys())}"
        )
    return configs[profile]


__all__ = [
    "load_agents_config",
    "load_llm_config",
    "get_agent_config",
    "get_llm_profile",
]
