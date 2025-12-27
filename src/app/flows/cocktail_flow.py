"""CocktailFlow - Main orchestration flow for cocktail recommendations.

This flow coordinates the Analysis and Recipe crews to deliver complete
cocktail recommendations based on user preferences, cabinet contents,
and current mood.

Flow Architecture:
    1. receive_input: Entry point, validates and normalizes input
    2. analyze: Runs Analysis Crew (Cabinet Analyst -> Mood Matcher)
    3. generate_recipe: Runs Recipe Crew (Recipe Writer -> Bottle Advisor)

The flow maintains state across steps and supports the "another" workflow
where users can reject a recommendation and get a new one (rejected drinks
are excluded from subsequent analysis).
"""

import logging
import uuid
from typing import Any

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from src.app.crews.analysis_crew import create_analysis_crew
from src.app.crews.recipe_crew import create_recipe_crew
from src.app.models import DrinkType, SkillLevel

logger = logging.getLogger(__name__)


class CocktailFlowState(BaseModel):
    """State container for the cocktail recommendation flow.

    This state is passed between flow steps and maintains all context
    needed for the recommendation pipeline.

    Attributes:
        session_id: Unique identifier for this flow session.
        cabinet: List of ingredient IDs available in the user's cabinet.
        mood: Description of the user's current mood or occasion.
        constraints: Optional list of constraints (e.g., "not too sweet").
        drink_type: Preferred drink type (cocktail/mocktail/both).
        skill_level: User's bartending skill level.
        recent_history: List of drink IDs to exclude (recently made).
        candidates: List of candidate drinks from analysis phase.
        selected: ID of the selected drink for recipe generation.
        recipe: Generated recipe data from Recipe Crew.
        next_bottle: Bottle recommendation from Recipe Crew.
        rejected: List of drink IDs rejected in this session.
        error: Error message if something went wrong.
        analysis_raw: Raw output from Analysis Crew (for debugging).
        recipe_raw: Raw output from Recipe Crew (for debugging).
    """

    # Session identification
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this flow session",
    )

    # User input
    cabinet: list[str] = Field(
        default_factory=list,
        description="List of ingredient IDs available in the user's cabinet",
    )
    mood: str = Field(
        default="",
        description="Description of the user's current mood or occasion",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Optional constraints like 'not too sweet'",
    )
    drink_type: str = Field(
        default="cocktail",
        description="Preferred drink type: 'cocktail', 'mocktail', or 'both'",
    )
    skill_level: str = Field(
        default="intermediate",
        description="User's skill level: 'beginner', 'intermediate', or 'adventurous'",
    )
    recent_history: list[str] = Field(
        default_factory=list,
        description="List of drink IDs recently made (to exclude from recommendations)",
    )

    # Analysis output
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate drinks from analysis phase with mood scores",
    )
    selected: str | None = Field(
        default=None,
        description="ID of the drink selected for recipe generation",
    )

    # Recipe output
    recipe: dict[str, Any] | None = Field(
        default=None,
        description="Generated recipe data from Recipe Crew",
    )
    next_bottle: dict[str, Any] | None = Field(
        default=None,
        description="Bottle recommendation from Recipe Crew",
    )

    # Session memory (for "show me another" workflow)
    rejected: list[str] = Field(
        default_factory=list,
        description="Drinks rejected in this session via 'show me another'",
    )

    # Error handling
    error: str | None = Field(
        default=None,
        description="Error message if something went wrong",
    )

    # Raw outputs for debugging
    analysis_raw: str | None = Field(
        default=None,
        description="Raw output from Analysis Crew",
    )
    recipe_raw: str | None = Field(
        default=None,
        description="Raw output from Recipe Crew",
    )


