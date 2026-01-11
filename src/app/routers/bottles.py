"""Router for bottle suggestion endpoints.

This module provides the /suggest-bottles endpoint for bottle purchase
recommendations based on the user's current cabinet.

Global rate limits protect compute-intensive operations (privacy-first, no user tracking):
- /suggest-bottles: 30/min (compute-intensive)
"""

import logging
from collections import defaultdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.app.rate_limit import rate_limit_compute

logger = logging.getLogger(__name__)

# Create the API router
router = APIRouter(tags=["bottles"])


# =============================================================================
# Models
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
    """Status of a missing essential item."""

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


# =============================================================================
# Helper Functions
# =============================================================================


def _smart_title_case(text: str) -> str:
    """Convert text to title case, handling apostrophes correctly."""
    if not text:
        return text
    words = text.split()
    result = []
    for word in words:
        if "'" in word:
            parts = word.split("'")
            titled = parts[0].capitalize() + "'" + "'".join(parts[1:]).lower()
            result.append(titled)
        else:
            result.append(word.capitalize())
    return " ".join(result)


def _get_ingredient_display_name(ingredient_id: str) -> str:
    """Convert ingredient ID to human-readable name."""
    return _smart_title_case(ingredient_id.replace("-", " "))


def _is_core_bottle(ingredient_id: str) -> bool:
    """Check if an ingredient is a Core Bottle.

    Core Bottles are spirits, modifiers, and non-alcoholic bases that
    form the foundation of a home bar.
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
    """Check if an ingredient is an Essential item.

    Essential items are bitters and specialty syrups that enhance
    drinks but are not Core Bottles.
    """
    from src.app.services.data_loader import load_ingredients

    ingredients_db = load_ingredients()
    bitters_syrups_ids = {ing.id for ing in ingredients_db.bitters_syrups}

    return ingredient_id in bitters_syrups_ids


# =============================================================================
# Endpoint
# =============================================================================


@router.post("/suggest-bottles", response_model=SuggestBottlesResponse)
@rate_limit_compute
async def suggest_bottles(
    bottles_request: SuggestBottlesRequest,
) -> SuggestBottlesResponse:
    """Get bottle purchase recommendations based on your cabinet.

    This endpoint analyzes your current cabinet and recommends bottles
    that would unlock the most new drinks. It also identifies missing
    essential items like bitters and specialty syrups.

    Args:
        bottles_request: Request with cabinet contents and preferences.

    Returns:
        SuggestBottlesResponse with ranked recommendations and AI advice.
    """
    from src.app.services.data_loader import load_all_drinks

    logger.info(
        f"Suggest bottles request: cabinet_size={len(bottles_request.cabinet)}, "
        f"drink_type={bottles_request.drink_type}, limit={bottles_request.limit}"
    )

    cabinet_set = {ing.lower().strip() for ing in bottles_request.cabinet}
    all_drinks = load_all_drinks()

    # Filter by drink type
    filtered_drinks = []
    for drink in all_drinks:
        if bottles_request.drink_type == "cocktails" and drink.is_mocktail:
            continue
        if bottles_request.drink_type == "mocktails" and not drink.is_mocktail:
            continue
        filtered_drinks.append(drink)

    # Calculate makeable drinks
    drinks_makeable_list: list[str] = []
    for drink in filtered_drinks:
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}
        if core_bottles_needed.issubset(cabinet_set):
            drinks_makeable_list.append(drink.name)

    drinks_makeable = len(drinks_makeable_list)

    # Count which bottles would unlock the most drinks
    ingredient_drinks: dict[str, list[dict]] = defaultdict(list)

    for drink in filtered_drinks:
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}

        if core_bottles_needed.issubset(cabinet_set):
            continue

        missing_core = core_bottles_needed - cabinet_set

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

    # Build recommendations
    all_recommendations = []
    for ing_id, drinks_list in ingredient_drinks.items():
        if ing_id in cabinet_set:
            continue

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
                    for d in drinks_list[:10]
                ],
            )
        )

    all_recommendations.sort(key=lambda x: x.new_drinks_unlocked, reverse=True)
    top_recommendations = all_recommendations[: bottles_request.limit]

    # Track missing essentials
    missing_essentials: list[EssentialStatus] = []
    essential_usage: dict[str, int] = defaultdict(int)

    for drink in filtered_drinks:
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}
        core_bottles_needed = {ing for ing in drink_ingredients if _is_core_bottle(ing)}

        if core_bottles_needed.issubset(cabinet_set):
            for ing in drink_ingredients:
                if _is_essential_item(ing) and ing not in cabinet_set:
                    essential_usage[ing] += 1

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

    core_bottles_in_cabinet = sum(1 for ing in cabinet_set if _is_core_bottle(ing))
    core_bottles_list = [ing for ing in cabinet_set if _is_core_bottle(ing)]

    # AI Enhancement
    ai_summary: str | None = None
    ai_top_reasoning: str | None = None
    essentials_note: str | None = None
    next_milestone: str | None = None

    if top_recommendations and core_bottles_in_cabinet > 0:
        try:
            from src.app.crews.bar_growth_crew import run_bar_growth_crew

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

            ranked_bottles_formatted = chr(10).join(
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

            # Run the crew with native async (no thread pool needed)
            ai_result = await run_bar_growth_crew(
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

    return SuggestBottlesResponse(
        cabinet_size=core_bottles_in_cabinet,
        drinks_makeable_now=drinks_makeable,
        recommendations=top_recommendations,
        total_available_recommendations=len(all_recommendations),
        ai_summary=ai_summary,
        ai_top_reasoning=ai_top_reasoning,
        essentials_note=essentials_note,
        next_milestone=next_milestone,
        missing_essentials=missing_essentials[:5],
    )
