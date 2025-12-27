"""Unlock calculator tool for next bottle recommendations.

This tool provides deterministic calculations for which new bottles
would unlock the most additional drinks, helping users maximize their bar.
"""

import json
from typing import Literal, TypedDict

from crewai.tools import BaseTool

from src.app.models.drinks import Drink
from src.app.services.data_loader import load_all_drinks, load_unlock_scores


class DrinkUnlock(TypedDict):
    """Type for drink unlock info in recommendations."""

    id: str
    name: str
    is_mocktail: bool
    difficulty: str


class IngredientRecommendation(TypedDict):
    """Type for ingredient recommendation entry."""

    ingredient_id: str
    new_drinks_unlocked: int
    drinks: list[DrinkUnlock]


class UnlockCalculatorTool(BaseTool):
    """Calculate which bottles unlock the most new drinks.

    This tool analyzes the user's current cabinet and recommends
    which new bottles would provide the best ROI by unlocking
    the most new drinks.
    """

    name: str = "unlock_calculator"
    description: str = (
        "Find which bottles to buy next for maximum ROI. "
        "Provide your current cabinet ingredients, and optionally filter by "
        "drink type ('cocktails', 'mocktails', or 'both') and limit results. "
        "Returns recommendations ranked by how many NEW drinks each bottle unlocks."
    )

    def _run(
        self,
        cabinet: list[str],
        drink_type: Literal["cocktails", "mocktails", "both"] = "both",
        limit: int = 5,
    ) -> str:
        """Calculate the best bottles to buy next.

        Args:
            cabinet: List of ingredient IDs the user already has.
            drink_type: Filter for 'cocktails', 'mocktails', or 'both'.
            limit: Maximum number of recommendations to return.

        Returns:
            JSON string with ranked bottle recommendations.
        """
        # Normalize cabinet
        cabinet_set = {ing.lower().strip() for ing in cabinet}

        # Load data
        unlock_scores = load_unlock_scores()
        all_drinks = load_all_drinks()

        # Find drinks we can already make (have all ingredients)
        already_makeable = self._get_makeable_drinks(cabinet_set, all_drinks)
        already_makeable_ids = {d.id.lower() for d in already_makeable}

        # Calculate unlock potential for each ingredient we do not have
        recommendations: list[IngredientRecommendation] = []

        for ingredient_id, unlocked_drinks in unlock_scores.items():
            # Skip if we already have this ingredient
            if ingredient_id.lower() in cabinet_set:
                continue

            # Calculate how many NEW drinks this ingredient would help unlock
            new_unlocks: list[DrinkUnlock] = []

            for unlock_info in unlocked_drinks:
                drink_id = unlock_info.id.lower()

                # Skip if we can already make this drink
                if drink_id in already_makeable_ids:
                    continue

                # Skip if drink type does not match filter
                if drink_type == "cocktails" and unlock_info.is_mocktail:
                    continue
                if drink_type == "mocktails" and not unlock_info.is_mocktail:
                    continue

                # Check if adding this ingredient would complete the drink
                # (we need all OTHER ingredients too)
                other_needed = {o.lower() for o in unlock_info.other}
                have_others = other_needed.issubset(cabinet_set)

                if have_others:
                    # This ingredient would complete this drink
                    new_unlocks.append(
                        {
                            "id": unlock_info.id,
                            "name": unlock_info.name,
                            "is_mocktail": unlock_info.is_mocktail,
                            "difficulty": unlock_info.difficulty,
                        }
                    )

            if new_unlocks:
                recommendations.append(
                    {
                        "ingredient_id": ingredient_id,
                        "new_drinks_unlocked": len(new_unlocks),
                        "drinks": new_unlocks,
                    }
                )

        # Sort by number of new drinks unlocked (highest first)
        recommendations.sort(key=lambda x: x["new_drinks_unlocked"], reverse=True)

        # Apply limit
        top_recommendations = recommendations[:limit]

        # Calculate summary statistics
        total_potential_unlocks = sum(
            r["new_drinks_unlocked"] for r in top_recommendations
        )

        result = {
            "query": {
                "cabinet_size": len(cabinet_set),
                "drink_type": drink_type,
                "limit": limit,
            },
            "current_status": {
                "drinks_you_can_make": len(already_makeable_ids),
                "drinks_makeable": [
                    {"id": d.id, "name": d.name, "is_mocktail": d.is_mocktail}
                    for d in sorted(already_makeable, key=lambda x: x.name)[:10]
                ],
            },
            "recommendations": top_recommendations,
            "total_recommendations": len(recommendations),
            "summary": {
                "top_bottles_shown": len(top_recommendations),
                "potential_new_drinks": total_potential_unlocks,
            },
        }

        return json.dumps(result, indent=2)

    def _get_makeable_drinks(
        self, cabinet_set: set[str], all_drinks: list[Drink]
    ) -> list[Drink]:
        """Find all drinks that can be made with the current cabinet."""
        makeable = []

        for drink in all_drinks:
            required = {ing.item.lower() for ing in drink.ingredients}
            if required.issubset(cabinet_set):
                makeable.append(drink)

        return makeable
