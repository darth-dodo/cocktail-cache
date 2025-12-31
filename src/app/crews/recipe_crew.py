"""Recipe Crew for generating skill-appropriate recipes with bottle advice.

This crew chains the Recipe Writer and Bottle Advisor agents to provide
a complete recommendation workflow: first generating a tailored recipe,
then suggesting strategic bottle purchases based on the user's cabinet.

Uses structured Pydantic models for reliable, typed outputs.
"""

import logging
import time

from crewai import Crew, Process, Task

from src.app.agents import create_bottle_advisor, create_recipe_writer
from src.app.models import (
    BottleAdvisorOutput,
    DrinkType,
    RecipeCrewOutput,
    RecipeOutput,
    SkillLevel,
)
from src.app.services.drink_data import (
    DrinkTypeFilter,
    format_bottle_recommendations_for_prompt,
    format_recipe_for_prompt,
    get_drink_by_id,
    get_substitutions_for_ingredients,
    get_unlock_recommendations,
)
from src.app.utils.parsing import parse_json_from_llm_output

logger = logging.getLogger(__name__)


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
            "recipe_data": "...",  # Pre-computed recipe data
            "substitutions_data": "...",  # Pre-computed substitutions
            "bottle_recommendations": "...",  # Pre-computed recommendations
        })
        # Access structured outputs via result.tasks_output
    """
    logger.info(
        f"Creating recipe crew with include_bottle_advice={include_bottle_advice}"
    )

    # Create agents without tools - data is injected directly into prompts
    recipe_writer = create_recipe_writer(tools=[])

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
            "Complete Recipe Data (pre-loaded):\n"
            "{recipe_data}\n\n"
            "Available Substitutions:\n"
            "{substitutions_data}\n\n"
            "Instructions:\n"
            "1. Use the recipe data provided above to create a complete recipe response\n"
            "2. Check if any ingredients are missing from the user's cabinet\n"
            "3. Include the substitution options listed above for any missing ingredients\n"
            "4. Adapt the recipe complexity and technique tips to the user's skill level:\n"
            "   - beginner: Detailed explanations, safety tips, precise measurements\n"
            "   - intermediate: Standard instructions with occasional tips\n"
            "   - adventurous: Concise instructions, suggest creative variations\n"
            "5. Generate a 'why' explanation for why this drink matches the user's context\n\n"
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
        # Create bottle advisor without tools - data is injected directly into prompts
        bottle_advisor = create_bottle_advisor(tools=[])
        agents.append(bottle_advisor)

        bottle_task = Task(
            description=(
                "Based on the recipe just generated and the user's current cabinet, "
                "recommend which bottle they should buy next.\n\n"
                "User Context:\n"
                "- Current Cabinet: {cabinet}\n"
                "- Drink Type Preference: {drink_type}\n\n"
                "Pre-computed Bottle Recommendations (based on unlock potential):\n"
                "{bottle_recommendations}\n\n"
                "Instructions:\n"
                "1. Use the pre-computed recommendations above to create your response\n"
                "2. Consider the drink type preference when making recommendations\n"
                "3. Prioritize bottles that complement what the user already has\n"
                "4. Focus on bottles that unlock NEW drinks the user cannot currently make\n"
                "5. Select the top 2-3 recommendations and provide clear reasoning for each\n\n"
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
    start_time = time.perf_counter()
    logger.info(
        f"run_recipe_crew started: cocktail_id={cocktail_id}, skill_level={skill_level}, "
        f"drink_type={drink_type}, cabinet_size={len(cabinet)}, include_bottle_advice={include_bottle_advice}"
    )

    # Normalize enum values to strings for template substitution
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    # Pre-compute all data for prompt injection (eliminates tool call latency)
    data_start = time.perf_counter()

    # 1. Get complete recipe data
    drink = get_drink_by_id(cocktail_id)
    if drink:
        recipe_data = format_recipe_for_prompt(drink)
    else:
        recipe_data = f"Recipe not found for ID: {cocktail_id}"
        logger.warning(f"Recipe not found for cocktail_id={cocktail_id}")

    # 2. Get substitutions for all ingredients in the recipe
    if drink:
        ingredient_ids = [ing["item"] for ing in drink.get("ingredients", [])]
        substitutions = get_substitutions_for_ingredients(ingredient_ids)
        if substitutions:
            subs_lines = []
            for ing, subs in substitutions.items():
                subs_lines.append(f"- {ing}: {', '.join(subs)}")
            substitutions_data = "\n".join(subs_lines)
        else:
            substitutions_data = "No substitutions available for the ingredients."
    else:
        substitutions_data = "No substitutions available (recipe not found)."

    # 3. Get bottle recommendations (only if needed)
    if include_bottle_advice:
        # Map drink_type string to the format expected by get_unlock_recommendations
        unlock_drink_type: DrinkTypeFilter = "both"
        if drink_str == "cocktail":
            unlock_drink_type = "cocktails"
        elif drink_str == "mocktail":
            unlock_drink_type = "mocktails"

        recommendations = get_unlock_recommendations(
            cabinet, unlock_drink_type, top_n=5
        )
        bottle_recommendations = format_bottle_recommendations_for_prompt(
            recommendations
        )
    else:
        bottle_recommendations = ""

    data_elapsed_ms = (time.perf_counter() - data_start) * 1000

    crew = create_recipe_crew(include_bottle_advice=include_bottle_advice)

    crew_start = time.perf_counter()
    result = crew.kickoff(
        inputs={
            "cocktail_id": cocktail_id,
            "skill_level": skill_str,
            "cabinet": cabinet,
            "drink_type": drink_str,
            "recipe_data": recipe_data,
            "substitutions_data": substitutions_data,
            "bottle_recommendations": bottle_recommendations,
        }
    )
    crew_elapsed_ms = (time.perf_counter() - crew_start) * 1000

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
                logger.warning(
                    "Recipe pydantic output unavailable, attempting raw parse"
                )
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
                logger.warning(
                    "Bottle pydantic output unavailable, attempting raw parse"
                )
                bottle_output = _parse_bottle_output(str(task_1))

    # Fallback: try to get from final result pydantic
    if recipe_output is None and hasattr(result, "pydantic") and result.pydantic:
        if isinstance(result.pydantic, RecipeOutput):
            recipe_output = result.pydantic
        elif isinstance(result.pydantic, BottleAdvisorOutput):
            bottle_output = result.pydantic

    # Create default recipe if still None
    if recipe_output is None:
        logger.error(
            f"Failed to extract recipe output for {cocktail_id}, using default"
        )
        recipe_output = _create_default_recipe(cocktail_id, str(result))

    # Create default bottle output if None
    if bottle_output is None:
        if include_bottle_advice:
            logger.warning("No bottle output available, using empty default")
        bottle_output = BottleAdvisorOutput(recommendations=[], total_new_drinks=0)

    total_elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"run_recipe_crew completed: recipe='{recipe_output.name}', "
        f"bottle_recommendations={len(bottle_output.recommendations)} in {total_elapsed_ms:.2f}ms "
        f"(data: {data_elapsed_ms:.2f}ms, crew: {crew_elapsed_ms:.2f}ms)"
    )
    return RecipeCrewOutput(recipe=recipe_output, bottle_advice=bottle_output)


def _parse_recipe_output(raw: str, cocktail_id: str) -> RecipeOutput:
    """Parse recipe output from raw text."""
    parsed = parse_json_from_llm_output(raw, RecipeOutput, logger, "recipe output")
    if parsed:
        return parsed

    logger.warning(f"Fallback to default recipe for {cocktail_id}")
    return _create_default_recipe(cocktail_id, raw)


def _parse_bottle_output(raw: str) -> BottleAdvisorOutput:
    """Parse bottle advisor output from raw text."""
    parsed = parse_json_from_llm_output(
        raw, BottleAdvisorOutput, logger, "bottle output"
    )
    if parsed:
        return parsed

    logger.warning("Fallback to empty bottle recommendations")
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


def create_recipe_only_crew() -> Crew:
    """Create a crew with only the Recipe Writer task.

    This crew is designed for parallel execution scenarios where the
    recipe generation runs independently of bottle advice. It contains
    only the Recipe Writer agent and task.

    Returns:
        A configured CrewAI Crew instance with only the Recipe Writer.

    Example:
        crew = create_recipe_only_crew()
        result = await crew.kickoff_async(inputs={
            "cocktail_id": "manhattan",
            "skill_level": "beginner",
            "cabinet": ["bourbon", "sweet-vermouth", "angostura-bitters"],
            "drink_type": "cocktail",
            "recipe_data": "...",  # Pre-computed recipe data
            "substitutions_data": "...",  # Pre-computed substitutions
        })
    """
    logger.info("Creating recipe-only crew (for parallel execution)")

    # Create recipe writer without tools - data is injected directly into prompts
    recipe_writer = create_recipe_writer(tools=[])

    # Create the recipe task (same as in create_recipe_crew)
    recipe_task = Task(
        description=(
            "Generate a detailed recipe for the cocktail with ID '{cocktail_id}'.\n\n"
            "User Context:\n"
            "- Skill Level: {skill_level}\n"
            "- Available Ingredients: {cabinet}\n"
            "- Drink Type Preference: {drink_type}\n\n"
            "Complete Recipe Data (pre-loaded):\n"
            "{recipe_data}\n\n"
            "Available Substitutions:\n"
            "{substitutions_data}\n\n"
            "Instructions:\n"
            "1. Use the recipe data provided above to create a complete recipe response\n"
            "2. Check if any ingredients are missing from the user's cabinet\n"
            "3. Include the substitution options listed above for any missing ingredients\n"
            "4. Adapt the recipe complexity and technique tips to the user's skill level:\n"
            "   - beginner: Detailed explanations, safety tips, precise measurements\n"
            "   - intermediate: Standard instructions with occasional tips\n"
            "   - adventurous: Concise instructions, suggest creative variations\n"
            "5. Generate a 'why' explanation for why this drink matches the user's context\n\n"
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

    crew = Crew(
        agents=[recipe_writer],
        tasks=[recipe_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


def create_bottle_only_crew() -> Crew:
    """Create a crew with only the Bottle Advisor task.

    This crew is designed for parallel execution scenarios where bottle
    advice generation runs independently of recipe generation. The bottle
    task does NOT have a context dependency on the recipe task.

    Returns:
        A configured CrewAI Crew instance with only the Bottle Advisor.

    Example:
        crew = create_bottle_only_crew()
        result = await crew.kickoff_async(inputs={
            "cabinet": ["bourbon", "sweet-vermouth", "angostura-bitters"],
            "drink_type": "cocktail",
            "bottle_recommendations": "...",  # Pre-computed recommendations
        })
    """
    logger.info("Creating bottle-only crew (for parallel execution)")

    # Create bottle advisor without tools - data is injected directly into prompts
    bottle_advisor = create_bottle_advisor(tools=[])

    # Create the bottle task WITHOUT context dependency on recipe_task
    bottle_task = Task(
        description=(
            "Recommend which bottle the user should buy next based on their "
            "current cabinet and drink preferences.\n\n"
            "User Context:\n"
            "- Current Cabinet: {cabinet}\n"
            "- Drink Type Preference: {drink_type}\n\n"
            "Pre-computed Bottle Recommendations (based on unlock potential):\n"
            "{bottle_recommendations}\n\n"
            "Instructions:\n"
            "1. Use the pre-computed recommendations above to create your response\n"
            "2. Consider the drink type preference when making recommendations\n"
            "3. Prioritize bottles that complement what the user already has\n"
            "4. Focus on bottles that unlock NEW drinks the user cannot currently make\n"
            "5. Select the top 2-3 recommendations and provide clear reasoning for each\n\n"
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
        # NO context dependency - runs independently
        output_pydantic=BottleAdvisorOutput,
    )

    crew = Crew(
        agents=[bottle_advisor],
        tasks=[bottle_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew
