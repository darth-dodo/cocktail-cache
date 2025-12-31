"""Analysis Crew for cocktail recommendations.

This crew analyzes the user's cabinet and mood to find and rank suitable drinks.

Supports two modes:
- Fast mode (default): Single agent, single LLM call (~50% faster)
- Full mode: Two agents for detailed analysis (Cabinet Analyst → Mood Matcher)

The crew uses structured Pydantic models for inputs and outputs,
ensuring reliable, typed data flow through the AI pipeline.
"""

import logging
import time

from crewai import Crew, Process, Task

from src.app.agents import (
    create_cabinet_analyst,
    create_drink_recommender,
    create_mood_matcher,
)
from src.app.models import AnalysisOutput, DrinkType, SkillLevel
from src.app.services.drink_data import (
    DrinkTypeFilter,
    format_drinks_for_prompt,
    get_makeable_drinks,
)
from src.app.utils.parsing import parse_json_from_llm_output

logger = logging.getLogger(__name__)


def create_analysis_crew(fast_mode: bool = True) -> Crew:
    """Create the Analysis Crew for finding and ranking drinks.

    Args:
        fast_mode: If True (default), uses a single unified agent for faster
            response. If False, uses two sequential agents for more detailed
            analysis.

    The crew expects the following inputs when kicked off:
        - mood: Description of the user's current mood/occasion
        - skill_level: 'beginner', 'intermediate', or 'adventurous'
        - available_drinks: Pre-formatted string of makeable drinks
            (use format_drinks_for_prompt() to generate this)

    Note: Agents do not use tools. Drink data is pre-computed and injected
    directly into the prompts via the available_drinks input. Use
    run_analysis_crew() which handles the data pre-computation automatically.

    Returns:
        A configured Crew instance ready to be kicked off with inputs.
        The output will be structured as AnalysisOutput Pydantic model.

    Example:
        # Preferred: use run_analysis_crew() which handles data injection
        result = run_analysis_crew(
            cabinet=["bourbon", "lemons", "honey"],
            mood="relaxing",
            skill_level="intermediate",
        )

        # Or manually inject data:
        drinks = get_makeable_drinks(cabinet, "cocktails", exclude)
        crew = create_analysis_crew(fast_mode=True)
        result = crew.kickoff(inputs={
            "mood": "unwinding after a long week",
            "skill_level": "intermediate",
            "available_drinks": format_drinks_for_prompt(drinks),
        })
    """
    logger.info(f"Creating analysis crew with fast_mode={fast_mode}")

    if fast_mode:
        crew = _create_fast_crew()
    else:
        crew = _create_full_crew()

    return crew


