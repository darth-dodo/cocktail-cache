"""Router for cocktail recommendation flow endpoints.

This module provides the unified /flow endpoint that handles all
cocktail recommendation actions: starting a new flow, requesting
another recommendation, and marking drinks as made.

Global rate limits protect upstream API quotas (privacy-first, no user tracking):
- /flow: 10/min (LLM calls - expensive)
"""

import logging
import time
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.app.config import get_settings
from src.app.flows.cocktail_flow import (
    CocktailFlowState,
    request_another,
    run_cocktail_flow,
)
from src.app.models import (
    DrinkType,
    RecipeOutput,
    SkillLevel,
)
from src.app.rate_limit import rate_limit_llm

logger = logging.getLogger(__name__)

# Create the API router
router = APIRouter(tags=["flow"])

# In-memory session storage for MVP
# In production, this would be Redis or similar persistent store
# Each entry stores (state, created_timestamp) for TTL-based cleanup
_sessions: dict[str, tuple[CocktailFlowState, float]] = {}


def cleanup_expired_sessions() -> int:
    """Remove expired sessions based on SESSION_TTL_SECONDS.

    Returns:
        Number of sessions removed.
    """
    settings = get_settings()
    now = time.time()
    expired_ids = [
        session_id
        for session_id, (_, created_at) in _sessions.items()
        if now - created_at > settings.SESSION_TTL_SECONDS
    ]
    for session_id in expired_ids:
        del _sessions[session_id]
    if expired_ids:
        logger.info(f"Cleaned up {len(expired_ids)} expired flow sessions")
    return len(expired_ids)


def get_session_count() -> int:
    """Get the current number of active sessions.

    Returns:
        Number of active sessions.
    """
    return len(_sessions)


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
        description="Whether to include bottle purchase recommendations",
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


class RecipeData(BaseModel):
    """Recipe data extracted from flow state."""

    id: str | None = Field(default=None, description="Drink identifier")
    name: str | None = Field(default=None, description="Drink name")
    raw_content: str | None = Field(
        default=None,
        description="Raw recipe content if structured data unavailable",
    )
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
    """Response model for the unified /flow endpoint."""

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


def _state_to_response(
    state: CocktailFlowState, message: str | None = None
) -> FlowResponse:
    """Convert CocktailFlowState to FlowResponse."""
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

    recipe_data: RecipeData | None = None
    if state.recipe:
        if isinstance(state.recipe, RecipeOutput):
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

            technique_tips = (
                [tip.model_dump() for tip in state.recipe.technique_tips]
                if state.recipe.technique_tips
                else None
            )

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
            recipe_data = RecipeData(
                id=state.selected,
                raw_content=str(state.recipe),
            )
    elif state.selected:
        recipe_data = RecipeData(id=state.selected)

    next_bottle: BottleRecData | None = None
    if state.next_bottle and isinstance(state.next_bottle, dict):
        ingredient = state.next_bottle.get("ingredient")
        unlocks = state.next_bottle.get("unlocks")
        if ingredient and unlocks is not None:
            ingredient_name = state.next_bottle.get("ingredient_name")
            if not ingredient_name:
                ingredient_name = ingredient.replace("-", " ").title()
            next_bottle = BottleRecData(
                ingredient=ingredient,
                ingredient_name=ingredient_name,
                unlocks=unlocks,
                drinks=state.next_bottle.get("drinks") or [],
            )

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
@rate_limit_llm
async def flow_endpoint(flow_request: FlowRequest) -> FlowResponse:
    """Unified endpoint for all cocktail flow operations."""
    logger.info(f"Flow endpoint called with action: {flow_request.action}")

    if flow_request.action == FlowAction.START:
        return await _handle_start(flow_request)
    elif flow_request.action == FlowAction.ANOTHER:
        return await _handle_another(flow_request)
    elif flow_request.action == FlowAction.MADE:
        return await _handle_made(flow_request)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown action: {flow_request.action}"
        )


async def _handle_start(request: FlowRequest) -> FlowResponse:
    """Handle START action to create a new flow."""
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

    state = await run_cocktail_flow(
        cabinet=request.cabinet,
        mood=request.mood or "",
        skill_level=request.skill_level or SkillLevel.INTERMEDIATE,
        drink_type=request.drink_type or DrinkType.COCKTAIL,
        recent_history=request.recent_history or [],
        constraints=request.constraints or [],
        include_bottle_advice=request.include_bottle_advice,
    )

    _sessions[state.session_id] = (state, time.time())
    logger.info(f"Created session {state.session_id}, selected={state.selected}")

    return _state_to_response(state)


async def _handle_another(request: FlowRequest) -> FlowResponse:
    """Handle ANOTHER action to get a different recommendation."""
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required for ANOTHER action",
        )

    session_data = _sessions.get(request.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}",
        )
    state, created_at = session_data

    logger.info(
        f"Requesting another for session {request.session_id}, "
        f"current selection={state.selected}"
    )

    new_state = await request_another(state)
    _sessions[new_state.session_id] = (new_state, created_at)
    logger.info(
        f"Updated session {new_state.session_id}, new selection={new_state.selected}"
    )

    return _state_to_response(new_state, message="Here's another recommendation")


async def _handle_made(request: FlowRequest) -> FlowResponse:
    """Handle MADE action to record a drink as made."""
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

    session_data = _sessions.get(request.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}",
        )
    state, created_at = session_data

    logger.info(
        f"Marking drink '{request.drink_id}' as made for session {request.session_id}"
    )

    if request.drink_id not in state.recent_history:
        state.recent_history.append(request.drink_id)

    _sessions[state.session_id] = (state, created_at)

    return FlowResponse(
        session_id=state.session_id,
        success=True,
        message=f"Recorded '{request.drink_id}' as made. It will be excluded from future recommendations.",
        recipe=None,
        next_bottle=None,
        alternatives=None,
        error=None,
    )
