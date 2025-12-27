"""Analysis Crew for cocktail recommendations.

This crew chains the Cabinet Analyst and Mood Matcher agents to:
1. Find drinks makeable from the user's cabinet
2. Rank those drinks by mood fit

The crew accepts user preferences including drink type, mood, skill level,
and a list of recent drinks to exclude from recommendations.
"""

from crewai import Crew, Process, Task

from src.app.agents import create_cabinet_analyst, create_mood_matcher
from src.app.models import DrinkType, SkillLevel
from src.app.tools import FlavorProfilerTool, RecipeDBTool


def create_analysis_crew() -> Crew:
    """Create the Analysis Crew that chains Cabinet Analyst -> Mood Matcher.

    This crew performs the first two stages of the cocktail recommendation
    pipeline:

    1. Cabinet Analyst: Uses RecipeDBTool to search the recipe database
       and identify all drinks makeable with the user's available ingredients.

    2. Mood Matcher: Uses FlavorProfilerTool to analyze flavor profiles
       and rank the candidate drinks by mood fit, considering skill level
       and excluding recently made drinks.

    The crew expects the following inputs when kicked off:
        - cabinet: List of ingredient IDs the user has available
        - drink_type: 'cocktails', 'mocktails', or 'both'
        - mood: Description of the user's current mood/occasion
        - skill_level: 'beginner', 'intermediate', or 'adventurous'
        - exclude: List of drink IDs to exclude (recent history)

    Returns:
        A configured Crew instance ready to be kicked off with inputs.

    Example:
        crew = create_analysis_crew()
        result = crew.kickoff(inputs={
            "cabinet": ["bourbon", "lemons", "honey", "simple-syrup"],
            "drink_type": "cocktails",
            "mood": "unwinding after a long week",
            "skill_level": "intermediate",
            "exclude": ["whiskey-sour", "old-fashioned"]
        })
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
            "- difficulty: Skill level required\n"
            "- timing_minutes: Preparation time\n"
            "- tags: Flavor and style tags\n"
            "- is_mocktail: Whether it's a mocktail"
        ),
        agent=cabinet_analyst,
    )

    # Task 2: Rank drinks by mood fit
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
            "Rank the remaining drinks from best to worst mood fit."
        ),
        expected_output=(
            "A ranked JSON list of drinks ordered by mood fit, each containing:\n"
            "- id: The drink identifier\n"
            "- name: The drink name\n"
            "- mood_score: How well it matches the mood (0-100)\n"
            "- mood_reasoning: Brief explanation of why it fits the mood\n"
            "- flavor_profile: The sweet/sour/bitter/spirit values\n"
            "- recommended: Boolean indicating if it's a top recommendation"
        ),
        agent=mood_matcher,
        context=[analyze_task],  # Receives output from cabinet analyst
    )

    # Create and return the crew with sequential processing
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
) -> str:
    """Convenience function to create and run the analysis crew.

    This function provides a simple interface for running the analysis
    workflow, handling enum-to-string conversion and default values.

    Args:
        cabinet: List of ingredient IDs available in the user's cabinet.
        mood: Description of the user's current mood or occasion.
        skill_level: User's bartending skill level. Defaults to intermediate.
        drink_type: Preferred drink type. Defaults to cocktail.
        exclude: List of drink IDs to exclude from recommendations.
            Typically the user's recent drink history.

    Returns:
        The crew's output as a string containing ranked drink recommendations.

    Example:
        result = run_analysis_crew(
            cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
            mood="relaxing after work",
            skill_level=SkillLevel.BEGINNER,
            drink_type=DrinkType.BOTH,
            exclude=["whiskey-sour"],
        )
    """
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

    crew = create_analysis_crew()
    result = crew.kickoff(
        inputs={
            "cabinet": cabinet,
            "drink_type": drink_filter,
            "mood": mood,
            "skill_level": skill_str,
            "exclude": exclude or [],
        }
    )

    return str(result)
