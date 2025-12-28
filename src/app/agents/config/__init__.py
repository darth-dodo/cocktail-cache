"""Agent configuration loader.

Loads agent, task, and LLM configurations from YAML files and validates
them using Pydantic models.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml

from src.app.models.config import AgentConfig, LLMConfig, TaskConfig

CONFIG_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _load_agents_yaml() -> dict[str, Any]:
    """Load raw agent configurations from YAML.

    Returns:
        Raw dictionary of agent configurations.
    """
    config_path = CONFIG_DIR / "agents.yaml"
    with open(config_path, encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


@lru_cache(maxsize=1)
def _load_llm_yaml() -> dict[str, Any]:
    """Load raw LLM configurations from YAML.

    Returns:
        Raw dictionary of LLM configurations.
    """
    config_path = CONFIG_DIR / "llm.yaml"
    with open(config_path, encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


@lru_cache(maxsize=1)
def _load_tasks_yaml() -> dict[str, Any]:
    """Load raw task configurations from YAML.

    Returns:
        Raw dictionary of task configurations.
    """
    config_path = CONFIG_DIR / "tasks.yaml"
    with open(config_path, encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


def load_agents_config() -> dict[str, AgentConfig]:
    """Load and validate agent configurations from YAML.

    Returns:
        Dictionary of validated AgentConfig instances keyed by agent name.
    """
    raw_configs = _load_agents_yaml()
    return {name: AgentConfig(**config) for name, config in raw_configs.items()}


def load_llm_config() -> dict[str, LLMConfig]:
    """Load and validate LLM configurations from YAML.

    Returns:
        Dictionary of validated LLMConfig instances keyed by profile name.
    """
    raw_configs = _load_llm_yaml()
    return {name: LLMConfig(**config) for name, config in raw_configs.items()}


def load_tasks_config() -> dict[str, TaskConfig]:
    """Load and validate task configurations from YAML.

    Returns:
        Dictionary of validated TaskConfig instances keyed by task name.
        Each task has 'description', 'expected_output', and 'output_model' fields.
    """
    raw_configs = _load_tasks_yaml()
    return {name: TaskConfig(**config) for name, config in raw_configs.items()}


def get_agent_config(agent_name: str) -> AgentConfig:
    """Get validated configuration for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., 'drink_recommender', 'bottle_advisor')

    Returns:
        Validated AgentConfig instance.

    Raises:
        KeyError: If agent_name is not found in configuration.
    """
    raw_configs = _load_agents_yaml()
    if agent_name not in raw_configs:
        raise KeyError(
            f"Unknown agent: {agent_name}. Available: {list(raw_configs.keys())}"
        )
    return AgentConfig(**raw_configs[agent_name])


def get_llm_profile(profile: str = "default") -> LLMConfig:
    """Get validated LLM configuration for a specific profile.

    Args:
        profile: Name of the LLM profile (e.g., 'default', 'fast', 'creative')

    Returns:
        Validated LLMConfig instance.

    Raises:
        KeyError: If profile is not found in configuration.
    """
    raw_configs = _load_llm_yaml()
    if profile not in raw_configs:
        raise KeyError(
            f"Unknown LLM profile: {profile}. Available: {list(raw_configs.keys())}"
        )
    return LLMConfig(**raw_configs[profile])


def get_task_config(task_name: str) -> TaskConfig:
    """Get validated configuration for a specific task.

    Args:
        task_name: Name of the task (e.g., 'unified_analysis', 'write_recipe',
            'advise_bottles')

    Returns:
        Validated TaskConfig instance with description, expected_output,
        and output_model fields.

    Raises:
        KeyError: If task_name is not found in configuration.
    """
    raw_configs = _load_tasks_yaml()
    if task_name not in raw_configs:
        raise KeyError(
            f"Unknown task: {task_name}. Available: {list(raw_configs.keys())}"
        )
    return TaskConfig(**raw_configs[task_name])


__all__ = [
    "load_agents_config",
    "load_llm_config",
    "load_tasks_config",
    "get_agent_config",
    "get_llm_profile",
    "get_task_config",
    "AgentConfig",
    "LLMConfig",
    "TaskConfig",
]