class CocktailFlow(Flow[CocktailFlowState]):
    """Main orchestration flow for cocktail recommendations.

    This flow coordinates the recommendation pipeline:
    1. Validates user input (cabinet, mood, preferences)
    2. Runs Analysis Crew to find and rank suitable drinks
    3. Runs Recipe Crew to generate detailed recipe and bottle advice

    The flow supports the "another" workflow where users can reject
    a recommendation. Rejected drinks are added to the exclusion list
    and a new recommendation is generated.

    Example:
        >>> flow = CocktailFlow()
        >>> result = flow.kickoff(inputs={
        ...     "cabinet": ["bourbon", "lemons", "honey"],
        ...     "mood": "unwinding after a long week",
        ...     "skill_level": "intermediate",
        ...     "drink_type": "cocktail",
        ... })
        >>> print(result.state.recipe)

    Another Example (rejection workflow):
        >>> # User doesn't like the first recommendation
        >>> flow.state.rejected.append(flow.state.selected)
        >>> flow.state.selected = None
        >>> flow.state.candidates = []
        >>> # Re-run from analyze step
        >>> flow.analyze()
        >>> flow.generate_recipe()
    """

    @start()
    def receive_input(self) -> CocktailFlowState:
        """Entry point: validate and normalize user input.

        This method is the flow entry point. It validates the incoming
        state, normalizes enum values, and prepares for the analysis phase.

        Returns:
            The validated and normalized flow state.

        Raises:
            ValueError: If cabinet is empty (no ingredients available).
        """
        logger.info(
            f"Flow started: session={self.state.session_id}, "
            f"cabinet_size={len(self.state.cabinet)}, "
            f"mood='{self.state.mood[:50]}...'"
        )

        # Validate cabinet is not empty
        if not self.state.cabinet:
            self.state.error = (
                "Cabinet is empty. Please add some ingredients to get recommendations."
            )
            logger.warning(f"Empty cabinet for session {self.state.session_id}")
            return self.state

        # Normalize drink_type to valid enum value
        drink_type_str = self.state.drink_type.lower()
        if drink_type_str not in ("cocktail", "mocktail", "both"):
            logger.warning(
                f"Invalid drink_type '{self.state.drink_type}', defaulting to 'cocktail'"
            )
            self.state.drink_type = "cocktail"

        # Normalize skill_level to valid enum value
        skill_str = self.state.skill_level.lower()
        if skill_str not in ("beginner", "intermediate", "adventurous"):
            logger.warning(
                f"Invalid skill_level '{self.state.skill_level}', "
                "defaulting to 'intermediate'"
            )
            self.state.skill_level = "intermediate"

        # Normalize cabinet ingredient names (lowercase, strip whitespace)
        self.state.cabinet = [
            ingredient.lower().strip() for ingredient in self.state.cabinet
        ]

        # Provide default mood if not specified
        if not self.state.mood:
            self.state.mood = "something refreshing"
            logger.debug("No mood specified, using default")

        logger.info(
            f"Input validated: {len(self.state.cabinet)} ingredients, "
            f"drink_type={self.state.drink_type}, skill={self.state.skill_level}"
        )

        return self.state

    @listen(receive_input)
    def analyze(self) -> CocktailFlowState:
        """Run Analysis Crew to find and rank suitable drinks.

        This step creates and kicks off the Analysis Crew which:
        1. Uses Cabinet Analyst to find drinks makeable from cabinet
        2. Uses Mood Matcher to rank drinks by mood fit

        The crew excludes both recently made drinks (recent_history)
        and drinks rejected in this session (rejected).

        Returns:
            Updated state with candidates and selected drink ID.
        """
        # Skip if there was an error in the previous step
        if self.state.error:
            logger.warning(f"Skipping analyze due to error: {self.state.error}")
            return self.state

        logger.info(f"Starting analysis for session {self.state.session_id}")

        # Build exclusion list: recent history + rejected in this session
        exclude_list = list(set(self.state.recent_history + self.state.rejected))

        # Map drink_type to RecipeDBTool format
        # RecipeDBTool expects: "cocktails", "mocktails", or "both"
        drink_type_map = {
            "cocktail": "cocktails",
            "mocktail": "mocktails",
            "both": "both",
        }
        db_drink_type = drink_type_map.get(self.state.drink_type, "cocktails")

        try:
            # Create and run the Analysis Crew
            analysis_crew = create_analysis_crew()
            result = analysis_crew.kickoff(
                inputs={
                    "cabinet": self.state.cabinet,
                    "drink_type": db_drink_type,
                    "mood": self.state.mood,
                    "skill_level": self.state.skill_level,
                    "exclude": exclude_list,
                }
            )

            # Store raw output for debugging
            self.state.analysis_raw = str(result)

            # Parse candidates from crew output
            # The Analysis Crew returns ranked drinks from Mood Matcher
            candidates = self._parse_analysis_result(str(result))
            self.state.candidates = candidates

            # Select the top candidate (if any)
            if candidates:
                self.state.selected = candidates[0].get("id")
                logger.info(
                    f"Analysis complete: {len(candidates)} candidates, "
                    f"selected={self.state.selected}"
                )
            else:
                self.state.error = (
                    "No drinks can be made with your current cabinet. "
                    "Try adding more ingredients."
                )
                logger.warning(
                    f"No candidates found for session {self.state.session_id}"
                )

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            self.state.error = f"Analysis failed: {str(e)}"

        return self.state

    @listen(analyze)
    def generate_recipe(self) -> CocktailFlowState:
        """Run Recipe Crew to generate detailed recipe and bottle advice.

        This step creates and kicks off the Recipe Crew which:
        1. Uses Recipe Writer to generate a skill-appropriate recipe
        2. Uses Bottle Advisor to recommend next bottle purchases

        Prerequisites:
            - A drink must be selected (self.state.selected is not None)
            - No errors from previous steps

        Returns:
            Updated state with recipe and next_bottle data.
        """
        # Skip if there was an error or no selection
        if self.state.error:
            logger.warning(f"Skipping recipe due to error: {self.state.error}")
            return self.state

        if not self.state.selected:
            logger.warning("No drink selected, skipping recipe generation")
            self.state.error = "No drink selected for recipe generation."
            return self.state

        logger.info(
            f"Generating recipe for '{self.state.selected}' "
            f"(session {self.state.session_id})"
        )

        try:
            # Create and run the Recipe Crew
            recipe_crew = create_recipe_crew()
            result = recipe_crew.kickoff(
                inputs={
                    "cocktail_id": self.state.selected,
                    "skill_level": self.state.skill_level,
                    "cabinet": self.state.cabinet,
                    "drink_type": self.state.drink_type,
                }
            )

            # Store raw output for debugging
            self.state.recipe_raw = str(result)

            # Parse recipe and bottle recommendation from crew output
            parsed = self._parse_recipe_result(str(result))
            self.state.recipe = parsed.get("recipe")
            self.state.next_bottle = parsed.get("next_bottle")

            logger.info(
                f"Recipe generated for '{self.state.selected}', "
                f"next_bottle={self.state.next_bottle.get('ingredient') if self.state.next_bottle else 'none'}"
            )

        except Exception as e:
            logger.error(f"Recipe generation failed: {e}", exc_info=True)
            self.state.error = f"Recipe generation failed: {str(e)}"

        return self.state

    def _parse_analysis_result(self, raw_output: str) -> list[dict[str, Any]]:
        """Parse Analysis Crew output into structured candidate list.

        The Analysis Crew (via Mood Matcher) returns ranked drinks.
        This method extracts the structured data from the raw output.

        Args:
            raw_output: Raw string output from the Analysis Crew.

        Returns:
            List of candidate drink dictionaries with mood scores.
        """
        # For MVP, we return a simplified structure
        # In production, this would parse the actual JSON from the crew output
        import json
        import re

        candidates = []

        # Try to extract JSON from the output
        try:
            # Look for JSON array in the output
            json_match = re.search(r"\[[\s\S]*\]", raw_output)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    candidates = parsed
        except json.JSONDecodeError:
            logger.debug("Could not parse JSON from analysis output, using fallback")

        # If no JSON found, try to extract drink IDs from text
        if not candidates:
            # Look for patterns like "id: drink-name" or "drink-name (score: 85)"
            id_pattern = r'"?id"?\s*:\s*"?([a-z0-9-]+)"?'
            ids = re.findall(id_pattern, raw_output.lower())
            for drink_id in ids[:5]:  # Limit to top 5
                candidates.append(
                    {
                        "id": drink_id,
                        "name": drink_id.replace("-", " ").title(),
                        "mood_score": 80,  # Default score
                        "recommended": True,
                    }
                )

        return candidates

    def _parse_recipe_result(self, raw_output: str) -> dict[str, Any]:
        """Parse Recipe Crew output into recipe and bottle recommendation.

        The Recipe Crew returns a detailed recipe and bottle advice.
        This method extracts the structured data from the raw output.

        Args:
            raw_output: Raw string output from the Recipe Crew.

        Returns:
            Dictionary with 'recipe' and 'next_bottle' keys.
        """
        import json
        import re

        result: dict[str, Any] = {"recipe": None, "next_bottle": None}

        # Try to extract JSON objects from the output
        try:
            # Look for recipe-like JSON
            recipe_match = re.search(r'\{[^{}]*"name"[^{}]*\}', raw_output)
            if recipe_match:
                result["recipe"] = json.loads(recipe_match.group())
        except json.JSONDecodeError:
            logger.debug("Could not parse recipe JSON, storing raw output")

        # Store raw output as recipe content if no JSON found
        if not result["recipe"]:
            result["recipe"] = {
                "raw_content": raw_output,
                "id": self.state.selected,
            }

        # Try to extract bottle recommendation
        try:
            bottle_match = re.search(
                r'"?ingredient"?\s*:\s*"?([a-z0-9-]+)"?.*?' r'"?unlocks"?\s*:\s*(\d+)',
                raw_output.lower(),
            )
            if bottle_match:
                result["next_bottle"] = {
                    "ingredient": bottle_match.group(1),
                    "unlocks": int(bottle_match.group(2)),
                }
        except (ValueError, AttributeError):
            logger.debug("Could not parse bottle recommendation")

        return result


