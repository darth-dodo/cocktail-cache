"""Cabinet Analyst agent for identifying makeable drinks.

This agent analyzes a user's bar cabinet contents and determines
which cocktails and mocktails can be made with available ingredients.
"""

from crewai import Agent


def create_cabinet_analyst(tools: list | None = None) -> Agent:
    """Create the Cabinet Analyst agent.

    The Cabinet Analyst is an expert mixologist who knows every classic
    cocktail and mocktail recipe. Given a home bar cabinet inventory,
    it identifies which drinks can be made with available ingredients.

    Args:
        tools: List of tools the agent can use. Typically includes
            RecipeDBTool for querying the recipe database.

    Returns:
        A configured CrewAI Agent instance.
    """
    return Agent(
        role="Cabinet Analyst",
        goal="Identify all drinks makeable with available ingredients",
        backstory=(
            "You are an expert mixologist who has memorized every classic cocktail "
            "and mocktail recipe. When shown a home bar cabinet, you instantly "
            "recognize which drinks can be made. You consider close substitutions "
            "and always respect the user's drink type preference (cocktail, mocktail, "
            "or both). You never suggest drinks that require unavailable ingredients."
        ),
        tools=tools or [],
        verbose=False,
        allow_delegation=False,
    )
