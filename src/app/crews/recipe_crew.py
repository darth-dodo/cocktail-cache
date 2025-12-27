"""Recipe Crew for generating skill-appropriate recipes with bottle advice.

This crew chains the Recipe Writer and Bottle Advisor agents to provide
a complete recommendation workflow: first generating a tailored recipe,
then suggesting strategic bottle purchases based on the user's cabinet.

Uses structured Pydantic models for reliable, typed outputs.
"""

from crewai import Crew, Process, Task

from src.app.agents import create_bottle_advisor, create_recipe_writer
from src.app.models import (
    BottleAdvisorOutput,
    DrinkType,
    RecipeCrewOutput,
    RecipeOutput,
    SkillLevel,
)
from src.app.tools import RecipeDBTool, SubstitutionFinderTool, UnlockCalculatorTool


def create_recipe_crew(include_bottle_advice: bool = True) -> Crew:
    """Create the Recipe Crew that chains Recipe Writer -> Bottle Advisor.

    The crew executes sequential tasks:
    1. Recipe Writer generates a skill-appropriate recipe with technique tips
    2. (Optional) Bottle Advisor recommends next bottle purchases based on cabinet context

    Both tasks use structured Pydantic output models for reliable data.

    Args:
        include_bottle_advice: Whether to include the bottle advisor task.
            When False, skips the bottle recommendation step to save processing time.
            Defaults to True.

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
        # Access structured outputs via result.tasks_output
    """
    # Initialize tools for each agent
    recipe_tools = [RecipeDBTool(), SubstitutionFinderTool()]

    # Create agents with their specialized tools
    recipe_writer = create_recipe_writer(tools=recipe_tools)

    # Build agents and tasks lists based on configuration
    agents = [recipe_writer]
    tasks = []

    # Task 1: Generate skill-appropriate recipe with structured output
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
            "5. Include any relevant substitution options for missing ingredients\n\n"
            "IMPORTANT: Return the result as a valid JSON object matching the RecipeOutput schema."
        ),
        expected_output=(
            "A JSON object with structure:\n"
            "{\n"
            '  "id": "cocktail-id",\n'
            '  "name": "Cocktail Name",\n'
            '  "tagline": "Short catchy description",\n'
            '  "why": "Why this drink matches the users mood",\n'
            '  "flavor_profile": {"sweet": 30, "sour": 20, "bitter": 25, "spirit": 70},\n'
            '  "ingredients": [\n'
            '    {"amount": "2", "unit": "oz", "item": "bourbon"}\n'
            "  ],\n"
            '  "method": [\n'
            '    {"action": "Add", "detail": "ingredients to mixing glass"}\n'
            "  ],\n"
            '  "glassware": "rocks",\n'
            '  "garnish": "orange peel",\n'
            '  "timing": "3 minutes",\n'
            '  "difficulty": "easy",\n'
            '  "technique_tips": [\n'
            '    {"skill_level": "beginner", "tip": "Use large ice to slow dilution"}\n'
            "  ],\n"
            '  "substitutions": ["alternative ingredient suggestions"],\n'
            '  "is_mocktail": false\n'
            "}"
        ),
        agent=recipe_writer,
        output_pydantic=RecipeOutput,
    )
    tasks.append(recipe_task)

    # Task 2 (Optional): Recommend next bottle purchase with structured output
    if include_bottle_advice:
        bottle_tools = [UnlockCalculatorTool()]
        bottle_advisor = create_bottle_advisor(tools=bottle_tools)
        agents.append(bottle_advisor)

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
                "5. Provide 2-3 top recommendations with clear reasoning\n\n"
                "IMPORTANT: Return the result as a valid JSON object matching the "
                "BottleAdvisorOutput schema."
            ),
            expected_output=(
                "A JSON object with structure:\n"
                "{\n"
                '  "recommendations": [\n'
                "    {\n"
                '      "ingredient": "ingredient-id",\n'
                '      "ingredient_name": "Ingredient Name",\n'
                '      "unlocks": 5,\n'
                '      "drinks": ["Drink 1", "Drink 2"],\n'
                '      "reasoning": "Why this is a good purchase"\n'
                "    }\n"
                "  ],\n"
                '  "total_new_drinks": 10\n'
                "}"
            ),
            agent=bottle_advisor,
            context=[recipe_task],
            output_pydantic=BottleAdvisorOutput,
        )
        tasks.append(bottle_task)

    # Create the crew with sequential execution
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )

    return crew


