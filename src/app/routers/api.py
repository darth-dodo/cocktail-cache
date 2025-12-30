"""API router for cocktail flow endpoints.

This module provides the unified /flow endpoint that handles all
cocktail recommendation actions: starting a new flow, requesting
another recommendation, and marking drinks as made.

Global rate limits protect upstream API quotas (privacy-first, no user tracking):
- /flow: 10/min (LLM calls - expensive)
- /suggest-bottles: 30/min (compute-intensive)
- Static data endpoints: No limit (fast local lookups)
"""

import logging
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.app.flows.cocktail_flow import (
    CocktailFlowState,
    request_another,
    run_cocktail_flow,
)
from src.app.models import (
    ChatRequest,
    ChatResponse,
    DrinkType,
    RecipeOutput,
    SkillLevel,
)
from src.app.rate_limit import rate_limit_compute, rate_limit_llm

logger = logging.getLogger(__name__)

# Create the API router
router = APIRouter(tags=["flow"])

# In-memory session storage for MVP
# In production, this would be Redis or similar persistent store
_sessions: dict[str, CocktailFlowState] = {}


class FlowAction(str, Enum):
    """Actions that can be performed on the cocktail flow."""

    START = "START"
    ANOTHER = "ANOTHER"
    MADE = "MADE"


class FlowRequest(BaseModel):
    """Request model for the unified /flow endpoint.

    The action field determines which operation to perform:
    - START: Begin a new flow with cabinet and preferences
    - ANOTHER: Request a different recommendation (requires session_id)
    - MADE: Mark a drink as made (requires session_id and drink_id)
    """

    action: FlowAction = Field(..., description="The action to perform")

    # Required for START action
    cabinet: list[str] | None = Field(
        default=None,
        description="List of ingredient IDs in the user's cabinet (required for START)",
    )
    mood: str | None = Field(
        default=None,
        description="Description of user's current mood (optional for START)",
    )
    skill_level: SkillLevel | None = Field(
        default=None,
        description="User's bartending skill level",
    )
    drink_type: DrinkType | None = Field(
        default=None,
        description="Preferred drink type (cocktail/mocktail/both)",
    )
    recent_history: list[str] | None = Field(
        default=None,
        description="List of recently made drink IDs to exclude",
    )
    constraints: list[str] | None = Field(
        default=None,
        description="Optional constraints like 'not too sweet'",
    )
    include_bottle_advice: bool = Field(
        default=True,
        description="Whether to include bottle purchase recommendations (set to False to skip and save processing time)",
    )

    # Required for ANOTHER and MADE actions
    session_id: str | None = Field(
        default=None,
        description="Session ID for ANOTHER and MADE actions",
    )

    # Required for MADE action
    drink_id: str | None = Field(
        default=None,
        description="Drink ID to mark as made (required for MADE action)",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Start a new flow",
                    "value": {
                        "action": "START",
                        "cabinet": ["bourbon", "lemons", "honey", "angostura-bitters"],
                        "mood": "unwinding after a long week",
                        "skill_level": "intermediate",
                        "drink_type": "cocktail",
                    },
                },
                {
                    "summary": "Start flow without bottle recommendations",
                    "value": {
                        "action": "START",
                        "cabinet": ["gin", "tonic-water", "lime"],
                        "mood": "quick refreshment",
                        "skill_level": "beginner",
                        "drink_type": "cocktail",
                        "include_bottle_advice": False,
                    },
                },
                {
                    "summary": "Request another recommendation",
                    "value": {
                        "action": "ANOTHER",
                        "session_id": "abc123-def456",
                    },
                },
                {
                    "summary": "Mark drink as made",
                    "value": {
                        "action": "MADE",
                        "session_id": "abc123-def456",
                        "drink_id": "old-fashioned",
                    },
                },
            ]
        }


class RecipeData(BaseModel):
    """Recipe data extracted from flow state."""

    id: str | None = Field(default=None, description="Drink identifier")
    name: str | None = Field(default=None, description="Drink name")
    raw_content: str | None = Field(
        default=None,
        description="Raw recipe content if structured data unavailable",
    )
    # Additional fields can be present from structured recipe
    tagline: str | None = None
    why: str | None = None
    ingredients: list[dict[str, Any]] | None = None
    method: list[dict[str, Any]] | None = None
    glassware: str | None = None
    garnish: str | None = None
    timing: str | None = None
    difficulty: str | None = None
    technique_tips: list[dict[str, Any]] | None = None
    is_mocktail: bool | None = None
    flavor_profile: dict[str, Any] | None = None

    class Config:
        extra = "allow"


class BottleRecData(BaseModel):
    """Bottle recommendation data."""

    ingredient: str = Field(..., description="Ingredient ID to purchase")
    ingredient_name: str = Field(
        ..., description="Human-readable name of the ingredient"
    )
    unlocks: int = Field(..., description="Number of new drinks this unlocks")
    drinks: list[str] = Field(
        default_factory=list,
        description="Names of drinks this ingredient would unlock",
    )


