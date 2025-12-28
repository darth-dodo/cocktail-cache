"""Drink data service for pre-computing data to inject into prompts.

This service provides the same functionality as the CrewAI tools,
but returns data that can be directly injected into agent prompts,
eliminating the tool call overhead and reducing latency.

Instead of:
    Agent -> Tool call -> Wait -> Parse result -> Reason

We now have:
    Pre-compute data -> Inject into prompt -> Agent reasons directly
"""

import logging
import time
from typing import Literal, TypeAlias, TypedDict

from src.app.services.data_loader import (
    load_all_drinks,
    load_cocktails,
    load_mocktails,
    load_substitutions,
    load_unlock_scores,
)

# Type alias for drink type filter
DrinkTypeFilter: TypeAlias = Literal["cocktails", "mocktails", "both"]


class BottleRecommendation(TypedDict):
    """Type for bottle recommendation dicts."""

    ingredient: str
    ingredient_name: str
    unlocks: int
    drinks: list[str]


logger = logging.getLogger(__name__)


def get_makeable_drinks(
    cabinet: list[str],
    drink_type: DrinkTypeFilter = "both",
    exclude: list[str] | None = None,
) -> list[dict]:
    """Get all drinks that can be made with the given cabinet ingredients.

    This is equivalent to RecipeDBTool._run() but returns structured data
    for prompt injection instead of JSON string for tool parsing.

    Args:
        cabinet: List of ingredient IDs available in the user's cabinet.
        drink_type: Filter for 'cocktails', 'mocktails', or 'both'.
        exclude: List of drink IDs to exclude from results.

    Returns:
        List of drink dicts with match info, sorted by score (highest first).
        Only includes drinks with score=1.0 (all ingredients available).
    """
    start_time = time.perf_counter()
    logger.debug(
        f"get_makeable_drinks called with {len(cabinet)} ingredients, "
        f"drink_type={drink_type}, exclude={len(exclude or [])} drinks"
    )

    # Normalize cabinet ingredients to lowercase
    cabinet_set = {ing.lower().strip() for ing in cabinet}
    exclude_set = {e.lower().strip() for e in (exclude or [])}

    # Load appropriate drinks based on type filter
    if drink_type == "cocktails":
        drinks = load_cocktails()
    elif drink_type == "mocktails":
        drinks = load_mocktails()
    else:
        drinks = load_all_drinks()

    logger.debug(f"Loaded {len(drinks)} drinks from database for type={drink_type}")

    # Find drinks with complete ingredient matches
    matches = []
    for drink in drinks:
        # Skip excluded drinks
        if drink.id.lower() in exclude_set:
            continue

        required_ingredients = [ing.item.lower() for ing in drink.ingredients]
        total_required = len(required_ingredients)

        if total_required == 0:
            continue

        # Check if all required ingredients are available
        have = [ing for ing in required_ingredients if ing in cabinet_set]

        score = len(have) / total_required

        # Only include drinks where half+ ingredients are available
        if score >= 0.5:
            matches.append(
                {
                    "id": drink.id,
                    "name": drink.name,
                    "tagline": drink.tagline,
                    "is_mocktail": drink.is_mocktail,
                    "difficulty": drink.difficulty,
                    "timing_minutes": drink.timing_minutes,
                    "tags": drink.tags,
                    "glassware": drink.glassware,
                    "ingredients": [ing.item for ing in drink.ingredients],
                    "flavor_profile": {
                        "sweet": drink.flavor_profile.sweet,
                        "sour": drink.flavor_profile.sour,
                        "bitter": drink.flavor_profile.bitter,
                        "spirit": drink.flavor_profile.spirit,
                    },
                }
            )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(f"Found {len(matches)} makeable drinks in {elapsed_ms:.2f}ms")
    return matches


