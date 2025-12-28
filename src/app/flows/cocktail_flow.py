"""CocktailFlow - Main orchestration flow for cocktail recommendations.

This flow coordinates the Analysis and Recipe crews to deliver complete
cocktail recommendations based on user preferences, cabinet contents,
and current mood.

Flow Architecture:
    1. receive_input: Entry point, validates and normalizes input
    2. analyze: Runs Analysis Crew (Cabinet Analyst -> Mood Matcher)
    3. generate_recipe: Runs Recipe Crew (Recipe Writer -> Bottle Advisor)
       - Supports parallel execution of Recipe Writer and Bottle Advisor
         when PARALLEL_CREWS is enabled (default: True)

The flow uses structured Pydantic models for all crew I/O, ensuring
reliable, typed data throughout the recommendation pipeline.
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from src.app.config import get_settings
from src.app.crews.analysis_crew import create_analysis_crew
from src.app.crews.recipe_crew import (
    create_bottle_only_crew,
    create_recipe_crew,
    create_recipe_only_crew,
)
from src.app.models import (
    AnalysisOutput,
    BottleAdvisorOutput,
    DrinkCandidate,
    DrinkType,
    RecipeOutput,
    SkillLevel,
)
from src.app.services.drink_data import (
    DrinkTypeFilter,
    format_bottle_recommendations_for_prompt,
    format_drinks_for_prompt,
    format_recipe_for_prompt,
    get_drink_by_id,
    get_makeable_drinks,
    get_substitutions_for_ingredients,
    get_unlock_recommendations,
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

    def __init__(self) -> None:
        """Initialize the flow with tracing based on config."""
        settings = get_settings()
        super().__init__(tracing=settings.CREWAI_TRACING)

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
        drink_type_map: dict[str, DrinkTypeFilter] = {
            "cocktail": "cocktails",
            "mocktail": "mocktails",
            "both": "both",
        }
        db_drink_type: DrinkTypeFilter = drink_type_map.get(
            self.state.drink_type, "cocktails"
        )

        try:
            # Pre-compute available drinks for prompt injection
            makeable_drinks = get_makeable_drinks(
                cabinet=self.state.cabinet,
                drink_type=db_drink_type,
                exclude=exclude_list,
            )
            available_drinks_text = format_drinks_for_prompt(makeable_drinks)

            # Create and run the Analysis Crew
            analysis_crew = create_analysis_crew()
            result = analysis_crew.kickoff(
                inputs={
                    "cabinet": self.state.cabinet,
                    "drink_type": db_drink_type,
                    "mood": self.state.mood,
                    "skill_level": self.state.skill_level,
                    "exclude": exclude_list,
                    "available_drinks": available_drinks_text,
                }
            )

            # Store raw output for debugging
            self.state.analysis_raw = str(result)

            # Get structured output from crew result
            if (
                hasattr(result, "pydantic")
                and result.pydantic
                and isinstance(result.pydantic, AnalysisOutput)
            ):
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
    async def generate_recipe(self) -> CocktailFlowState:
        """Run Recipe Crew to generate detailed recipe and bottle advice.

        This step creates and kicks off the Recipe Crew which:
        1. Uses Recipe Writer to generate a skill-appropriate recipe
        2. Uses Bottle Advisor to recommend next bottle purchases

        When PARALLEL_CREWS is enabled (default) and bottle advice is requested,
        the Recipe Writer and Bottle Advisor run in parallel for faster execution.
        Otherwise, they run sequentially with the bottle advisor receiving recipe context.

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

        settings = get_settings()
        start_time = time.perf_counter()

        # Choose execution mode based on settings and whether bottle advice is requested
        if settings.PARALLEL_CREWS and self.state.include_bottle_advice:
            await self._generate_parallel()
            mode = "parallel"
        else:
            await self._generate_sequential()
            mode = "sequential"

        elapsed = time.perf_counter() - start_time
        logger.info(f"Recipe generation ({mode}): {elapsed:.2f}s")

        return self.state

    async def _generate_parallel(self) -> None:
        """Run Recipe Writer and Bottle Advisor in parallel.

        This method executes both crews concurrently using asyncio.gather(),
        providing significant latency reduction when both tasks are needed.

        Error Handling:
            - If recipe fails: Set error state, discard bottle result
            - If bottle fails: Log warning, continue with recipe only
            - If timeout (30s): Set error state
        """
        # Map drink_type to service format
        drink_type_map: dict[str, DrinkTypeFilter] = {
            "cocktail": "cocktails",
            "mocktail": "mocktails",
            "both": "both",
        }

        # Pre-compute data for prompt injection
        drink_data = get_drink_by_id(self.state.selected or "")
        recipe_data_text = format_recipe_for_prompt(drink_data) if drink_data else ""

        # Get substitutions for missing ingredients
        if drink_data:
            ing_ids = [ing["item"] for ing in drink_data.get("ingredients", [])]
            cabinet_lower = {c.lower() for c in self.state.cabinet}
            missing = [i for i in ing_ids if i.lower() not in cabinet_lower]
            subs = get_substitutions_for_ingredients(missing)
            subs_text = (
                "\n".join(f"- {k}: {', '.join(v)}" for k, v in subs.items())
                if subs
                else "None needed"
            )
        else:
            subs_text = "Recipe not found"

        # Get bottle recommendations - map drink_type to expected format
        bottle_drink_type: DrinkTypeFilter = drink_type_map.get(
            self.state.drink_type, "both"
        )
        bottle_recs = get_unlock_recommendations(self.state.cabinet, bottle_drink_type)
        bottle_recs_text = format_bottle_recommendations_for_prompt(bottle_recs)

        recipe_crew = create_recipe_only_crew()
        bottle_crew = create_bottle_only_crew()

        try:
            # Run both crews in parallel with timeout
            results = await asyncio.wait_for(
                asyncio.gather(
                    recipe_crew.kickoff_async(
                        inputs={
                            "cocktail_id": self.state.selected,
                            "skill_level": self.state.skill_level,
                            "cabinet": self.state.cabinet,
                            "drink_type": self.state.drink_type,
                            "recipe_data": recipe_data_text,
                            "substitutions_data": subs_text,
                        }
                    ),
                    bottle_crew.kickoff_async(
                        inputs={
                            "cabinet": self.state.cabinet,
                            "drink_type": self.state.drink_type,
                            "bottle_recommendations": bottle_recs_text,
                        }
                    ),
                    return_exceptions=True,  # Don't fail fast, handle individually
                ),
                timeout=30.0,
            )

            recipe_result, bottle_result = results

            # Handle individual failures
            if isinstance(recipe_result, Exception):
                logger.error(f"Recipe generation failed: {recipe_result}")
                self.state.error = f"Recipe generation failed: {recipe_result}"
                return

            bottle_result_valid: bool = True
            if isinstance(bottle_result, Exception):
                logger.warning(f"Bottle advice failed: {bottle_result}")
                bottle_result_valid = False  # Continue without bottle advice

            # Store raw output for debugging
            self.state.recipe_raw = str(recipe_result)

            # Extract recipe output
            recipe_output = self._extract_recipe_from_result(recipe_result)
            self.state.recipe = recipe_output

            # Extract bottle output if available
            if bottle_result_valid and not isinstance(bottle_result, Exception):
                bottle_output = self._extract_bottle_from_result(bottle_result)
                self.state.bottle_advice = bottle_output

                # Create legacy format for API compatibility
                if bottle_output and bottle_output.recommendations:
                    top_rec = bottle_output.recommendations[0]
                    self.state.next_bottle = {
                        "ingredient": top_rec.ingredient,
                        "ingredient_name": top_rec.ingredient_name,
                        "unlocks": top_rec.unlocks,
                        "drinks": top_rec.drinks,
                    }
            else:
                self.state.bottle_advice = BottleAdvisorOutput(
                    recommendations=[], total_new_drinks=0
                )

            logger.info(
                f"Recipe generated for '{self.state.selected}' (parallel), "
                f"has_bottle_advice={self.state.bottle_advice is not None}"
            )

        except TimeoutError:
            logger.error("Recipe generation timed out after 30s")
            self.state.error = "Recipe generation timed out"

        except Exception as e:
            logger.error(f"Parallel recipe generation failed: {e}", exc_info=True)
            self.state.error = f"Recipe generation failed: {str(e)}"

    async def _generate_sequential(self) -> None:
        """Run Recipe Crew sequentially (original behavior).

        This method maintains backwards compatibility by running the combined
        Recipe Crew that chains Recipe Writer -> Bottle Advisor sequentially.
        """
        # Map drink_type to service format
        drink_type_map: dict[str, DrinkTypeFilter] = {
            "cocktail": "cocktails",
            "mocktail": "mocktails",
            "both": "both",
        }

        # Pre-compute data for prompt injection
        drink_data = get_drink_by_id(self.state.selected or "")
        recipe_data_text = format_recipe_for_prompt(drink_data) if drink_data else ""

        # Get substitutions for missing ingredients
        if drink_data:
            ing_ids = [ing["item"] for ing in drink_data.get("ingredients", [])]
            cabinet_lower = {c.lower() for c in self.state.cabinet}
            missing = [i for i in ing_ids if i.lower() not in cabinet_lower]
            subs = get_substitutions_for_ingredients(missing)
            subs_text = (
                "\n".join(f"- {k}: {', '.join(v)}" for k, v in subs.items())
                if subs
                else "None needed"
            )
        else:
            subs_text = "Recipe not found"

        # Get bottle recommendations - map drink_type to expected format
        bottle_drink_type: DrinkTypeFilter = drink_type_map.get(
            self.state.drink_type, "both"
        )
        bottle_recs = get_unlock_recommendations(self.state.cabinet, bottle_drink_type)
        bottle_recs_text = format_bottle_recommendations_for_prompt(bottle_recs)

        try:
            # Create and run the Recipe Crew
            recipe_crew = create_recipe_crew(
                include_bottle_advice=self.state.include_bottle_advice
            )
            result = await recipe_crew.kickoff_async(
                inputs={
                    "cocktail_id": self.state.selected,
                    "skill_level": self.state.skill_level,
                    "cabinet": self.state.cabinet,
                    "drink_type": self.state.drink_type,
                    "recipe_data": recipe_data_text,
                    "substitutions_data": subs_text,
                    "bottle_recommendations": bottle_recs_text,
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
                            str(task_0), self.state.selected or ""
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
                    "ingredient_name": top_rec.ingredient_name,
                    "unlocks": top_rec.unlocks,
                    "drinks": top_rec.drinks,
                }

            logger.info(
                f"Recipe generated for '{self.state.selected}' (sequential), "
                f"has_bottle_advice={bottle_output is not None}"
            )

        except Exception as e:
            logger.error(f"Recipe generation failed: {e}", exc_info=True)
            self.state.error = f"Recipe generation failed: {str(e)}"

    def _extract_recipe_from_result(self, result: Any) -> RecipeOutput | None:
        """Extract RecipeOutput from a crew result.

        Args:
            result: The CrewAI kickoff result.

        Returns:
            Parsed RecipeOutput or None if extraction fails.
        """
        # Try to get from pydantic attribute first
        if hasattr(result, "pydantic") and isinstance(result.pydantic, RecipeOutput):
            return result.pydantic

        # Try to get from tasks_output
        if hasattr(result, "tasks_output") and result.tasks_output:
            task_0 = result.tasks_output[0]
            if hasattr(task_0, "pydantic") and isinstance(
                task_0.pydantic, RecipeOutput
            ):
                return task_0.pydantic

        # Fallback to parsing
        return self._parse_recipe_output(str(result), self.state.selected or "unknown")

    def _extract_bottle_from_result(self, result: Any) -> BottleAdvisorOutput | None:
        """Extract BottleAdvisorOutput from a crew result.

        Args:
            result: The CrewAI kickoff result.

        Returns:
            Parsed BottleAdvisorOutput or None if extraction fails.
        """
        # Try to get from pydantic attribute first
        if hasattr(result, "pydantic") and isinstance(
            result.pydantic, BottleAdvisorOutput
        ):
            return result.pydantic

        # Try to get from tasks_output
        if hasattr(result, "tasks_output") and result.tasks_output:
            task_0 = result.tasks_output[0]
            if hasattr(task_0, "pydantic") and isinstance(
                task_0.pydantic, BottleAdvisorOutput
            ):
                return task_0.pydantic

        # Fallback to parsing
        return self._parse_bottle_output(str(result))

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
