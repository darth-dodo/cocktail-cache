"""Services for the Cocktail Cache application."""

from src.app.services.data_loader import (
    load_all_drinks,
    load_cocktails,
    load_ingredients,
    load_mocktails,
    load_substitutions,
    load_unlock_scores,
)
from src.app.services.drink_data import (
    BottleRecommendation,
    DrinkTypeFilter,
    format_bottle_recommendations_for_prompt,
    format_drinks_for_prompt,
    format_recipe_for_prompt,
    get_drink_by_id,
    get_drink_flavor_profiles,
    get_makeable_drinks,
    get_substitutions_for_ingredients,
    get_unlock_recommendations,
)

__all__ = [
    # Data loader exports
    "load_all_drinks",
    "load_cocktails",
    "load_mocktails",
    "load_ingredients",
    "load_substitutions",
    "load_unlock_scores",
    # Drink data service exports
    "BottleRecommendation",
    "DrinkTypeFilter",
    "get_makeable_drinks",
    "get_drink_flavor_profiles",
    "get_drink_by_id",
    "get_substitutions_for_ingredients",
    "get_unlock_recommendations",
    "format_drinks_for_prompt",
    "format_recipe_for_prompt",
    "format_bottle_recommendations_for_prompt",
]
