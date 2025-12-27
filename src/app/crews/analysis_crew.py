"""Analysis Crew for cocktail recommendations.

This crew analyzes the user's cabinet and mood to find and rank suitable drinks.

Supports two modes:
- Fast mode (default): Single agent, single LLM call (~50% faster)
- Full mode: Two agents for detailed analysis (Cabinet Analyst → Mood Matcher)

The crew uses structured Pydantic models for inputs and outputs,
ensuring reliable, typed data flow through the AI pipeline.
"""

from crewai import Crew, Process, Task

from src.app.agents import (
    create_cabinet_analyst,
    create_drink_recommender,
    create_mood_matcher,
)
from src.app.models import AnalysisOutput, DrinkType, SkillLevel
from src.app.tools import FlavorProfilerTool, RecipeDBTool


def create_analysis_crew(fast_mode: bool = True) -> Crew:
    """Create the Analysis Crew for finding and ranking drinks.

    Args:
        fast_mode: If True (default), uses a single unified agent for faster
            response. If False, uses two sequential agents for more detailed
            analysis.

    The crew expects the following inputs when kicked off:
        - cabinet: List of ingredient IDs the user has available
        - drink_type: 'cocktails', 'mocktails', or 'both'
        - mood: Description of the user's current mood/occasion
        - skill_level: 'beginner', 'intermediate', or 'adventurous'
        - exclude: List of drink IDs to exclude (recent history)

    Returns:
        A configured Crew instance ready to be kicked off with inputs.
        The output will be structured as AnalysisOutput Pydantic model.

    Example:
        crew = create_analysis_crew(fast_mode=True)
        result = crew.kickoff(inputs={
            "cabinet": ["bourbon", "lemons", "honey", "simple-syrup"],
            "drink_type": "cocktails",
            "mood": "unwinding after a long week",
            "skill_level": "intermediate",
            "exclude": ["whiskey-sour", "old-fashioned"]
        })
        # result.pydantic contains AnalysisOutput
    """
    if fast_mode:
        return _create_fast_crew()
    else:
        return _create_full_crew()


def _create_fast_crew() -> Crew:
    """Create a single-agent crew for fast analysis.

    Uses one unified Drink Recommender agent with both tools,
    completing the entire analysis in a single LLM call.
    """
    # Create tool instances
    recipe_db = RecipeDBTool()
    flavor_profiler = FlavorProfilerTool()

    # Create unified agent with both tools
    drink_recommender = create_drink_recommender(tools=[recipe_db, flavor_profiler])

    # Single task that does everything
    unified_task = Task(
        description=(
            "Find and rank the best drinks for the user based on their cabinet and mood.\n\n"
            "Cabinet contents: {cabinet}\n"
            "Drink type preference: {drink_type}\n"
            "User's mood: {mood}\n"
            "Skill level: {skill_level}\n"
            "Drinks to exclude: {exclude}\n\n"
            "Instructions:\n"
            "1. Use the recipe_database tool to find drinks makeable with the cabinet ingredients\n"
            "2. Filter to only include drinks with score=1.0 (all ingredients available)\n"
            "3. Exclude any drinks in the exclude list\n"
            "4. Use the flavor_profiler tool to understand drink characteristics\n"
            "5. Rank drinks by mood fit:\n"
            "   - Relaxing moods → spirit-forward, balanced drinks\n"
            "   - Celebratory moods → refreshing, bright drinks\n"
            "   - Contemplative moods → complex, layered drinks\n"
            "6. Consider skill level when ranking (beginners need simpler drinks)\n"
            "7. Return the top 5 ranked drinks\n\n"
            "IMPORTANT: Return the result as a valid JSON object matching the "
            "AnalysisOutput schema."
        ),
        expected_output=(
            "A JSON object with structure:\n"
            "{\n"
            '  "candidates": [\n'
            "    {\n"
            '      "id": "drink-id",\n'
            '      "name": "Drink Name",\n'
            '      "tagline": "Brief description",\n'
            '      "difficulty": "easy|medium|hard|advanced",\n'
            '      "timing_minutes": 5,\n'
            '      "tags": ["tag1", "tag2"],\n'
            '      "is_mocktail": false,\n'
            '      "mood_score": 85,\n'
            '      "mood_reasoning": "Why this matches the mood"\n'
            "    }\n"
            "  ],\n"
            '  "total_found": 3,\n'
            '  "mood_summary": "Summary of mood-based ranking"\n'
            "}"
        ),
        agent=drink_recommender,
        output_pydantic=AnalysisOutput,
    )

    return Crew(
        agents=[drink_recommender],
        tasks=[unified_task],
        process=Process.sequential,
        verbose=False,
    )


