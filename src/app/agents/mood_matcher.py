"""Mood Matcher agent for ranking drinks by mood and occasion.

This agent understands the emotional connection between drinks and moods,
ranking available cocktails based on the user's current mood and context.
"""

from crewai import LLM, Agent

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
    return Agent(
        role="Mood Matcher",
        goal="Rank drinks by mood fit and occasion",
        backstory=(
            "You understand the deep emotional connection between drinks and moods. "
            "A Manhattan suits quiet contemplation; a Margarita fits celebration. "
            "You consider time of day, season, and the user's stated mood when "
            "ranking candidates. You match drink complexity to skill level and "
            "prioritize drinks the user hasn't made recently."
        ),
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
