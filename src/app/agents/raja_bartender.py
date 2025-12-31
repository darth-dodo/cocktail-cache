"""Raja Bartender agent for conversational cocktail chat.

Raja is a charismatic bartender from Bombay who provides
personality-rich cocktail advice through natural conversation.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_llm
from src.app.tools import (
    FlavorProfilerTool,
    RecipeDBTool,
    SubstitutionFinderTool,
    UnlockCalculatorTool,
)


def _get_default_tools() -> list:
    """Return the default tools for Raja bartender agent.

    Returns:
        List of tool instances:
        - RecipeDBTool: Search drink database
        - SubstitutionFinderTool: Find ingredient substitutes
        - UnlockCalculatorTool: Recommend bottles to buy
        - FlavorProfilerTool: Compare drink flavors
    """
    return [
        RecipeDBTool(),
        SubstitutionFinderTool(),
        UnlockCalculatorTool(),
        FlavorProfilerTool(),
    ]


def create_raja_bartender(
    tools: list | None = None,
    llm: LLM | None = None,
    include_default_tools: bool = True,
) -> Agent:
    """Create the Raja Bartender conversational agent.

    Raja is a personality-rich bartender from Colaba, Bombay who has
    been mixing drinks for 20 years. He speaks with warmth, uses
    Hindi phrases, and loves sharing stories about cocktails.

    Raja has access to powerful tools:
    - RecipeDBTool: Search the drink database by ingredients
    - SubstitutionFinderTool: Find ingredient substitutes
    - UnlockCalculatorTool: Recommend bottles to buy for maximum ROI
    - FlavorProfilerTool: Compare drink flavors

    Args:
        tools: List of additional tools for the agent. If provided and
            include_default_tools is True, these are added to defaults.
        llm: Optional LLM configuration. Defaults to conversational profile
            with higher temperature for personality variation.
        include_default_tools: Whether to include the default cocktail tools.
            Defaults to True.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("raja_bartender")

    # Use conversational LLM profile for more personality
    default_llm = llm or get_llm(profile="conversational")

    # Build tools list
    if include_default_tools:
        agent_tools = _get_default_tools()
        if tools:
            agent_tools.extend(tools)
    else:
        agent_tools = tools or []

    return Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=agent_tools,
        llm=default_llm,
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
    )