def get_drink_flavor_profiles(drink_ids: list[str]) -> list[dict]:
    """Get flavor profiles for the specified drinks.

    This is equivalent to FlavorProfilerTool._run() but returns structured
    data for prompt injection.

    Args:
        drink_ids: List of drink IDs to get profiles for.

    Returns:
        List of drink flavor profiles with analysis.
    """
    start_time = time.perf_counter()
    logger.debug(f"get_drink_flavor_profiles called for {len(drink_ids)} drinks")

    # Normalize IDs
    normalized_ids = {cid.lower().strip() for cid in drink_ids}

    # Build lookup of all drinks
    all_drinks = load_all_drinks()
    drinks_by_id = {d.id.lower(): d for d in all_drinks}

    profiles = []
    for drink_id in normalized_ids:
        drink = drinks_by_id.get(drink_id)
        if not drink:
            continue

        fp = drink.flavor_profile

        # Calculate derived characteristics
        flavors = {"sweet": fp.sweet, "sour": fp.sour, "bitter": fp.bitter}
        dominant = max(flavors, key=lambda k: flavors[k])

        # Categorize the drink style
        if fp.spirit == 0:
            style = "refreshing/mocktail"
        elif fp.spirit >= 70:
            style = "spirit-forward"
        elif fp.sour >= 40 and fp.sweet >= 30:
            style = "sour"
        elif fp.bitter >= 40:
            style = "bitter/aperitivo"
        elif fp.sweet >= 50:
            style = "sweet/dessert"
        else:
            style = "balanced"

        profiles.append(
            {
                "id": drink.id,
                "name": drink.name,
                "is_mocktail": drink.is_mocktail,
                "flavor_profile": {
                    "sweet": fp.sweet,
                    "sour": fp.sour,
                    "bitter": fp.bitter,
                    "spirit": fp.spirit,
                },
                "dominant_flavor": dominant,
                "style": style,
                "spirit_forward": fp.spirit >= 60,
                "tags": drink.tags,
            }
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    not_found = len(normalized_ids) - len(profiles)
    if not_found > 0:
        logger.warning(f"{not_found} drink IDs not found in database")
    logger.info(f"Retrieved {len(profiles)} flavor profiles in {elapsed_ms:.2f}ms")
    return profiles


def get_drink_by_id(drink_id: str) -> dict | None:
    """Get complete drink data by ID.

    This provides complete recipe data for the Recipe Writer agent.

    Args:
        drink_id: The drink ID to look up.

    Returns:
        Complete drink data dict, or None if not found.
    """
    start_time = time.perf_counter()
    logger.debug(f"get_drink_by_id called for drink_id={drink_id}")

    all_drinks = load_all_drinks()
    drink_id_lower = drink_id.lower().strip()

    for drink in all_drinks:
        if drink.id.lower() == drink_id_lower:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Found drink '{drink.name}' (id={drink_id}) in {elapsed_ms:.2f}ms"
            )
            return {
                "id": drink.id,
                "name": drink.name,
                "tagline": drink.tagline,
                "is_mocktail": drink.is_mocktail,
                "difficulty": drink.difficulty,
                "timing_minutes": drink.timing_minutes,
                "glassware": drink.glassware,
                "garnish": drink.garnish,
                "tags": drink.tags,
                "flavor_profile": {
                    "sweet": drink.flavor_profile.sweet,
                    "sour": drink.flavor_profile.sour,
                    "bitter": drink.flavor_profile.bitter,
                    "spirit": drink.flavor_profile.spirit,
                },
                "ingredients": [
                    {
                        "amount": ing.amount,
                        "unit": ing.unit,
                        "item": ing.item,
                    }
                    for ing in drink.ingredients
                ],
                "method": drink.method,
            }

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.warning(
        f"Drink not found for id={drink_id} after searching {len(all_drinks)} drinks in {elapsed_ms:.2f}ms"
    )
    return None


