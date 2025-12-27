"""Recipe database tool for querying cocktails and mocktails.

This tool provides deterministic search functionality for the drinks database,
allowing agents to find drinks based on available ingredients.
"""

import json
from typing import Literal

from crewai.tools import BaseTool

from src.app.models.drinks import Drink
from src.app.services.data_loader import load_all_drinks, load_cocktails, load_mocktails


class RecipeDBTool(BaseTool):
    """Query cocktails and mocktails database based on available ingredients.

    This tool searches the recipe database and returns drinks that can be made
    with the provided cabinet ingredients. Each result includes a match score
    indicating how complete the ingredient match is.
    """

    name: str = "recipe_database"
    description: str = (
        "Search and retrieve cocktail/mocktail recipes by ingredients. "
        "Provide a list of ingredients you have, and optionally filter by "
        "drink type ('cocktails', 'mocktails', or 'both'). "
        "Returns matching drinks with completeness scores."
    )

    def _run(
        self,
        cabinet: list[str],
        drink_type: Literal["cocktails", "mocktails", "both"] = "both",
    ) -> str:
        """Search for drinks that can be made with the given ingredients.

        Args:
            cabinet: List of ingredient IDs the user has available.
            drink_type: Filter for 'cocktails', 'mocktails', or 'both'.

        Returns:
            JSON string with matching drinks and their match scores.
            Score of 1.0 means all ingredients are available.
        """
        # Normalize cabinet ingredients to lowercase for matching
        cabinet_set = {ing.lower().strip() for ing in cabinet}

        # Load appropriate drinks based on type filter
        drinks = self._load_drinks_by_type(drink_type)

        # Calculate matches for each drink
        matches = []
        for drink in drinks:
            match_info = self._calculate_match(drink, cabinet_set)
            if match_info["score"] > 0:
                matches.append(match_info)

        # Sort by score (highest first), then by name
        matches.sort(key=lambda x: (-x["score"], x["name"]))

        result = {
            "query": {
                "cabinet": list(cabinet_set),
                "drink_type": drink_type,
            },
            "total_matches": len(matches),
            "matches": matches,
        }

        return json.dumps(result, indent=2)

    def _load_drinks_by_type(
        self, drink_type: Literal["cocktails", "mocktails", "both"]
    ) -> list[Drink]:
        """Load drinks filtered by type."""
        if drink_type == "cocktails":
            return load_cocktails()
        elif drink_type == "mocktails":
            return load_mocktails()
        else:
            return load_all_drinks()

    def _calculate_match(self, drink: Drink, cabinet_set: set[str]) -> dict:
        """Calculate how well a drink matches the available ingredients.

        Returns a dict with drink info and match details.
        """
        required_ingredients = [ing.item.lower() for ing in drink.ingredients]
        total_required = len(required_ingredients)

        if total_required == 0:
            return {"score": 0}

        # Find which ingredients we have and which are missing
        have = []
        missing = []

        for ing in required_ingredients:
            if ing in cabinet_set:
                have.append(ing)
            else:
                missing.append(ing)

        score = len(have) / total_required

        return {
            "id": drink.id,
            "name": drink.name,
            "tagline": drink.tagline,
            "is_mocktail": drink.is_mocktail,
            "difficulty": drink.difficulty,
            "timing_minutes": drink.timing_minutes,
            "glassware": drink.glassware,
            "tags": drink.tags,
            "score": round(score, 3),
            "ingredients_have": have,
            "ingredients_missing": missing,
            "total_ingredients": total_required,
        }