class FlowResponse(BaseModel):
    """Response model for the unified /flow endpoint.

    Contains the session ID, recipe data, next bottle recommendation,
    alternatives, and any error message.
    """

    session_id: str = Field(..., description="Session ID for follow-up requests")
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str | None = Field(
        default=None,
        description="Human-readable message about the result",
    )
    recipe: RecipeData | None = Field(
        default=None,
        description="The recommended recipe",
    )
    next_bottle: BottleRecData | None = Field(
        default=None,
        description="Suggested next bottle purchase",
    )
    alternatives: list[dict[str, Any]] | None = Field(
        default=None,
        description="Alternative drink candidates",
    )
    error: str | None = Field(
        default=None,
        description="Error message if something went wrong",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456",
                "success": True,
                "message": "Recommendation generated successfully",
                "recipe": {
                    "id": "whiskey-sour",
                    "name": "Whiskey Sour",
                    "tagline": "The perfect balance of booze and citrus",
                },
                "next_bottle": {
                    "ingredient": "sweet-vermouth",
                    "ingredient_name": "Sweet Vermouth",
                    "unlocks": 4,
                    "drinks": ["Manhattan", "Negroni", "Boulevardier"],
                },
                "alternatives": [
                    {"id": "old-fashioned", "name": "Old Fashioned", "mood_score": 85}
                ],
                "error": None,
            }
        }


def _state_to_response(
    state: CocktailFlowState, message: str | None = None
) -> FlowResponse:
    """Convert CocktailFlowState to FlowResponse.

    Extracts recipe data, next bottle recommendation, and alternatives
    from the flow state into the API response format.

    Args:
        state: The flow state to convert.
        message: Optional message to include in response.

    Returns:
        FlowResponse with extracted data.
    """
    # Handle error case
    if state.error:
        return FlowResponse(
            session_id=state.session_id,
            success=False,
            message=None,
            recipe=None,
            next_bottle=None,
            alternatives=None,
            error=state.error,
        )

    # Extract recipe data
    recipe_data: RecipeData | None = None
    if state.recipe:
        if isinstance(state.recipe, RecipeOutput):
            # Handle structured RecipeOutput Pydantic model
            # Convert ingredients to frontend-compatible format
            ingredients = (
                [
                    {
                        "amount": f"{ing.amount} {ing.unit}".strip(),
                        "name": ing.item,
                    }
                    for ing in state.recipe.ingredients
                ]
                if state.recipe.ingredients
                else None
            )

            # Convert method to frontend-compatible format
            method = (
                [
                    {
                        "step": i + 1,
                        "instruction": f"{step.action}: {step.detail}"
                        if step.action
                        else step.detail,
                    }
                    for i, step in enumerate(state.recipe.method)
                ]
                if state.recipe.method
                else None
            )

            # Convert technique_tips to list of dicts
            technique_tips = (
                [tip.model_dump() for tip in state.recipe.technique_tips]
                if state.recipe.technique_tips
                else None
            )

            # Convert flavor_profile to dict
            flavor_profile = (
                state.recipe.flavor_profile.model_dump()
                if state.recipe.flavor_profile
                else None
            )

            recipe_data = RecipeData(
                id=state.recipe.id,
                name=state.recipe.name,
                tagline=state.recipe.tagline,
                why=state.recipe.why,
                ingredients=ingredients,
                method=method,
                glassware=state.recipe.glassware,
                garnish=state.recipe.garnish,
                timing=state.recipe.timing,
                difficulty=state.recipe.difficulty,
                technique_tips=technique_tips,
                is_mocktail=state.recipe.is_mocktail,
                flavor_profile=flavor_profile,
            )
        elif isinstance(state.recipe, dict):
            recipe_data = RecipeData(
                id=state.recipe.get("id") or state.selected,
                name=state.recipe.get("name"),
                raw_content=state.recipe.get("raw_content"),
                tagline=state.recipe.get("tagline"),
                why=state.recipe.get("why"),
                ingredients=state.recipe.get("ingredients"),
                method=state.recipe.get("method"),
                glassware=state.recipe.get("glassware"),
                garnish=state.recipe.get("garnish"),
                timing=state.recipe.get("timing"),
                difficulty=state.recipe.get("difficulty"),
                technique_tips=state.recipe.get("technique_tips"),
                is_mocktail=state.recipe.get("is_mocktail"),
                flavor_profile=state.recipe.get("flavor_profile"),
            )
        else:
            # Handle case where recipe is not a dict or RecipeOutput
            recipe_data = RecipeData(
                id=state.selected,
                raw_content=str(state.recipe),
            )
    elif state.selected:
        # No recipe but we have a selection
        recipe_data = RecipeData(id=state.selected)

    # Extract next bottle recommendation
    next_bottle: BottleRecData | None = None
    if state.next_bottle and isinstance(state.next_bottle, dict):
        ingredient = state.next_bottle.get("ingredient")
        unlocks = state.next_bottle.get("unlocks")
        if ingredient and unlocks is not None:
            # Get ingredient_name from state or derive from ingredient ID
            ingredient_name = state.next_bottle.get("ingredient_name")
            if not ingredient_name:
                # Derive human-readable name from ingredient ID
                ingredient_name = ingredient.replace("-", " ").title()
            next_bottle = BottleRecData(
                ingredient=ingredient,
                ingredient_name=ingredient_name,
                unlocks=unlocks,
                drinks=state.next_bottle.get("drinks") or [],
            )

    # Extract alternatives (candidates excluding selected)
    alternatives: list[dict[str, Any]] | None = None
    if state.candidates:
        alternatives = [
            candidate
            for candidate in state.candidates
            if candidate.get("id") != state.selected
        ]

    return FlowResponse(
        session_id=state.session_id,
        success=True,
        message=message or "Recommendation generated successfully",
        recipe=recipe_data,
        next_bottle=next_bottle,
        alternatives=alternatives if alternatives else None,
        error=None,
    )


