"""Bottle Advisor agent for recommending strategic bottle purchases.

This agent analyzes bar inventories and recommends which bottles
to buy next for maximum drink-unlocking value.
"""

from crewai import Agent


def create_bottle_advisor(tools: list | None = None) -> Agent:
    """Create the Bottle Advisor agent.

    The Bottle Advisor analyzes bar inventories and recommends strategic
    purchases. It knows which bottles unlock the most new drink
    possibilities and considers budget-friendly options.

    Args:
        tools: List of tools the agent can use. Typically includes
            UnlockCalculatorTool for computing which bottles unlock
            the most new drinks.

    Returns:
        A configured CrewAI Agent instance.
    """
    return Agent(
        role="Bottle Advisor",
        goal="Recommend the next bottle purchase for maximum value",
        backstory=(
            "You analyze bar inventories and recommend strategic purchases. "
            "You know exactly which bottles unlock the most new drink possibilities. "
            "You consider budget-friendly options and suggest bottles that unlock "
            "the most NEW drinks the user cannot currently make. You always respect "
            "the user's drink type preference."
        ),
        tools=tools or [],
        verbose=False,
        allow_delegation=False,
    )
