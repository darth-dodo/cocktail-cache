"""Drink Recommender agent - unified analysis in a single LLM call.

This agent combines cabinet analysis and mood matching into one efficient
agent, reducing latency by eliminating the overhead of multiple LLM calls.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm


def create_drink_recommender(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Drink Recommender agent.

    This unified agent combines the capabilities of Cabinet Analyst and
    Mood Matcher into a single agent, reducing the number of LLM calls
    from 2 to 1 for the analysis phase.

    The agent:
    1. Searches the recipe database for makeable drinks
    2. Analyzes flavor profiles
    3. Ranks drinks by mood fit
    4. Returns structured recommendations

    Args:
        tools: List of tools the agent can use. Should include:
            - RecipeDBTool for querying the recipe database
            - FlavorProfilerTool for analyzing flavors
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("drink_recommender")
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=config.get("verbose", False),
        allow_delegation=config.get("allow_delegation", False),
    )