class IngredientItem(BaseModel):
    """An ingredient for the frontend."""

    id: str = Field(..., description="Unique ingredient identifier")
    name: str = Field(..., description="Display name for the ingredient")
    emoji: str = Field(default="🍹", description="Emoji icon for the ingredient")


class DrinkSummary(BaseModel):
    """Summary of a drink for browsing/search."""

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(..., description="Short description")
    difficulty: str = Field(
        ..., description="Difficulty level (easy/medium/hard/advanced)"
    )
    is_mocktail: bool = Field(..., description="Whether this is a mocktail")
    timing_minutes: int = Field(..., description="Preparation time in minutes")
    tags: list[str] = Field(default_factory=list, description="Drink tags")
    ingredient_ids: list[str] = Field(
        default_factory=list, description="List of ingredient IDs for cabinet matching"
    )


class DrinksResponse(BaseModel):
    """Response model for the drinks browse endpoint."""

    drinks: list[DrinkSummary] = Field(..., description="List of all available drinks")
    total: int = Field(..., description="Total number of drinks")


class IngredientsResponse(BaseModel):
    """Response model for the ingredients endpoint."""

    categories: dict[str, list[IngredientItem]] = Field(
        ..., description="Ingredients organized by category"
    )


# Category display names and emoji mappings
CATEGORY_CONFIG = {
    "spirits": {"display": "Spirits", "default_emoji": "🥃"},
    "modifiers": {"display": "Liqueurs & Modifiers", "default_emoji": "🍷"},
    "bitters_syrups": {"display": "Bitters & Syrups", "default_emoji": "💧"},
    "fresh": {"display": "Fresh & Produce", "default_emoji": "🍋"},
    "mixers": {"display": "Mixers", "default_emoji": "🧊"},
    "non_alcoholic": {"display": "Non-Alcoholic", "default_emoji": "🧃"},
}

# Specific emoji overrides for common ingredients
INGREDIENT_EMOJIS = {
    "bourbon": "🥃",
    "rye": "🥃",
    "scotch": "🥃",
    "irish-whiskey": "🥃",
    "gin": "🍸",
    "vodka": "🍸",
    "white-rum": "🥃",
    "dark-rum": "🥃",
    "tequila": "🌵",
    "mezcal": "🌵",
    "cognac": "🍷",
    "brandy": "🍷",
    "campari": "🔴",
    "aperol": "🍊",
    "sweet-vermouth": "🍷",
    "dry-vermouth": "🍸",
    "cointreau": "🍊",
    "amaretto": "🌰",
    "kahlua": "☕",
    "chartreuse": "🌿",
    "maraschino": "🍒",
    "angostura": "💧",
    "orange-bitters": "🍊",
    "simple-syrup": "🍯",
    "honey-syrup": "🍯",
    "grenadine": "🍒",
    "lemon-juice": "🍋",
    "lime-juice": "🍋",
    "orange-juice": "🍊",
    "grapefruit-juice": "🍊",
    "pineapple-juice": "🍍",
    "cranberry-juice": "🍒",
    "mint": "🌿",
    "ginger": "🫚",
    "cucumber": "🥒",
    "egg-white": "🥚",
    "cream": "🥛",
    "soda-water": "💧",
    "tonic-water": "💧",
    "ginger-beer": "🍺",
    "cola": "🥤",
    "champagne": "🥂",
    "prosecco": "🥂",
}


def _get_ingredient_emoji(ingredient_id: str, category: str) -> str:
    """Get emoji for an ingredient, with fallback to category default."""
    if ingredient_id in INGREDIENT_EMOJIS:
        return INGREDIENT_EMOJIS[ingredient_id]
    return CATEGORY_CONFIG.get(category, {}).get("default_emoji", "🍹")