def get_substitutions_for_ingredients(
    ingredient_ids: list[str],
) -> dict[str, list[str]]:
    """Get substitution options for the given ingredients.

    Args:
        ingredient_ids: List of ingredient IDs to find substitutions for.

    Returns:
        Dict mapping each ingredient ID to a list of possible substitutes.
    """
    start_time = time.perf_counter()
    logger.debug(
        f"get_substitutions_for_ingredients called for {len(ingredient_ids)} ingredients"
    )

    subs_db = load_substitutions()
    result = {}
    missing_count = 0

    for ing_id in ingredient_ids:
        # Use the Pydantic model's method to find substitutes across all categories
        subs = subs_db.find_substitutes(ing_id)
        if subs:
            result[ing_id] = subs
        else:
            missing_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    if missing_count > 0:
        logger.warning(
            f"No substitutions found for {missing_count} of {len(ingredient_ids)} ingredients"
        )
    logger.info(
        f"Found substitutions for {len(result)} ingredients in {elapsed_ms:.2f}ms"
    )
    return result


def get_unlock_recommendations(
    cabinet: list[str],
    drink_type: DrinkTypeFilter = "both",
    top_n: int = 5,
) -> list[BottleRecommendation]:
    """Get bottle purchase recommendations based on unlock potential.

    This is equivalent to UnlockCalculatorTool._run().

    Args:
        cabinet: Current ingredients the user has.
        drink_type: Filter for drink type preference.
        top_n: Number of recommendations to return.

    Returns:
        List of bottle recommendations with unlock counts.
    """
    start_time = time.perf_counter()
    logger.debug(
        f"get_unlock_recommendations called with {len(cabinet)} cabinet items, "
        f"drink_type={drink_type}, top_n={top_n}"
    )

    cabinet_set = {ing.lower().strip() for ing in cabinet}
    unlock_scores = load_unlock_scores()

    # Load drinks to filter by type
    if drink_type == "cocktails":
        drinks = load_cocktails()
    elif drink_type == "mocktails":
        drinks = load_mocktails()
    else:
        drinks = load_all_drinks()

    drink_ids = {d.id.lower() for d in drinks}
    logger.debug(f"Analyzing unlock potential against {len(drink_ids)} drinks")

    # Calculate unlocks for each potential new ingredient
    recommendations: list[BottleRecommendation] = []

    for ingredient_id, unlocked_drinks in unlock_scores.items():
        # Skip ingredients already in cabinet
        if ingredient_id.lower() in cabinet_set:
            continue

        # Filter unlocks to drink type
        # unlocked_drinks is a list of UnlockedDrink objects
        relevant_unlocks: list[str] = []
        for unlocked in unlocked_drinks:
            if unlocked.id.lower() in drink_ids:
                # Check if this drink would become makeable
                drink = next(
                    (d for d in drinks if d.id.lower() == unlocked.id.lower()),
                    None,
                )
                if drink:
                    required = {ing.item.lower() for ing in drink.ingredients}
                    # Would be makeable if we add this ingredient and have all others
                    would_have = cabinet_set | {ingredient_id.lower()}
                    if required.issubset(would_have):
                        relevant_unlocks.append(unlocked.name)

        if relevant_unlocks:
            recommendations.append(
                BottleRecommendation(
                    ingredient=ingredient_id,
                    ingredient_name=ingredient_id.replace("-", " ").title(),
                    unlocks=len(relevant_unlocks),
                    drinks=relevant_unlocks[:5],  # Top 5 drinks
                )
            )

    # Sort by unlocks count (descending)
    recommendations.sort(key=lambda x: x["unlocks"], reverse=True)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    total_unlocks = sum(r["unlocks"] for r in recommendations[:top_n])
    logger.info(
        f"Generated {len(recommendations[:top_n])} bottle recommendations "
        f"(total potential unlocks: {total_unlocks}) in {elapsed_ms:.2f}ms"
    )
    return recommendations[:top_n]


