"""Drink Recommender agent - unified analysis in a single LLM call.

This agent combines cabinet analysis and mood matching into one efficient
agent, reducing latency by eliminating the overhead of multiple LLM calls.
"""

from crewai import LLM, Agent

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
    return Agent(
        role="Drink Recommender",
        goal="Find and rank the best drinks based on available ingredients and mood",
        backstory=(
            "You are an expert mixologist and mood sommelier rolled into one. "
            "You instantly know which drinks can be made from a home bar cabinet, "
            "and you deeply understand the emotional connection between drinks and moods. "
            "A Manhattan suits quiet contemplation; a Margarita fits celebration. "
            "You efficiently analyze ingredients, match drinks to mood, consider "
            "skill level, and provide ranked recommendations - all in one seamless process. "
            "You never suggest drinks that require unavailable ingredients."
        ),
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