def _smart_title_case(text: str) -> str:
    """Convert text to title case, handling apostrophes and special cases properly.

    Unlike str.title(), this handles:
    - Apostrophes: "lyre's" -> "Lyre's" (not "Lyre'S")
    - Common abbreviations preserved
    """
    if not text:
        return text

    words = text.split()
    result = []

    for word in words:
        if "'" in word:
            # Handle apostrophes: capitalize first letter, keep rest of word structure
            parts = word.split("'")
            # Capitalize first part, keep second part lowercase
            titled = parts[0].capitalize() + "'" + "'".join(parts[1:]).lower()
            result.append(titled)
        else:
            result.append(word.capitalize())

    return " ".join(result)


def _format_ingredient_name(names: list[str]) -> str:
    """Get the best display name from the names list."""
    if not names:
        return "Unknown"
    # Use the first name with smart title casing
    return _smart_title_case(names[0])


class DrinkDetailResponse(BaseModel):
    """Full drink details for the drink detail page."""

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(..., description="Short description")
    difficulty: str = Field(
        ..., description="Difficulty level (easy/medium/hard/advanced)"
    )
    is_mocktail: bool = Field(..., description="Whether this is a mocktail")
    timing_minutes: int = Field(..., description="Preparation time in minutes")
    tags: list[str] = Field(default_factory=list, description="Drink tags")
    ingredients: list[dict[str, str]] = Field(
        ..., description="List of ingredients with amount, unit, item"
    )
    method: list[dict[str, str]] = Field(
        ..., description="List of method steps with action and detail"
    )
    glassware: str = Field(..., description="Type of glass to serve in")
    garnish: str = Field(..., description="Garnish description")
    flavor_profile: dict[str, int] = Field(
        ..., description="Flavor profile with sweet, sour, bitter, spirit levels"
    )


@router.get("/drinks", response_model=DrinksResponse)
async def get_drinks() -> DrinksResponse:
    """Get all available drinks for browsing.

    Returns a summary of all cocktails and mocktails with basic info
    suitable for search and browse functionality.

    Returns:
        DrinksResponse with list of drink summaries.
    """
    from src.app.services.data_loader import load_all_drinks

    all_drinks = load_all_drinks()

    drinks = [
        DrinkSummary(
            id=drink.id,
            name=drink.name,
            tagline=drink.tagline,
            difficulty=drink.difficulty,
            is_mocktail=drink.is_mocktail,
            timing_minutes=drink.timing_minutes,
            tags=drink.tags,
            ingredient_ids=[ing.item for ing in drink.ingredients],
        )
        for drink in all_drinks
    ]

    return DrinksResponse(drinks=drinks, total=len(drinks))


@router.get("/drinks/{drink_id}", response_model=DrinkDetailResponse)
async def get_drink_by_id(drink_id: str) -> DrinkDetailResponse:
    """Get a single drink by ID with full details.

    Args:
        drink_id: The unique identifier of the drink.

    Returns:
        DrinkDetailResponse with full drink data.

    Raises:
        HTTPException: If drink is not found.
    """
    from src.app.services.data_loader import load_all_drinks

    all_drinks = load_all_drinks()

    # Find the drink by ID
    drink = next((d for d in all_drinks if d.id == drink_id), None)

    if not drink:
        raise HTTPException(
            status_code=404,
            detail=f"Drink not found: {drink_id}",
        )

    return DrinkDetailResponse(
        id=drink.id,
        name=drink.name,
        tagline=drink.tagline,
        difficulty=drink.difficulty,
        is_mocktail=drink.is_mocktail,
        timing_minutes=drink.timing_minutes,
        tags=drink.tags,
        ingredients=[
            {"amount": ing.amount, "unit": ing.unit, "item": ing.item}
            for ing in drink.ingredients
        ],
        method=[
            {"action": step.action, "detail": step.detail} for step in drink.method
        ],
        glassware=drink.glassware,
        garnish=drink.garnish,
        flavor_profile=drink.flavor_profile.model_dump(),
    )


