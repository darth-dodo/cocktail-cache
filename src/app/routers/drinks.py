"""Router for drink browsing and search endpoints.

This module provides endpoints for browsing, searching, and viewing
cocktail and mocktail recipes, as well as ingredient data.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create the router with prefix and tags
router = APIRouter(prefix="/drinks", tags=["drinks"])


# =============================================================================
# Models
# =============================================================================


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


# Category display names and emoji mappings
CATEGORY_CONFIG = {
    "spirits": {"display": "Spirits", "default_emoji": "🥃"},
    "modifiers": {"display": "Liqueurs & Modifiers", "default_emoji": "🍷"},
    "bitters_syrups": {"display": "Bitters & Syrups", "default_emoji": "💧"},
    "fresh": {"display": "Fresh & Produce", "default_emoji": "🍋"},
    "mixers": {"display": "Mixers", "default_emoji": "🧊"},
    "non_alcoholic": {"display": "Non-Alcoholic", "default_emoji": "🧃"},
}

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
    if ingredient_id in INGREDIENT_EMOJIS:
        return INGREDIENT_EMOJIS[ingredient_id]
    return CATEGORY_CONFIG.get(category, {}).get("default_emoji", "🍹")


def _smart_title_case(text: str) -> str:
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


def _format_ingredient_name(names: list[str]) -> str:
    if not names:
        return "Unknown"
    return _smart_title_case(names[0])


@router.get("", response_model=DrinksResponse)
async def get_drinks() -> DrinksResponse:
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


@router.get("/{drink_id}", response_model=DrinkDetailResponse)
async def get_drink_by_id(drink_id: str) -> DrinkDetailResponse:
    from src.app.services.data_loader import load_all_drinks

    all_drinks = load_all_drinks()
    drink = next((d for d in all_drinks if d.id == drink_id), None)
    if not drink:
        raise HTTPException(status_code=404, detail=f"Drink not found: {drink_id}")
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


ingredients_router = APIRouter(tags=["drinks"])


@ingredients_router.get("/ingredients", response_model=IngredientsResponse)
async def get_ingredients() -> IngredientsResponse:
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
        if items:
            categories[display_name] = items
    return IngredientsResponse(categories=categories)