def _create_full_crew() -> Crew:
    """Create a two-agent crew for detailed analysis.

    Uses Cabinet Analyst → Mood Matcher for more thorough analysis,
    but requires two LLM calls.
    """
    # Create tool instances
    recipe_db = RecipeDBTool()
    flavor_profiler = FlavorProfilerTool()

    # Create agents with their respective tools
    cabinet_analyst = create_cabinet_analyst(tools=[recipe_db])
    mood_matcher = create_mood_matcher(tools=[flavor_profiler])

    # Task 1: Analyze cabinet contents and find makeable drinks
    analyze_task = Task(
        description=(
            "Analyze the user's bar cabinet and find all drinks that can be made.\n\n"
            "Cabinet contents: {cabinet}\n"
            "Drink type preference: {drink_type}\n\n"
            "Use the recipe_database tool to search for drinks matching these "
            "ingredients. Filter by the drink type preference (cocktails, mocktails, "
            "or both). Return all drinks with a match score of 1.0 (complete matches) "
            "along with their key details (name, difficulty, timing, tags).\n\n"
            "Important: Only include drinks where ALL required ingredients are "
            "available in the cabinet."
        ),
        expected_output=(
            "A JSON list of makeable drinks, each containing:\n"
            "- id: The drink identifier\n"
            "- name: The drink name\n"
            "- tagline: Brief description\n"
            "- difficulty: Skill level required (easy, medium, hard, advanced)\n"
            "- timing_minutes: Preparation time as integer\n"
            "- tags: Flavor and style tags as list\n"
            "- is_mocktail: Boolean whether it's a mocktail"
        ),
        agent=cabinet_analyst,
    )

    # Task 2: Rank drinks by mood fit - outputs structured AnalysisOutput
    match_task = Task(
        description=(
            "Rank the candidate drinks by how well they match the user's mood "
            "and preferences.\n\n"
            "User's mood: {mood}\n"
            "Skill level: {skill_level}\n"
            "Drinks to exclude: {exclude}\n\n"
            "Use the flavor_profiler tool to get detailed flavor profiles for "
            "the candidate drinks from the previous analysis. Consider:\n\n"
            "1. Mood alignment: Match drink characteristics to the stated mood\n"
            "   - Relaxing moods pair well with spirit-forward, balanced drinks\n"
            "   - Celebratory moods pair well with refreshing, bright drinks\n"
            "   - Contemplative moods pair well with complex, layered drinks\n\n"
            "2. Skill appropriateness: Beginners need simpler techniques;\n"
            "   adventurous users can handle complex preparations\n\n"
            "3. Variety: Exclude drinks from the exclude list (recent history)\n"
            "   to encourage exploration\n\n"
            "Rank the remaining drinks from best to worst mood fit.\n\n"
            "IMPORTANT: Return the result as a valid JSON object matching the "
            "AnalysisOutput schema with 'candidates', 'total_found', and 'mood_summary' fields."
        ),
        expected_output=(
            "A JSON object with structure:\n"
            "{\n"
            '  "candidates": [\n'
            "    {\n"
            '      "id": "drink-id",\n'
            '      "name": "Drink Name",\n'
            '      "tagline": "Brief description",\n'
            '      "difficulty": "easy|medium|hard|advanced",\n'
            '      "timing_minutes": 5,\n'
            '      "tags": ["tag1", "tag2"],\n'
            '      "is_mocktail": false,\n'
            '      "mood_score": 85,\n'
            '      "mood_reasoning": "Why this matches the mood"\n'
            "    }\n"
            "  ],\n"
            '  "total_found": 3,\n'
            '  "mood_summary": "Summary of mood-based ranking"\n'
            "}"
        ),
        agent=mood_matcher,
        context=[analyze_task],
        output_pydantic=AnalysisOutput,
    )

    return Crew(
        agents=[cabinet_analyst, mood_matcher],
        tasks=[analyze_task, match_task],
        process=Process.sequential,
        verbose=False,
    )


def run_analysis_crew(
    cabinet: list[str],
    mood: str,
    skill_level: SkillLevel | str = SkillLevel.INTERMEDIATE,
    drink_type: DrinkType | str = DrinkType.COCKTAIL,
    exclude: list[str] | None = None,
    fast_mode: bool = True,
) -> AnalysisOutput:
    """Run the analysis crew and return structured output.

    This function provides a simple interface for running the analysis
    workflow, handling enum-to-string conversion and default values.

    Args:
        cabinet: List of ingredient IDs available in the user's cabinet.
        mood: Description of the user's current mood or occasion.
        skill_level: User's bartending skill level. Defaults to intermediate.
        drink_type: Preferred drink type. Defaults to cocktail.
        exclude: List of drink IDs to exclude from recommendations.
            Typically the user's recent drink history.
        fast_mode: If True (default), uses single-agent mode for ~50% faster
            response. Set to False for more detailed two-agent analysis.

    Returns:
        AnalysisOutput containing ranked drink candidates.

    Example:
        result = run_analysis_crew(
            cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
            mood="relaxing after work",
            skill_level=SkillLevel.BEGINNER,
            drink_type=DrinkType.BOTH,
            exclude=["whiskey-sour"],
            fast_mode=True,  # Default: faster single-agent mode
        )
        for candidate in result.candidates:
            print(f"{candidate.name}: {candidate.mood_score}")
    """
    import json
    import re

    # Normalize enum values to strings for template substitution
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    # Map drink_type enum values to tool-expected format
    drink_type_map = {
        "cocktail": "cocktails",
        "mocktail": "mocktails",
        "both": "both",
    }
    drink_filter = drink_type_map.get(drink_str, drink_str)

    crew = create_analysis_crew(fast_mode=fast_mode)
    result = crew.kickoff(
        inputs={
            "cabinet": cabinet,
            "drink_type": drink_filter,
            "mood": mood,
            "skill_level": skill_str,
            "exclude": exclude or [],
        }
    )

    # Return the structured pydantic output if available
    if (
        hasattr(result, "pydantic")
        and result.pydantic
        and isinstance(result.pydantic, AnalysisOutput)
    ):
        return result.pydantic

    # Fallback: parse from raw output if pydantic output unavailable
    try:
        json_match = re.search(r"\{[\s\S]*\}", str(result))
        if json_match:
            data = json.loads(json_match.group())
            return AnalysisOutput(**data)
    except (json.JSONDecodeError, ValueError):
        pass

    # Return empty result if parsing fails
    return AnalysisOutput(candidates=[], total_found=0, mood_summary="")