@router.get("/ingredients", response_model=IngredientsResponse)
async def get_ingredients() -> IngredientsResponse:
    """Get all available ingredients organized by category.

    Returns ingredients from the canonical ingredients.json database,
    formatted for frontend display with emojis and display names.

    Returns:
        IngredientsResponse with categorized ingredients.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()

    categories: dict[str, list[IngredientItem]] = {}

    for category_key in CATEGORY_CONFIG:
        category_ingredients = getattr(ingredients_db, category_key, [])
        display_name = CATEGORY_CONFIG[category_key]["display"]

        items = [
            IngredientItem(
                id=ing.id,
                name=_format_ingredient_name(ing.names),
                emoji=_get_ingredient_emoji(ing.id, category_key),
            )
            for ing in category_ingredients
        ]

        if items:  # Only include non-empty categories
            categories[display_name] = items

    return IngredientsResponse(categories=categories)


@router.post("/flow", response_model=FlowResponse)
@rate_limit_llm
async def flow_endpoint(flow_request: FlowRequest) -> FlowResponse:
    """Unified endpoint for all cocktail flow operations.

    Handles three actions:
    - START: Create a new flow with cabinet and preferences
    - ANOTHER: Request a different recommendation for existing session
    - MADE: Mark a drink as made in the user's history

    Rate limited to 10 calls/minute globally to protect LLM API quotas.

    Args:
        flow_request: The flow request with action and required parameters.

    Returns:
        FlowResponse with recommendation or status message.

    Raises:
        HTTPException: If session not found or validation fails.
    """
    logger.info(f"Flow endpoint called with action: {flow_request.action}")

    if flow_request.action == FlowAction.START:
        return await _handle_start(flow_request)
    elif flow_request.action == FlowAction.ANOTHER:
        return await _handle_another(flow_request)
    elif flow_request.action == FlowAction.MADE:
        return await _handle_made(flow_request)
    else:
        # This should never happen due to enum validation
        raise HTTPException(
            status_code=400, detail=f"Unknown action: {flow_request.action}"
        )


async def _handle_start(request: FlowRequest) -> FlowResponse:
    """Handle START action to create a new flow.

    Args:
        request: The flow request with cabinet and preferences.

    Returns:
        FlowResponse with the initial recommendation.

    Raises:
        HTTPException: If cabinet is missing or empty.
    """
    # Validate required fields for START
    if not request.cabinet:
        raise HTTPException(
            status_code=400,
            detail="Cabinet is required for START action and cannot be empty",
        )

    logger.info(
        f"Starting new flow with {len(request.cabinet)} ingredients, "
        f"mood='{request.mood or 'not specified'}', "
        f"include_bottle_advice={request.include_bottle_advice}"
    )

    # Run the cocktail flow (async to work with FastAPI's event loop)
    state = await run_cocktail_flow(
        cabinet=request.cabinet,
        mood=request.mood or "",
        skill_level=request.skill_level or SkillLevel.INTERMEDIATE,
        drink_type=request.drink_type or DrinkType.COCKTAIL,
        recent_history=request.recent_history or [],
        constraints=request.constraints or [],
        include_bottle_advice=request.include_bottle_advice,
    )

    # Store session state
    _sessions[state.session_id] = state
    logger.info(f"Created session {state.session_id}, selected={state.selected}")

    return _state_to_response(state)


async def _handle_another(request: FlowRequest) -> FlowResponse:
    """Handle ANOTHER action to get a different recommendation.

    Args:
        request: The flow request with session_id.

    Returns:
        FlowResponse with a new recommendation.

    Raises:
        HTTPException: If session_id is missing or session not found.
    """
    # Validate required fields for ANOTHER
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for ANOTHER action",
        )

    # Get existing session state
    state = _sessions.get(request.session_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}",
        )

    logger.info(
        f"Requesting another for session {request.session_id}, "
        f"current selection={state.selected}"
    )

    # Request another recommendation (async)
    new_state = await request_another(state)

    # Update session state
    _sessions[new_state.session_id] = new_state
    logger.info(
        f"Updated session {new_state.session_id}, new selection={new_state.selected}"
    )

    return _state_to_response(new_state, message="Here's another recommendation")


async def _handle_made(request: FlowRequest) -> FlowResponse:
    """Handle MADE action to record a drink as made.

    This adds the drink to the session's recent_history so it will be
    excluded from future recommendations.

    Args:
        request: The flow request with session_id and drink_id.

    Returns:
        FlowResponse with success confirmation.

    Raises:
        HTTPException: If session_id or drink_id is missing, or session not found.
    """
    # Validate required fields for MADE
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for MADE action",
        )
    if not request.drink_id:
        raise HTTPException(
            status_code=400,
            detail="drink_id is required for MADE action",
        )

    # Get existing session state
    state = _sessions.get(request.session_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}",
        )

    logger.info(
        f"Marking drink '{request.drink_id}' as made for session {request.session_id}"
    )

    # Add drink to recent history (avoiding duplicates)
    if request.drink_id not in state.recent_history:
        state.recent_history.append(request.drink_id)

    # Update session state
    _sessions[state.session_id] = state

    return FlowResponse(
        session_id=state.session_id,
        success=True,
        message=f"Recorded '{request.drink_id}' as made. It will be excluded from future recommendations.",
        recipe=None,
        next_bottle=None,
        alternatives=None,
        error=None,
    )


# =============================================================================
# Suggest Bottles Endpoint
# =============================================================================


class SuggestBottlesRequest(BaseModel):
    """Request model for bottle suggestions."""

    cabinet: list[str] = Field(
        default_factory=list,
        description="List of ingredient IDs the user already has",
    )
    drink_type: str = Field(
        default="both",
        description="Filter by drink type: 'cocktails', 'mocktails', or 'both'",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of recommendations to return",
    )


class UnlockedDrink(BaseModel):
    """A drink that would be unlocked by purchasing a bottle."""

    id: str = Field(..., description="Drink identifier")
    name: str = Field(..., description="Display name")
    is_mocktail: bool = Field(..., description="Whether it's a mocktail")
    difficulty: str = Field(..., description="Difficulty level")


class BottleRecommendation(BaseModel):
    """A single bottle recommendation."""

    ingredient_id: str = Field(..., description="Ingredient ID to purchase")
    ingredient_name: str = Field(..., description="Human-readable ingredient name")
    new_drinks_unlocked: int = Field(
        ..., description="Number of new drinks this unlocks"
    )
    drinks: list[UnlockedDrink] = Field(
        ..., description="List of drinks this would unlock"
    )


class EssentialStatus(BaseModel):
    """Status of a missing essential item (bitters, specialty syrups)."""

    ingredient_id: str = Field(..., description="Ingredient ID")
    ingredient_name: str = Field(..., description="Human-readable name")
    used_in_drinks: int = Field(
        ..., description="Number of makeable drinks that use this"
    )


class SuggestBottlesResponse(BaseModel):
    """Response model for bottle suggestions."""

    cabinet_size: int = Field(..., description="Number of Core Bottles in cabinet")
    drinks_makeable_now: int = Field(
        ..., description="Drinks makeable with Core Bottles (kitchen items assumed)"
    )
    recommendations: list[BottleRecommendation] = Field(
        ..., description="Ranked list of bottle recommendations"
    )
    total_available_recommendations: int = Field(
        ..., description="Total recommendations before limit applied"
    )
    # AI-enhanced fields (optional, may be None if AI is disabled)
    ai_summary: str | None = Field(
        default=None,
        description="AI-generated personalized summary of bar growth advice",
    )
    ai_top_reasoning: str | None = Field(
        default=None,
        description="AI-generated reasoning for the top recommendation",
    )
    essentials_note: str | None = Field(
        default=None,
        description="Note about missing essential items like bitters",
    )
    next_milestone: str | None = Field(
        default=None,
        description="AI-generated encouragement about progress",
    )
    missing_essentials: list[EssentialStatus] = Field(
        default_factory=list,
        description="List of missing essential items (bitters, specialty syrups)",
    )


def _get_ingredient_display_name(ingredient_id: str) -> str:
    """Convert ingredient ID to human-readable name."""
    # Convert kebab-case to title case with proper apostrophe handling
    return _smart_title_case(ingredient_id.replace("-", " "))


def _is_bottle_ingredient(ingredient_id: str) -> bool:
    """Check if an ingredient is a bottle (spirit, liqueur/modifier, or non-alcoholic spirit).

    Returns True for spirits, liqueurs/modifiers, and non-alcoholic spirits.
    Returns False for accessories like juices, syrups, bitters, mixers, fresh produce.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()

    # Check if ingredient is in spirits, modifiers, or non-alcoholic categories
    spirits_ids = {ing.id for ing in ingredients_db.spirits}
    modifiers_ids = {ing.id for ing in ingredients_db.modifiers}
    non_alcoholic_ids = {ing.id for ing in ingredients_db.non_alcoholic}

    return (
        ingredient_id in spirits_ids
        or ingredient_id in modifiers_ids
        or ingredient_id in non_alcoholic_ids
    )