def _create_fast_crew() -> Crew:
    """Create a single-agent crew for fast analysis.

    Uses one unified Drink Recommender agent without tools,
    receiving pre-computed drink data directly in the prompt.
    """
    # Create unified agent without tools - data is pre-computed and injected
    drink_recommender = create_drink_recommender(tools=[])

    # Single task that does everything - drink data is injected via {available_drinks}
    unified_task = Task(
        description=(
            "Find and rank the best drinks for the user based on their cabinet and mood.\n\n"
            "User's mood: {mood}\n"
            "Skill level: {skill_level}\n\n"
            "AVAILABLE DRINKS (pre-computed from cabinet, already filtered and excludes applied):\n"
            "{available_drinks}\n\n"
            "Instructions:\n"
            "1. Review the available drinks listed above\n"
            "2. Rank drinks by mood fit using the flavor profiles provided:\n"
            "   - Relaxing moods -> spirit-forward, balanced drinks (higher spirit values)\n"
            "   - Celebratory moods -> refreshing, bright drinks (higher sour, lower spirit)\n"
            "   - Contemplative moods -> complex, layered drinks (balanced profiles)\n"
            "3. Consider skill level when ranking (beginners need simpler drinks)\n"
            "4. Return the top 5 ranked drinks\n\n"
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

    Uses Cabinet Analyst -> Mood Matcher for more thorough analysis,
    but requires two LLM calls. Both agents receive pre-computed data
    instead of using tools.
    """
    # Create agents without tools - data is pre-computed and injected
    cabinet_analyst = create_cabinet_analyst(tools=[])
    mood_matcher = create_mood_matcher(tools=[])

    # Task 1: Analyze cabinet contents and find makeable drinks
    # Drink data is injected via {available_drinks}
    analyze_task = Task(
        description=(
            "Analyze the available drinks and identify the best candidates.\n\n"
            "AVAILABLE DRINKS (pre-computed from cabinet, already filtered):\n"
            "{available_drinks}\n\n"
            "Review the drinks listed above and summarize their key characteristics. "
            "Return all drinks with their details (name, difficulty, timing, tags, "
            "flavor profiles) for the next agent to rank by mood."
        ),
        expected_output=(
            "A JSON list of makeable drinks, each containing:\n"
            "- id: The drink identifier\n"
            "- name: The drink name\n"
            "- tagline: Brief description\n"
            "- difficulty: Skill level required (easy, medium, hard, advanced)\n"
            "- timing_minutes: Preparation time as integer\n"
            "- tags: Flavor and style tags as list\n"
            "- is_mocktail: Boolean whether it's a mocktail\n"
            "- flavor_profile: The flavor characteristics"
        ),
        agent=cabinet_analyst,
    )

    # Task 2: Rank drinks by mood fit - outputs structured AnalysisOutput
    match_task = Task(
        description=(
            "Rank the candidate drinks by how well they match the user's mood "
            "and preferences.\n\n"
            "User's mood: {mood}\n"
            "Skill level: {skill_level}\n\n"
            "Use the flavor profiles provided in the previous analysis to rank "
            "the drinks. Consider:\n\n"
            "1. Mood alignment: Match drink characteristics to the stated mood\n"
            "   - Relaxing moods pair well with spirit-forward, balanced drinks\n"
            "   - Celebratory moods pair well with refreshing, bright drinks\n"
            "   - Contemplative moods pair well with complex, layered drinks\n\n"
            "2. Skill appropriateness: Beginners need simpler techniques;\n"
            "   adventurous users can handle complex preparations\n\n"
            "Rank the drinks from best to worst mood fit.\n\n"
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

    Pre-computes drink data and injects it directly into agent prompts,
    eliminating tool call latency.

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
    start_time = time.perf_counter()
    logger.info(
        f"run_analysis_crew started: mood='{mood}', skill_level={skill_level}, "
        f"drink_type={drink_type}, cabinet_size={len(cabinet)}, "
        f"exclude_count={len(exclude or [])}, fast_mode={fast_mode}"
    )

    # Normalize enum values to strings for template substitution
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    # Map drink_type enum values to data service format
    drink_type_map: dict[str, DrinkTypeFilter] = {
        "cocktail": "cocktails",
        "mocktail": "mocktails",
        "both": "both",
    }
    drink_filter: DrinkTypeFilter = drink_type_map.get(drink_str, "both")

    # Pre-compute drink data to inject into prompts (eliminates tool calls)
    data_start = time.perf_counter()
    makeable_drinks = get_makeable_drinks(
        cabinet=cabinet,
        drink_type=drink_filter,
        exclude=exclude,
    )
    available_drinks_text = format_drinks_for_prompt(makeable_drinks)
    data_elapsed_ms = (time.perf_counter() - data_start) * 1000

    crew = create_analysis_crew(fast_mode=fast_mode)

    crew_start = time.perf_counter()
    result = crew.kickoff(
        inputs={
            "cabinet": cabinet,
            "drink_type": drink_filter,
            "mood": mood,
            "skill_level": skill_str,
            "exclude": exclude or [],
            "available_drinks": available_drinks_text,
        }
    )
    crew_elapsed_ms = (time.perf_counter() - crew_start) * 1000

    # Return the structured pydantic output if available
    if (
        hasattr(result, "pydantic")
        and result.pydantic
        and isinstance(result.pydantic, AnalysisOutput)
    ):
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"run_analysis_crew completed: {len(result.pydantic.candidates)} candidates "
            f"found in {total_elapsed_ms:.2f}ms (data: {data_elapsed_ms:.2f}ms, crew: {crew_elapsed_ms:.2f}ms)"
        )
        return result.pydantic

    # Fallback: parse from raw output if pydantic output unavailable
    logger.warning("Pydantic output unavailable, attempting to parse from raw output")
    parsed_output = parse_json_from_llm_output(
        str(result), AnalysisOutput, logger, "analysis output"
    )
    if parsed_output:
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"run_analysis_crew completed (fallback parse): {len(parsed_output.candidates)} candidates "
            f"found in {total_elapsed_ms:.2f}ms"
        )
        return parsed_output

    # Return empty result if parsing fails
    total_elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.error(
        f"run_analysis_crew failed after {total_elapsed_ms:.2f}ms, returning empty result"
    )
    return AnalysisOutput(candidates=[], total_found=0, mood_summary="")