def run_recipe_crew(
    cocktail_id: str,
    skill_level: SkillLevel | str,
    cabinet: list[str],
    drink_type: DrinkType | str = DrinkType.COCKTAIL,
    include_bottle_advice: bool = True,
) -> RecipeCrewOutput:
    """Run the recipe crew and return structured output.

    Args:
        cocktail_id: The ID of the cocktail to generate a recipe for.
        skill_level: User's bartending skill level (beginner/intermediate/adventurous).
        cabinet: List of ingredient IDs available in the user's cabinet.
        drink_type: Preferred drink type (cocktail/mocktail/both).
        include_bottle_advice: Whether to include bottle recommendations.
            When False, skips the bottle advisor task to save processing time.
            Defaults to True.

    Returns:
        RecipeCrewOutput containing the recipe and bottle advice (if enabled).

    Example:
        result = run_recipe_crew(
            cocktail_id="old-fashioned",
            skill_level=SkillLevel.BEGINNER,
            cabinet=["bourbon", "simple-syrup", "angostura-bitters"],
            drink_type=DrinkType.COCKTAIL,
        )
        print(f"Recipe: {result.recipe.name}")
        for rec in result.bottle_advice.recommendations:
            print(f"Buy {rec.ingredient_name}: unlocks {rec.unlocks} drinks")
    """

    # Normalize enum values to strings for template substitution
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    crew = create_recipe_crew(include_bottle_advice=include_bottle_advice)
    result = crew.kickoff(
        inputs={
            "cocktail_id": cocktail_id,
            "skill_level": skill_str,
            "cabinet": cabinet,
            "drink_type": drink_str,
        }
    )

    # Extract structured outputs from tasks_output
    recipe_output: RecipeOutput | None = None
    bottle_output: BottleAdvisorOutput | None = None

    if hasattr(result, "tasks_output") and result.tasks_output:
        # Task 0: Recipe Writer output
        if len(result.tasks_output) >= 1:
            task_0 = result.tasks_output[0]
            if hasattr(task_0, "pydantic") and isinstance(
                task_0.pydantic, RecipeOutput
            ):
                recipe_output = task_0.pydantic
            else:
                # Try to parse from raw
                recipe_output = _parse_recipe_output(str(task_0), cocktail_id)

        # Task 1: Bottle Advisor output (only if bottle advice was included)
        if include_bottle_advice and len(result.tasks_output) >= 2:
            task_1 = result.tasks_output[1]
            if hasattr(task_1, "pydantic") and isinstance(
                task_1.pydantic, BottleAdvisorOutput
            ):
                bottle_output = task_1.pydantic
            else:
                # Try to parse from raw
                bottle_output = _parse_bottle_output(str(task_1))

    # Fallback: try to get from final result pydantic
    if recipe_output is None and hasattr(result, "pydantic") and result.pydantic:
        if isinstance(result.pydantic, RecipeOutput):
            recipe_output = result.pydantic
        elif isinstance(result.pydantic, BottleAdvisorOutput):
            bottle_output = result.pydantic

    # Create default recipe if still None
    if recipe_output is None:
        recipe_output = _create_default_recipe(cocktail_id, str(result))

    # Create default bottle output if None
    if bottle_output is None:
        bottle_output = BottleAdvisorOutput(recommendations=[], total_new_drinks=0)

    return RecipeCrewOutput(recipe=recipe_output, bottle_advice=bottle_output)


def _parse_recipe_output(raw: str, cocktail_id: str) -> RecipeOutput:
    """Parse recipe output from raw text."""
    import json
    import re

    try:
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            data = json.loads(json_match.group())
            return RecipeOutput(**data)
    except (json.JSONDecodeError, ValueError):
        pass

    return _create_default_recipe(cocktail_id, raw)


def _parse_bottle_output(raw: str) -> BottleAdvisorOutput:
    """Parse bottle advisor output from raw text."""
    import json
    import re

    try:
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            data = json.loads(json_match.group())
            return BottleAdvisorOutput(**data)
    except (json.JSONDecodeError, ValueError):
        pass

    return BottleAdvisorOutput(recommendations=[], total_new_drinks=0)


def _create_default_recipe(cocktail_id: str, raw_content: str) -> RecipeOutput:
    """Create a default recipe output when parsing fails."""
    from src.app.models import FlavorProfile
    from src.app.models.recipe import RecipeIngredient, RecipeStep

    return RecipeOutput(
        id=cocktail_id,
        name=cocktail_id.replace("-", " ").title(),
        tagline="A classic cocktail",
        why="Selected based on your available ingredients and mood.",
        flavor_profile=FlavorProfile(sweet=30, sour=20, bitter=25, spirit=70),
        ingredients=[RecipeIngredient(amount="2", unit="oz", item="spirit")],
        method=[RecipeStep(action="Mix", detail="Combine ingredients and serve")],
        glassware="rocks",
        garnish="optional",
        timing="3 minutes",
        difficulty="easy",
        technique_tips=[],
        substitutions=[],
        is_mocktail=False,
    )