def _is_core_bottle(ingredient_id: str) -> bool:
    """Check if an ingredient is a Core Bottle (requires tracking in cabinet).

    Core Bottles include:
    - Spirits (bourbon, gin, vodka, rum, tequila, etc.)
    - Modifiers (liqueurs like Cointreau, Campari, vermouth, etc.)
    - Non-Alcoholic spirits (Seedlip, etc.)

    These are bottles users invest in and should track.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()

    spirits_ids = {ing.id for ing in ingredients_db.spirits}
    modifiers_ids = {ing.id for ing in ingredients_db.modifiers}
    non_alcoholic_ids = {ing.id for ing in ingredients_db.non_alcoholic}

    return (
        ingredient_id in spirits_ids
        or ingredient_id in modifiers_ids
        or ingredient_id in non_alcoholic_ids
    )


def _is_essential_item(ingredient_id: str) -> bool:
    """Check if an ingredient is an Essential item (optional tracking).

    Essentials include:
    - Bitters (Angostura, orange bitters, etc.)
    - Specialty syrups (orgeat, falernum, etc.)

    These are shown in a separate "Don't forget" section.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()
    bitters_syrups_ids = {ing.id for ing in ingredients_db.bitters_syrups}

    return ingredient_id in bitters_syrups_ids


def _is_kitchen_item(ingredient_id: str) -> bool:
    """Check if an ingredient is a Kitchen item (assume available).

    Kitchen items include:
    - Fresh produce (lemons, limes, herbs, etc.)
    - Mixers (soda water, tonic, ginger beer, etc.)

    These are assumed available from any grocery store.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()

    fresh_ids = {ing.id for ing in ingredients_db.fresh}
    mixers_ids = {ing.id for ing in ingredients_db.mixers}

    return ingredient_id in fresh_ids or ingredient_id in mixers_ids


@router.post("/suggest-bottles", response_model=SuggestBottlesResponse)
@rate_limit_compute
async def suggest_bottles(
    bottles_request: SuggestBottlesRequest,
) -> SuggestBottlesResponse:
    """Get bottle purchase recommendations based on your cabinet.

    Uses the "Track your BAR, assume your KITCHEN" philosophy:
    - Core Bottles (spirits, modifiers, non-alcoholic spirits): Must have
    - Essentials (bitters, specialty syrups): Nice-to-have, tracked separately
    - Kitchen items (fresh produce, mixers): Assumed available

    Returns ranked recommendations of Core Bottles to purchase,
    with optional AI-generated personalized advice.

    Rate limited to 30 calls/minute globally.

    Args:
        bottles_request: Request with cabinet ingredients and filters.

    Returns:
        SuggestBottlesResponse with ranked bottle recommendations.
    """
    from collections import defaultdict

    from src.app.services.data_loader import load_all_drinks

    logger.info(
        f"Suggest bottles request: cabinet_size={len(bottles_request.cabinet)}, "
        f"drink_type={bottles_request.drink_type}, limit={bottles_request.limit}"
    )

    # Normalize cabinet to lowercase
    cabinet_set = {ing.lower().strip() for ing in bottles_request.cabinet}

    # Load all drinks
    all_drinks = load_all_drinks()

    # Filter by drink type
    filtered_drinks = []
    for drink in all_drinks:
        if bottles_request.drink_type == "cocktails" and drink.is_mocktail:
            continue
        if bottles_request.drink_type == "mocktails" and not drink.is_mocktail:
            continue
        filtered_drinks.append(drink)

    # ==========================================================================
    # LENIENT MAKEABILITY: Only require Core Bottles, assume kitchen items
    # ==========================================================================
    drinks_makeable_list: list[str] = []
    for drink in filtered_drinks:
        # Get all ingredients for this drink
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}

        # Separate into Core Bottles vs Kitchen/Essentials
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}

        # Check if user has all required Core Bottles
        # (Kitchen items are assumed available, essentials are nice-to-have)
        if core_bottles_needed.issubset(cabinet_set):
            drinks_makeable_list.append(drink.name)

    drinks_makeable = len(drinks_makeable_list)

    # ==========================================================================
    # Count which Core Bottles would unlock the most NEW drinks
    # ==========================================================================
    ingredient_drinks: dict[str, list[dict]] = defaultdict(list)

    for drink in filtered_drinks:
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}

        # Only consider Core Bottles as "required"
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}

        # Skip if we can already make this drink (have all Core Bottles)
        if core_bottles_needed.issubset(cabinet_set):
            continue

        # Find missing Core Bottles
        missing_core = core_bottles_needed - cabinet_set

        # Only count drinks where exactly ONE Core Bottle is missing
        if len(missing_core) == 1:
            bottle_id = next(iter(missing_core))
            ingredient_drinks[bottle_id].append(
                {
                    "id": drink.id,
                    "name": drink.name,
                    "is_mocktail": drink.is_mocktail,
                    "difficulty": drink.difficulty,
                }
            )

    # ==========================================================================
    # Build recommendations (Core Bottles only)
    # ==========================================================================
    all_recommendations = []
    for ing_id, drinks_list in ingredient_drinks.items():
        # Skip ingredients already in cabinet
        if ing_id in cabinet_set:
            continue

        # Only recommend Core Bottles (not essentials or kitchen items)
        if not _is_core_bottle(ing_id):
            continue

        all_recommendations.append(
            BottleRecommendation(
                ingredient_id=ing_id,
                ingredient_name=_get_ingredient_display_name(ing_id),
                new_drinks_unlocked=len(drinks_list),
                drinks=[
                    UnlockedDrink(
                        id=d["id"],
                        name=d["name"],
                        is_mocktail=d["is_mocktail"],
                        difficulty=d["difficulty"],
                    )
                    for d in drinks_list[:10]  # Limit drinks per recommendation
                ],
            )
        )

    # Sort by number of drinks (highest first)
    all_recommendations.sort(key=lambda x: x.new_drinks_unlocked, reverse=True)

    # Apply limit
    top_recommendations = all_recommendations[: bottles_request.limit]

    # ==========================================================================
    # Track missing essentials (bitters, specialty syrups)
    # ==========================================================================
    missing_essentials: list[EssentialStatus] = []
    essential_usage: dict[str, int] = defaultdict(int)

    # Count how many makeable drinks use each essential
    for drink in filtered_drinks:
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}

        # Only count for drinks we can make (have all Core Bottles)
        if core_bottles_needed.issubset(cabinet_set):
            for ing in drink_ingredients:
                if _is_essential_item(ing) and ing not in cabinet_set:
                    essential_usage[ing] += 1

    # Build essentials list sorted by usage
    for essential_id, usage_count in sorted(
        essential_usage.items(), key=lambda x: x[1], reverse=True
    ):
        if usage_count > 0:
            missing_essentials.append(
                EssentialStatus(
                    ingredient_id=essential_id,
                    ingredient_name=_get_ingredient_display_name(essential_id),
                    used_in_drinks=usage_count,
                )
            )

    # Count Core Bottles in cabinet
    core_bottles_in_cabinet = sum(1 for ing in cabinet_set if _is_core_bottle(ing))
    core_bottles_list = [ing for ing in cabinet_set if _is_core_bottle(ing)]

    # ==========================================================================
    # AI ENHANCEMENT: Run Bar Growth Crew for personalized recommendations
    # ==========================================================================
    ai_summary: str | None = None
    ai_top_reasoning: str | None = None
    essentials_note: str | None = None
    next_milestone: str | None = None

    # Only run AI if we have recommendations and some cabinet items
    if top_recommendations and core_bottles_in_cabinet > 0:
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            from src.app.crews.bar_growth_crew import run_bar_growth_crew

            # Format data for the AI crew
            cabinet_formatted = ", ".join(
                _get_ingredient_display_name(b) for b in sorted(core_bottles_list)
            )
            cabinet_formatted += f" ({core_bottles_in_cabinet} bottles)"

            makeable_formatted = (
                f"You can make {drinks_makeable} drinks"
                + (
                    f": {', '.join(drinks_makeable_list[:10])}"
                    if drinks_makeable_list
                    else ""
                )
                + ("..." if len(drinks_makeable_list) > 10 else "")
            )

            ranked_bottles_formatted = "\n".join(
                f"{i + 1}. {rec.ingredient_name}: +{rec.new_drinks_unlocked} drinks "
                f"({', '.join(d.name for d in rec.drinks[:3])}{'...' if len(rec.drinks) > 3 else ''})"
                for i, rec in enumerate(top_recommendations[:5])
            )

            essentials_formatted = (
                "Missing: "
                + ", ".join(
                    f"{e.ingredient_name} (in {e.used_in_drinks} drinks)"
                    for e in missing_essentials[:5]
                )
                if missing_essentials
                else "No essential items missing."
            )

            # Run the crew in a thread pool to not block the event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                ai_result = await loop.run_in_executor(
                    executor,
                    run_bar_growth_crew,
                    cabinet_formatted,
                    makeable_formatted,
                    ranked_bottles_formatted,
                    essentials_formatted,
                )

            ai_summary = ai_result.summary
            ai_top_reasoning = ai_result.top_recommendation.reasoning
            essentials_note = ai_result.essentials_note
            next_milestone = ai_result.next_milestone

            logger.info("AI bar growth advice generated successfully")

        except Exception as e:
            logger.warning(f"AI bar growth crew failed, returning without AI: {e}")
            # Continue without AI - the basic recommendations are still useful

    return SuggestBottlesResponse(
        cabinet_size=core_bottles_in_cabinet,
        drinks_makeable_now=drinks_makeable,
        recommendations=top_recommendations,
        total_available_recommendations=len(all_recommendations),
        ai_summary=ai_summary,
        ai_top_reasoning=ai_top_reasoning,
        essentials_note=essentials_note,
        next_milestone=next_milestone,
        missing_essentials=missing_essentials[:5],  # Top 5 missing essentials
    )


# =============================================================================
# Raja Chat Endpoints
# =============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat_with_raja(request: ChatRequest) -> ChatResponse:
    """Send a message to Raja and get a response.

    This is the main chat endpoint for conversational interaction with Raja,
    the AI bartender from Bombay. Raja provides personality-rich cocktail
    advice based on the user's mood, cabinet, and preferences.

    First-time callers should omit session_id to start a new conversation.
    Follow-up messages should include the session_id from the previous response.

    Args:
        request: Chat request with message and optional context.

    Returns:
        ChatResponse with Raja's response and extracted entities.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    from src.app.crews.raja_chat_crew import run_raja_chat

    logger.info(
        f"Chat request: session_id={request.session_id}, "
        f"message_length={len(request.message)}"
    )

    # Run the crew in a thread pool to not block the event loop
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        response = await loop.run_in_executor(
            executor,
            run_raja_chat,
            request,
        )

    logger.info(f"Chat response: session_id={response.session_id}")
    return response


@router.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str) -> dict:
    """Get the conversation history for a chat session.

    Returns the full conversation history including Raja's greeting
    and all subsequent messages.

    Args:
        session_id: The session ID to retrieve history for.

    Returns:
        Dictionary with session info and message history.

    Raises:
        HTTPException: If session is not found.
    """
    from src.app.crews.raja_chat_crew import get_session

    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}",
        )

    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "message_count": len(session.history.messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in session.history.messages
        ],
        "current_mood": session.current_mood,
        "last_recommended_drink": session.last_recommended_drink,
    }


@router.delete("/chat/{session_id}")
async def end_chat_session(session_id: str) -> dict:
    """End a chat session and clean up resources.

    This deletes the session and its history from memory.
    The session_id will no longer be valid for follow-up messages.

    Args:
        session_id: The session ID to delete.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If session is not found.
    """
    from src.app.crews.raja_chat_crew import delete_session

    if not delete_session(session_id):
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}",
        )

    return {
        "success": True,
        "message": f"Session {session_id} has been deleted",
    }
