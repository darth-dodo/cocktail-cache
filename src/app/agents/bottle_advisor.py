"""Bottle Advisor agent for recommending strategic bottle purchases.

This agent analyzes bar inventories and recommends which bottles
to buy next for maximum drink-unlocking value.
"""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm


def create_bottle_advisor(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Bottle Advisor agent.

    The Bottle Advisor analyzes bar inventories and recommends strategic
    purchases. It knows which bottles unlock the most new drink
    possibilities and considers budget-friendly options.

    Args:
        tools: List of tools the agent can use. Typically includes
            UnlockCalculatorTool for computing which bottles unlock
            the most new drinks.
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    config = get_agent_config("bottle_advisor")
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=config.get("verbose", False),
        allow_delegation=config.get("allow_delegation", False),
    )
