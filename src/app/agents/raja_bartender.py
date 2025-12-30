"""Raja Bartender agent for conversational cocktail chat.

Raja is a charismatic bartender from Bombay who provides
personality-rich cocktail advice through natural conversation.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_llm


def create_raja_bartender(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Raja Bartender conversational agent.

    Raja is a personality-rich bartender from Colaba, Bombay who has
    been mixing drinks for 20 years. He speaks with warmth, uses
    Hindi phrases, and loves sharing stories about cocktails.

    Args:
        tools: List of tools the agent can use. Typically none needed
            as data is injected via task description.
        llm: Optional LLM configuration. Defaults to conversational profile
            with higher temperature for personality variation.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("raja_bartender")

    # Use conversational LLM profile for more personality
    default_llm = llm or get_llm(profile="conversational")

    return Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=tools or [],
        llm=default_llm,
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
    )
