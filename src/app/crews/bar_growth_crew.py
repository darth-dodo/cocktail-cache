"""Bar Growth Crew for strategic bottle purchase recommendations.

This crew provides personalized bar growth advice using pre-computed
data about makeable drinks and bottle unlock potential.

Uses structured Pydantic models for reliable, typed outputs.
"""

import logging
import time

from crewai import Crew, Process, Task

from src.app.agents.bar_growth_advisor import create_bar_growth_advisor
from src.app.models.crew_io import BarGrowthOutput, BarGrowthRecommendation
from src.app.utils.parsing import parse_json_from_llm_output

logger = logging.getLogger(__name__)


def create_bar_growth_crew() -> Crew:
    """Create the Bar Growth Crew for bottle recommendations.

    The crew uses a single Bar Growth Advisor agent that receives
    pre-computed data about the user's cabinet, makeable drinks,
    and bottle rankings.

    Returns:
        A configured CrewAI Crew instance ready for execution.

    Example:
        crew = create_bar_growth_crew()
        result = crew.kickoff(inputs={
            "cabinet_contents": "Bourbon, Gin, Sweet Vermouth",
            "makeable_drinks": "Old Fashioned, Martini, Manhattan...",
            "ranked_bottles": "1. Vodka (+8), 2. Rum (+6)...",
            "essentials_status": "Missing: Angostura bitters (used in 15 drinks)",
        })
    """
    logger.info("Creating bar growth crew")

    # Create agent without tools - data is injected directly into prompts
    bar_growth_advisor = create_bar_growth_advisor(tools=[])

    # Single task for bar growth advice
    advise_task = Task(
        description=(
            "Provide strategic bar growth advice based on the user's current cabinet "
            "and what bottles would unlock the most new drink possibilities.\n\n"
            "CURRENT BAR STATUS:\n"
            "{cabinet_contents}\n\n"
            "DRINKS YOU CAN MAKE (Core Bottles Only - Kitchen items assumed available):\n"
            "{makeable_drinks}\n\n"
            "BOTTLE RANKINGS (by unlock potential):\n"
            "{ranked_bottles}\n\n"
            "ESSENTIALS STATUS (Bitters & Specialty Syrups):\n"
            "{essentials_status}\n\n"
            "IMPORTANT PHILOSOPHY:\n"
            "- We track CORE BOTTLES: spirits, modifiers, non-alcoholic spirits\n"
            "- We ASSUME kitchen items (fresh produce, mixers) are available\n"
            "- Essentials (bitters, specialty syrups) are nice-to-haves, not requirements\n"
            "- Focus recommendations on bottles that unlock the MOST new drinks\n\n"
            "Instructions:\n"
            "1. Analyze the user's current bar and identify their strongest categories\n"
            "2. Look at the ranked bottles and identify the #1 best purchase\n"
            "3. Provide 2-3 additional recommendations as alternatives\n"
            "4. If they're missing key essentials (like Angostura bitters), mention it\n"
            "5. Give encouraging advice about what milestone they're building toward\n"
            "   (e.g., 'You're 2 bottles away from mastering the classics!')\n\n"
            "Be conversational, encouraging, and specific. Reference actual drink names "
            "they'll be able to make. Make building a home bar feel achievable!\n\n"
            "IMPORTANT: Return the result as a valid JSON object matching the "
            "BarGrowthOutput schema."
        ),
        expected_output=(
            "A JSON object with structure:\n"
            "{\n"
            '  "summary": "Personalized overview of their bar and growth path",\n'
            '  "top_recommendation": {\n'
            '    "ingredient_id": "ingredient-id",\n'
            '    "name": "Ingredient Name",\n'
            '    "unlocks": 5,\n'
            '    "reasoning": "Why this is THE bottle to buy next",\n'
            '    "signature_drinks": ["Classic Drink 1", "Classic Drink 2"]\n'
            "  },\n"
            '  "additional_recommendations": [\n'
            "    {\n"
            '      "ingredient_id": "ingredient-id-2",\n'
            '      "name": "Alternative Ingredient",\n'
            '      "unlocks": 3,\n'
            '      "reasoning": "Why this is also a good choice",\n'
            '      "signature_drinks": ["Other Drink"]\n'
            "    }\n"
            "  ],\n"
            '  "essentials_note": "Optional note about missing bitters/syrups",\n'
            '  "next_milestone": "Encouraging message about their progress"\n'
            "}"
        ),
        agent=bar_growth_advisor,
        output_pydantic=BarGrowthOutput,
    )

    return Crew(
        agents=[bar_growth_advisor],
        tasks=[advise_task],
        process=Process.sequential,
        verbose=False,
    )


async def run_bar_growth_crew(
    cabinet_contents: str,
    makeable_drinks: str,
    ranked_bottles: str,
    essentials_status: str,
) -> BarGrowthOutput:
    """Run the bar growth crew and return structured output.

    This function provides a simple interface for running the bar growth
    workflow, handling pre-computed data injection and output parsing.

    Uses native async execution via CrewAI's akickoff() for better
    concurrency without thread pool overhead.

    Args:
        cabinet_contents: Formatted string of user's current bottles.
        makeable_drinks: Formatted string of drinks user can make.
        ranked_bottles: Formatted string ranking bottles by unlock potential.
        essentials_status: Formatted string about missing essentials.

    Returns:
        BarGrowthOutput containing personalized recommendations.

    Example:
        result = await run_bar_growth_crew(
            cabinet_contents="Bourbon, Gin, Sweet Vermouth (3 bottles)",
            makeable_drinks="You can make 12 drinks: Old Fashioned, Martini...",
            ranked_bottles="1. Vodka: +8 drinks (Moscow Mule, Cosmopolitan...)",
            essentials_status="Missing: Angostura bitters (used in 15 drinks)",
        )
        print(result.summary)
        print(result.top_recommendation.name)
    """
    start_time = time.perf_counter()
    logger.info(f"run_bar_growth_crew started: cabinet={cabinet_contents[:50]}...")

    crew = create_bar_growth_crew()

    result = await crew.akickoff(
        inputs={
            "cabinet_contents": cabinet_contents,
            "makeable_drinks": makeable_drinks,
            "ranked_bottles": ranked_bottles,
            "essentials_status": essentials_status,
        }
    )
    # Return the structured pydantic output if available
    if (
        hasattr(result, "pydantic")
        and result.pydantic
        and isinstance(result.pydantic, BarGrowthOutput)
    ):
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"run_bar_growth_crew completed in {total_elapsed_ms:.2f}ms")
        return result.pydantic

    # Fallback: parse from raw output if pydantic output unavailable
    logger.warning("Pydantic output unavailable, attempting to parse from raw output")
    parsed_output = parse_json_from_llm_output(
        str(result), BarGrowthOutput, logger, "bar growth output"
    )
    if parsed_output:
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"run_bar_growth_crew completed (fallback parse) in {total_elapsed_ms:.2f}ms"
        )
        return parsed_output

    # Return fallback result if parsing fails
    total_elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.error(
        f"run_bar_growth_crew failed after {total_elapsed_ms:.2f}ms, returning fallback"
    )
    return BarGrowthOutput(
        summary="Unable to generate personalized recommendations at this time.",
        top_recommendation=BarGrowthRecommendation(
            ingredient_id="unknown",
            name="Unknown",
            unlocks=0,
            reasoning="Please try again later.",
            signature_drinks=[],
        ),
        additional_recommendations=[],
        essentials_note=None,
        next_milestone="Keep building your bar!",
    )