def format_drinks_for_prompt(drinks: list[dict], include_flavor: bool = True) -> str:
    """Format drink data for injection into agent prompts.

    Args:
        drinks: List of drink dicts from get_makeable_drinks().
        include_flavor: Whether to include flavor profile details.

    Returns:
        Formatted string ready for prompt injection.
    """
    logger.debug(
        f"format_drinks_for_prompt called with {len(drinks)} drinks, include_flavor={include_flavor}"
    )

    if not drinks:
        logger.warning("No drinks to format for prompt")
        return "No drinks found that can be made with the available ingredients."

    lines = []
    for i, drink in enumerate(drinks, 1):
        fp = drink.get("flavor_profile", {})
        flavor_str = ""
        if include_flavor:
            flavor_str = f" | Flavor: sweet={fp.get('sweet', 0)}, sour={fp.get('sour', 0)}, bitter={fp.get('bitter', 0)}, spirit={fp.get('spirit', 0)}"

        lines.append(
            f"{i}. {drink['name']} (id: {drink['id']})\n"
            f"   Tagline: {drink['tagline']}\n"
            f"   Difficulty: {drink['difficulty']} | Time: {drink['timing_minutes']} min\n"
            f"   Tags: {', '.join(drink['tags'])}{flavor_str}"
        )

    return "\n\n".join(lines)


def format_recipe_for_prompt(drink: dict) -> str:
    """Format a complete recipe for injection into the Recipe Writer prompt.

    Args:
        drink: Complete drink data from get_drink_by_id().

    Returns:
        Formatted string with full recipe details.
    """
    if not drink:
        logger.warning("No drink data to format for recipe prompt")
        return "Recipe not found."

    logger.debug(
        f"Formatting recipe for prompt: {drink.get('name', 'unknown')} (id={drink.get('id', 'unknown')})"
    )

    fp = drink.get("flavor_profile", {})
    ingredients = drink.get("ingredients", [])
    method = drink.get("method", [])

    ing_lines = []
    for ing in ingredients:
        ing_lines.append(f"  - {ing['amount']} {ing['unit']} {ing['item']}")

    method_lines = []
    for i, step in enumerate(method, 1):
        method_lines.append(f"  {i}. {step}")

    return f"""Recipe: {drink["name"]}
ID: {drink["id"]}
Tagline: {drink["tagline"]}
Type: {"Mocktail" if drink["is_mocktail"] else "Cocktail"}
Difficulty: {drink["difficulty"]}
Time: {drink["timing_minutes"]} minutes
Glassware: {drink["glassware"]}
Garnish: {drink["garnish"]}

Flavor Profile:
  Sweet: {fp.get("sweet", 0)}/100
  Sour: {fp.get("sour", 0)}/100
  Bitter: {fp.get("bitter", 0)}/100
  Spirit: {fp.get("spirit", 0)}/100

Ingredients:
{chr(10).join(ing_lines)}

Method:
{chr(10).join(method_lines)}

Tags: {", ".join(drink["tags"])}"""


def format_bottle_recommendations_for_prompt(
    recommendations: list[BottleRecommendation],
) -> str:
    """Format bottle recommendations for injection into Bottle Advisor prompt.

    Args:
        recommendations: List of recommendations from get_unlock_recommendations().

    Returns:
        Formatted string with bottle purchase suggestions.
    """
    logger.debug(
        f"format_bottle_recommendations_for_prompt called with "
        f"{len(recommendations)} recommendations"
    )

    if not recommendations:
        logger.warning("No bottle recommendations to format for prompt")
        return (
            "No new bottles would unlock additional drinks with your current cabinet."
        )

    lines = []
    for rec in recommendations:
        drink_names = rec.get("drinks", [])
        if drink_names:
            # Show up to 5 drink names for better context
            drinks_display = drink_names[:5]
            drinks_str = ", ".join(drinks_display)
            if len(drink_names) > 5:
                drinks_str += f" (+{len(drink_names) - 5} more)"
        else:
            drinks_str = "No specific drinks listed"

        lines.append(
            f"- {rec['ingredient_name']} (ingredient_id: {rec['ingredient']})\n"
            f"  Unlocks: {rec['unlocks']} new drinks\n"
            f"  Drink names that would be unlocked: {drinks_str}"
        )

    return "\n\n".join(lines)
