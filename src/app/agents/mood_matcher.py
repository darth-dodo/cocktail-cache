"""Mood Matcher agent for ranking drinks by mood and occasion.

This agent understands the emotional connection between drinks and moods,
ranking available cocktails based on the user's current mood and context.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm


def create_mood_matcher(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Mood Matcher agent.

    The Mood Matcher understands the emotional resonance of drinks.
    It knows that a Manhattan suits quiet contemplation while a
    Margarita fits celebration. It ranks candidates by mood fit.

    Args:
        tools: List of tools the agent can use. Typically includes
            FlavorProfilerTool for analyzing flavor characteristics.
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("mood_matcher")
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=config.get("verbose", False),
        allow_delegation=config.get("allow_delegation", False),
    )
