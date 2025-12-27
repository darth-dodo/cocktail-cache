"""Recipe Crew for generating skill-appropriate recipes with bottle advice.

This crew chains the Recipe Writer and Bottle Advisor agents to provide
a complete recommendation workflow: first generating a tailored recipe,
then suggesting strategic bottle purchases based on the user's cabinet.
"""

from crewai import Crew, Process, Task

from src.app.agents import create_bottle_advisor, create_recipe_writer
from src.app.models import DrinkType, SkillLevel
from src.app.tools import RecipeDBTool, SubstitutionFinderTool, UnlockCalculatorTool


def create_recipe_crew() -> Crew:
    """Create the Recipe Crew that chains Recipe Writer -> Bottle Advisor.

    The crew executes two sequential tasks:
    1. Recipe Writer generates a skill-appropriate recipe with technique tips
    2. Bottle Advisor recommends next bottle purchases based on cabinet context

    Returns:
        A configured CrewAI Crew instance ready for execution.

    Example:
        crew = create_recipe_crew()
        result = crew.kickoff(inputs={
            "cocktail_id": "manhattan",
            "skill_level": "beginner",
            "cabinet": ["bourbon", "sweet-vermouth", "angostura-bitters"],
            "drink_type": "cocktail",
        })
    """
    # Initialize tools for each agent
    recipe_tools = [RecipeDBTool(), SubstitutionFinderTool()]
    bottle_tools = [UnlockCalculatorTool()]

    # Create agents with their specialized tools
    recipe_writer = create_recipe_writer(tools=recipe_tools)
    bottle_advisor = create_bottle_advisor(tools=bottle_tools)

    # Task 1: Generate skill-appropriate recipe
    recipe_task = Task(
        description=(
            "Generate a detailed recipe for the cocktail with ID '{cocktail_id}'.\n\n"
            "User Context:\n"
            "- Skill Level: {skill_level}\n"
            "- Available Ingredients: {cabinet}\n"
            "- Drink Type Preference: {drink_type}\n\n"
            "Instructions:\n"
            "1. Use the recipe_database tool to retrieve the full recipe details\n"
            "2. Check if any ingredients are missing from the user's cabinet\n"
            "3. If ingredients are missing, use substitution_finder to suggest alternatives\n"
            "4. Adapt the recipe complexity and technique tips to the user's skill level:\n"
            "   - beginner: Detailed explanations, safety tips, precise measurements\n"
            "   - intermediate: Standard instructions with occasional tips\n"
            "   - adventurous: Concise instructions, suggest creative variations\n"
            "5. Include any relevant substitution options for missing ingredients"
        ),
        expected_output=(
            "A complete recipe including:\n"
            "- Drink name and description\n"
            "- Full ingredient list with measurements\n"
            "- Step-by-step preparation instructions\n"
            "- Technique tips appropriate for the skill level\n"
            "- Suggested substitutions for any missing ingredients\n"
            "- Glassware and garnish recommendations"
        ),
        agent=recipe_writer,
    )

    # Task 2: Recommend next bottle purchase (depends on recipe context)
    bottle_task = Task(
        description=(
            "Based on the recipe just generated and the user's current cabinet, "
            "recommend which bottle they should buy next.\n\n"
            "User Context:\n"
            "- Current Cabinet: {cabinet}\n"
            "- Drink Type Preference: {drink_type}\n\n"
            "Instructions:\n"
            "1. Use the unlock_calculator tool to analyze which new bottles would "
            "unlock the most additional drinks\n"
            "2. Consider the drink type preference when making recommendations\n"
            "3. Prioritize bottles that complement what the user already has\n"
            "4. Focus on bottles that unlock NEW drinks the user cannot currently make\n"
            "5. Provide 2-3 top recommendations with clear reasoning"
        ),
        expected_output=(
            "A prioritized list of bottle recommendations including:\n"
            "- Top 2-3 bottles to buy next\n"
            "- Number of new drinks each bottle would unlock\n"
            "- Specific drinks that would become available\n"
            "- Brief reasoning for each recommendation"
        ),
        agent=bottle_advisor,
        context=[recipe_task],  # Bottle advisor receives recipe context
    )

    # Create the crew with sequential execution
    crew = Crew(
        agents=[recipe_writer, bottle_advisor],
        tasks=[recipe_task, bottle_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


def run_recipe_crew(
    cocktail_id: str,
    skill_level: SkillLevel | str,
    cabinet: list[str],
    drink_type: DrinkType | str = DrinkType.COCKTAIL,
) -> str:
    """Convenience function to create and run the recipe crew.

    Args:
        cocktail_id: The ID of the cocktail to generate a recipe for.
        skill_level: User's bartending skill level (beginner/intermediate/adventurous).
        cabinet: List of ingredient IDs available in the user's cabinet.
        drink_type: Preferred drink type (cocktail/mocktail/both).

    Returns:
        The crew's output as a string containing the recipe and bottle advice.

    Example:
        result = run_recipe_crew(
            cocktail_id="old-fashioned",
            skill_level=SkillLevel.BEGINNER,
            cabinet=["bourbon", "simple-syrup", "angostura-bitters"],
            drink_type=DrinkType.COCKTAIL,
        )
    """
    # Normalize enum values to strings for template substitution
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    crew = create_recipe_crew()
    result = crew.kickoff(
        inputs={
            "cocktail_id": cocktail_id,
            "skill_level": skill_str,
            "cabinet": cabinet,
            "drink_type": drink_str,
        }
    )

    return str(result)
