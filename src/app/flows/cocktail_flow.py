"""CocktailFlow - Main orchestration flow for cocktail recommendations.

This flow coordinates the Analysis and Recipe crews to deliver complete
cocktail recommendations based on user preferences, cabinet contents,
and current mood.

Flow Architecture:
    1. receive_input: Entry point, validates and normalizes input
    2. analyze: Runs Analysis Crew (Cabinet Analyst -> Mood Matcher)
    3. generate_recipe: Runs Recipe Crew (Recipe Writer -> Bottle Advisor)

The flow uses structured Pydantic models for all crew I/O, ensuring
reliable, typed data throughout the recommendation pipeline.
"""

import logging
import uuid
from typing import Any

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from src.app.crews.analysis_crew import create_analysis_crew
from src.app.crews.recipe_crew import create_recipe_crew
from src.app.models import (
    AnalysisOutput,
    BottleAdvisorOutput,
    DrinkCandidate,
    DrinkType,
    RecipeOutput,
    SkillLevel,
)

logger = logging.getLogger(__name__)


class CocktailFlowState(BaseModel):
    """State container for the cocktail recommendation flow.

    This state is passed between flow steps and maintains all context
    needed for the recommendation pipeline. Uses structured Pydantic
    models for crew outputs.

    Attributes:
        session_id: Unique identifier for this flow session.
        cabinet: List of ingredient IDs available in the user's cabinet.
        mood: Description of the user's current mood or occasion.
        constraints: Optional list of constraints (e.g., "not too sweet").
        drink_type: Preferred drink type (cocktail/mocktail/both).
        skill_level: User's bartending skill level.
        recent_history: List of drink IDs to exclude (recently made).
        analysis: Structured output from Analysis Crew.
        candidates: List of candidate drinks (derived from analysis).
        selected: ID of the selected drink for recipe generation.
        recipe: Structured recipe data from Recipe Crew.
        bottle_advice: Structured bottle recommendations from Recipe Crew.
        rejected: List of drink IDs rejected in this session.
        error: Error message if something went wrong.
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
    include_bottle_advice: bool = Field(
        default=True,
        description="Whether to include bottle purchase recommendations",
    )

    # Structured Analysis output
    analysis: AnalysisOutput | None = Field(
        default=None,
        description="Structured output from Analysis Crew",
    )
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate drinks from analysis phase (for API compatibility)",
    )
    selected: str | None = Field(
        default=None,
        description="ID of the drink selected for recipe generation",
    )

    # Structured Recipe output
    recipe: RecipeOutput | None = Field(
        default=None,
        description="Structured recipe data from Recipe Crew",
    )
    bottle_advice: BottleAdvisorOutput | None = Field(
        default=None,
        description="Structured bottle recommendations from Recipe Crew",
    )

    # Legacy fields for API compatibility
    next_bottle: dict[str, Any] | None = Field(
        default=None,
        description="Bottle recommendation (legacy format for API)",
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

    All crew outputs use structured Pydantic models for type safety.

    Example:
        >>> flow = CocktailFlow()
        >>> result = await flow.kickoff_async(inputs={
        ...     "cabinet": ["bourbon", "lemons", "honey"],
        ...     "mood": "unwinding after a long week",
        ...     "skill_level": "intermediate",
        ...     "drink_type": "cocktail",
        ... })
        >>> print(result.state.recipe.name)
    """

    @start()
    def receive_input(self) -> CocktailFlowState:
        """Entry point: validate and normalize user input.

        This method is the flow entry point. It validates the incoming
        state, normalizes enum values, and prepares for the analysis phase.

        Returns:
            The validated and normalized flow state.
        """
        logger.info(
            f"Flow started: session={self.state.session_id}, "
            f"cabinet_size={len(self.state.cabinet)}, "
            f"mood='{self.state.mood[:50] if self.state.mood else ''}...'"
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

        The crew returns structured AnalysisOutput with typed candidates.

        Returns:
            Updated state with analysis results and selected drink ID.
        """
        # Skip if there was an error in the previous step
        if self.state.error:
            logger.warning(f"Skipping analyze due to error: {self.state.error}")
            return self.state

        logger.info(f"Starting analysis for session {self.state.session_id}")

        # Build exclusion list: recent history + rejected in this session
        exclude_list = list(set(self.state.recent_history + self.state.rejected))

        # Map drink_type to RecipeDBTool format
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

            # Get structured output from crew result
            if result.pydantic and isinstance(result.pydantic, AnalysisOutput):
                self.state.analysis = result.pydantic
            else:
                # Fallback: try to parse from raw output
                self.state.analysis = self._parse_analysis_output(str(result))

            # Convert to candidate dicts for API compatibility
            if self.state.analysis and self.state.analysis.candidates:
                self.state.candidates = [
                    candidate.model_dump()
                    for candidate in self.state.analysis.candidates
                ]
                # Select the top candidate
                self.state.selected = self.state.analysis.candidates[0].id
                logger.info(
                    f"Analysis complete: {len(self.state.candidates)} candidates, "
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

        The crew returns structured RecipeOutput and BottleAdvisorOutput.

        Returns:
            Updated state with recipe and bottle_advice data.
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
            recipe_crew = create_recipe_crew(
                include_bottle_advice=self.state.include_bottle_advice
            )
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
                        recipe_output = self._parse_recipe_output(
                            str(task_0), self.state.selected
                        )

                # Task 1: Bottle Advisor output (only if bottle advice was included)
                if self.state.include_bottle_advice and len(result.tasks_output) >= 2:
                    task_1 = result.tasks_output[1]
                    if hasattr(task_1, "pydantic") and isinstance(
                        task_1.pydantic, BottleAdvisorOutput
                    ):
                        bottle_output = task_1.pydantic
                    else:
                        bottle_output = self._parse_bottle_output(str(task_1))

            # Store structured outputs
            self.state.recipe = recipe_output
            self.state.bottle_advice = bottle_output

            # Create legacy format for API compatibility
            if bottle_output and bottle_output.recommendations:
                top_rec = bottle_output.recommendations[0]
                self.state.next_bottle = {
                    "ingredient": top_rec.ingredient,
                    "unlocks": top_rec.unlocks,
                    "drinks": top_rec.drinks,
                }

            logger.info(
                f"Recipe generated for '{self.state.selected}', "
                f"has_bottle_advice={bottle_output is not None}"
            )

        except Exception as e:
            logger.error(f"Recipe generation failed: {e}", exc_info=True)
            self.state.error = f"Recipe generation failed: {str(e)}"

        return self.state

    def _parse_analysis_output(self, raw_output: str) -> AnalysisOutput:
        """Parse Analysis Crew output into structured AnalysisOutput.

        Args:
            raw_output: Raw string output from the Analysis Crew.

        Returns:
            Parsed AnalysisOutput with candidates.
        """
        import json
        import re

        try:
            json_match = re.search(r"\{[\s\S]*\}", raw_output)
            if json_match:
                data = json.loads(json_match.group())
                return AnalysisOutput(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Could not parse analysis JSON: {e}")

        # Try to extract drink IDs from text as fallback
        candidates = []
        id_pattern = r'"?id"?\s*:\s*"?([a-z0-9-]+)"?'
        ids = re.findall(id_pattern, raw_output.lower())
        for drink_id in ids[:5]:
            candidates.append(
                DrinkCandidate(
                    id=drink_id,
                    name=drink_id.replace("-", " ").title(),
                    mood_score=80,
                )
            )

        return AnalysisOutput(
            candidates=candidates,
            total_found=len(candidates),
            mood_summary="",
        )

    def _parse_recipe_output(self, raw: str, cocktail_id: str) -> RecipeOutput:
        """Parse recipe output from raw text."""
        import json
        import re

        from src.app.models import FlavorProfile
        from src.app.models.recipe import RecipeIngredient, RecipeStep

        try:
            json_match = re.search(r"\{[\s\S]*\}", raw)
            if json_match:
                data = json.loads(json_match.group())
                return RecipeOutput(**data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Return default recipe with raw content in 'why' field
        return RecipeOutput(
            id=cocktail_id,
            name=cocktail_id.replace("-", " ").title(),
            tagline="A classic cocktail",
            why=raw[:500] if raw else "Selected based on your ingredients.",
            flavor_profile=FlavorProfile(sweet=30, sour=20, bitter=25, spirit=70),
            ingredients=[RecipeIngredient(amount="2", unit="oz", item="spirit")],
            method=[RecipeStep(action="Mix", detail="Combine ingredients and serve")],
            glassware="rocks",
            garnish="optional",
            timing="3 minutes",
            difficulty="easy",
        )

    def _parse_bottle_output(self, raw: str) -> BottleAdvisorOutput:
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


async def run_cocktail_flow(
    cabinet: list[str],
    mood: str,
    skill_level: SkillLevel | str = SkillLevel.INTERMEDIATE,
    drink_type: DrinkType | str = DrinkType.COCKTAIL,
    recent_history: list[str] | None = None,
    constraints: list[str] | None = None,
    include_bottle_advice: bool = True,
) -> CocktailFlowState:
    """Run the complete cocktail recommendation flow.

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
        include_bottle_advice: Whether to include bottle purchase recommendations.
            When False, skips the bottle advisor step to save processing time.
            Defaults to True.

    Returns:
        The final CocktailFlowState with structured recipe and recommendations.

    Example:
        >>> state = await run_cocktail_flow(
        ...     cabinet=["bourbon", "simple-syrup", "angostura-bitters"],
        ...     mood="relaxing evening",
        ...     skill_level=SkillLevel.INTERMEDIATE,
        ... )
        >>> if state.recipe:
        ...     print(f"Recommended: {state.recipe.name}")
        ...     for ing in state.recipe.ingredients:
        ...         print(f"  - {ing.amount} {ing.unit} {ing.item}")
    """
    # Normalize enum values to strings
    skill_str = (
        skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
    )
    drink_str = drink_type.value if isinstance(drink_type, DrinkType) else drink_type

    # Create the flow and run with inputs using async kickoff
    flow = CocktailFlow()
    await flow.kickoff_async(
        inputs={
            "cabinet": cabinet,
            "mood": mood,
            "skill_level": skill_str,
            "drink_type": drink_str,
            "recent_history": recent_history or [],
            "constraints": constraints or [],
            "include_bottle_advice": include_bottle_advice,
        }
    )

    return flow.state


async def request_another(flow_state: CocktailFlowState) -> CocktailFlowState:
    """Request another recommendation, excluding the previously selected drink.

    This function implements the "show me something else" workflow. It takes
    an existing flow state, adds the currently selected drink to the rejected
    list, and re-runs the analysis and recipe generation to find a new drink.

    Args:
        flow_state: The current flow state with a selected drink.

    Returns:
        Updated flow state with a new recommendation.

    Example:
        >>> state = await run_cocktail_flow(cabinet=["gin", "vermouth"], mood="fancy")
        >>> if state.selected == "martini" and user_says_another:
        ...     state = await request_another(state)
        ...     print(f"New recommendation: {state.recipe.name}")
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
            "include_bottle_advice": flow_state.include_bottle_advice,
        }
    )

    return flow.state