async def run_cocktail_flow(
    cabinet: list[str],
    mood: str,
    skill_level: SkillLevel | str = SkillLevel.INTERMEDIATE,
    drink_type: DrinkType | str = DrinkType.COCKTAIL,
    recent_history: list[str] | None = None,
    constraints: list[str] | None = None,
) -> CocktailFlowState:
    """Convenience function to run the complete cocktail recommendation flow.

    This function creates a CocktailFlow, initializes it with the provided
    inputs, and runs all steps to completion. Uses async kickoff to work
    properly with FastAPI's event loop.

    Args:
        cabinet: List of ingredient IDs available in the user's cabinet.
        mood: Description of the user's current mood or occasion.
        skill_level: User's bartending skill level.
        drink_type: Preferred drink type (cocktail/mocktail/both).
        recent_history: List of drink IDs to exclude (recently made).
        constraints: Optional constraints (e.g., "not too sweet").

    Returns:
        The final CocktailFlowState with recipe and recommendations.

    Example:
        >>> state = await run_cocktail_flow(
        ...     cabinet=["bourbon", "lemons", "honey", "angostura-bitters"],
        ...     mood="unwinding after a long week",
        ...     skill_level=SkillLevel.INTERMEDIATE,
        ...     drink_type=DrinkType.COCKTAIL,
        ...     recent_history=["old-fashioned"],
        ... )
        >>> if not state.error:
        ...     print(f"Recommended: {state.selected}")
        ...     print(f"Recipe: {state.recipe}")
    """
    # Normalize enum values to strings
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    # Create the flow and run with inputs using async kickoff
    # CrewAI Flow populates state from inputs dict
    flow = CocktailFlow()
    await flow.kickoff_async(
        inputs={
            "cabinet": cabinet,
            "mood": mood,
            "skill_level": skill_str,
            "drink_type": drink_str,
            "recent_history": recent_history or [],
            "constraints": constraints or [],
        }
    )

    return flow.state


