"""Recipe Writer agent for generating skill-appropriate recipes.

This agent creates clear, detailed recipes with technique tips
tailored to the user's skill level.
"""

from crewai import LLM, Agent

from src.app.agents.llm_config import get_default_llm


def create_recipe_writer(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create the Recipe Writer agent.

    The Recipe Writer has taught thousands of home bartenders at every
    skill level. It generates recipes with appropriate detail and
    technique tips based on the user's experience.

    Args:
        tools: List of tools the agent can use. Typically includes
            RecipeDBTool for retrieving recipes and SubstitutionFinderTool
            for suggesting ingredient alternatives.
        llm: Optional LLM configuration. Defaults to Claude Haiku.

    Returns:
        A configured CrewAI Agent instance.
    """
    return Agent(
        role="Recipe Writer",
        goal="Generate clear, skill-appropriate recipes with technique tips",
        backstory=(
            "You have taught thousands of home bartenders at every skill level. "
            "For beginners, you provide detailed technique explanations, safety tips, "
            "and precise measurements. For intermediate users, you give standard "
            "instructions with occasional tips. For adventurous bartenders, you're "
            "concise and suggest creative variations or experiments."
        ),
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
