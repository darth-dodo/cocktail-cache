"""API router for cocktail flow endpoints.

This module provides the unified /flow endpoint that handles all
cocktail recommendation actions: starting a new flow, requesting
another recommendation, and marking drinks as made.
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
from src.app.models import DrinkType, RecipeOutput, SkillLevel

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
    unlocks: int = Field(..., description="Number of new drinks this unlocks")
    drinks: list[str] | None = Field(
        default=None,
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
                    "unlocks": 4,
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
            next_bottle = BottleRecData(
                ingredient=ingredient,
                unlocks=unlocks,
                drinks=state.next_bottle.get("drinks"),
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


@router.post("/flow", response_model=FlowResponse)
async def flow_endpoint(request: FlowRequest) -> FlowResponse:
    """Unified endpoint for all cocktail flow operations.

    Handles three actions:
    - START: Create a new flow with cabinet and preferences
    - ANOTHER: Request a different recommendation for existing session
    - MADE: Mark a drink as made in the user's history

    Args:
        request: The flow request with action and required parameters.

    Returns:
        FlowResponse with recommendation or status message.

    Raises:
        HTTPException: If session not found or validation fails.
    """
    logger.info(f"Flow endpoint called with action: {request.action}")

    if request.action == FlowAction.START:
        return await _handle_start(request)
    elif request.action == FlowAction.ANOTHER:
        return await _handle_another(request)
    elif request.action == FlowAction.MADE:
        return await _handle_made(request)
    else:
        # This should never happen due to enum validation
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")


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