async def request_another(flow_state: CocktailFlowState) -> CocktailFlowState:
    """Request another recommendation, excluding the previously selected drink.

    This function implements the "show me something else" workflow. It takes
    an existing flow state, adds the currently selected drink to the rejected
    list, and re-runs the analysis and recipe generation to find a new drink.
    Uses async kickoff to work properly with FastAPI's event loop.

    Args:
        flow_state: The current flow state with a selected drink.

    Returns:
        Updated flow state with a new recommendation.

    Example:
        >>> state = await run_cocktail_flow(cabinet=["gin", "vermouth"], mood="fancy")
        >>> if state.selected == "martini" and user_says_another:
        ...     state = await request_another(state)
        ...     print(f"New recommendation: {state.selected}")
    """
    if not flow_state.selected:
        logger.warning("Cannot request another: no drink currently selected")
        return flow_state

    # Build updated rejected list with current selection
    updated_rejected = list(flow_state.rejected) + [flow_state.selected]
    logger.info(
        f"Rejecting '{flow_state.selected}', total rejected: {len(updated_rejected)}"
    )

    # Create a new flow and run with updated inputs using async kickoff
    # This preserves the original inputs but adds the rejected drink
    flow = CocktailFlow()
    await flow.kickoff_async(
        inputs={
            "session_id": flow_state.session_id,
            "cabinet": flow_state.cabinet,
            "mood": flow_state.mood,
            "skill_level": flow_state.skill_level,
            "drink_type": flow_state.drink_type,
            "recent_history": flow_state.recent_history,
            "constraints": flow_state.constraints,
            "rejected": updated_rejected,
        }
    )

    return flow.state
