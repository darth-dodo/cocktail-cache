"""Cabinet Analyst agent for identifying makeable drinks.

This agent analyzes a user's bar cabinet contents and determines
which cocktails and mocktails can be made with available ingredients.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm


def create_cabinet_analyst(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Cabinet Analyst agent.

    The Cabinet Analyst is an expert mixologist who knows every classic
    cocktail and mocktail recipe. Given a home bar cabinet inventory,
    it identifies which drinks can be made with available ingredients.

    Args:
        tools: List of tools the agent can use. Typically includes
            RecipeDBTool for querying the recipe database.
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("cabinet_analyst")
    return Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
    )
