"""Bar Growth Advisor agent for strategic bar building recommendations.

This agent provides personalized advice on which bottles to purchase
next to maximize cocktail-making potential, focusing on core bottles
while assuming kitchen items are available.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm


def create_bar_growth_advisor(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Bar Growth Advisor agent.

    The Bar Growth Advisor helps home bartenders build their collection
    strategically. It focuses on CORE BOTTLES (spirits, modifiers,
    non-alcoholic spirits) rather than kitchen items that most people
    already have. It provides encouraging, personalized advice.

    Philosophy:
    - Track your BAR, assume your KITCHEN
    - Core Bottles: spirits, modifiers, non-alcoholic spirits (track these)
    - Essentials: bitters, specialty syrups (nice-to-have, optional tracking)
    - Kitchen: fresh produce, mixers (assume available)

    Args:
        tools: List of tools the agent can use. Typically none needed
            as data is injected via task description.
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("bar_growth_advisor")
    return Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
    )
