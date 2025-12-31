"""Unlock calculator tool for next bottle recommendations.

This tool provides deterministic calculations for which new bottles
would unlock the most additional drinks, helping users maximize their bar.
Raja uses this to give friendly shopping advice in his signature style.
"""

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
    the most new drinks. Raja uses this to give friendly shopping
    advice with his signature Bombay bartender personality.
    """

    name: str = "unlock_calculator"
    description: str = (
        "Raja's shopping advisor - find which bottles to add next for maximum value! "
        "Give me your current cabinet ingredients, and I'll tell you which bottles "
        "will unlock the most new drinks. Filter by 'cocktails', 'mocktails', or 'both'. "
        "Returns friendly recommendations with signature drinks each bottle enables."
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
            Conversational string with Raja's shopping recommendations.
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

        # Format conversational output
        return self._format_conversational_output(
            top_recommendations=top_recommendations,
            total_recommendations=len(recommendations),
            already_makeable_count=len(already_makeable_ids),
            cabinet_size=len(cabinet_set),
            drink_type=drink_type,
        )

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

    def _format_ingredient_name(self, ingredient_id: str) -> str:
        """Format ingredient ID into a readable name."""
        # Convert kebab-case or snake_case to Title Case
        return ingredient_id.replace("-", " ").replace("_", " ").title()

    def _get_signature_drink(self, drinks: list[DrinkUnlock]) -> str:
        """Pick a signature drink to highlight from the unlocked drinks.

        Prioritizes well-known classics and non-mocktails when available.
        """
        # Known classics to prioritize
        classics = {
            "negroni",
            "margarita",
            "cosmopolitan",
            "manhattan",
            "martini",
            "daiquiri",
            "mojito",
            "old-fashioned",
            "whiskey-sour",
            "mai-tai",
            "pina-colada",
            "moscow-mule",
            "bloody-mary",
            "espresso-martini",
            "aperol-spritz",
        }

        # First, look for classics
        for drink in drinks:
            if drink["id"].lower() in classics:
                return drink["name"]

        # Then prioritize cocktails over mocktails
        cocktails = [d for d in drinks if not d["is_mocktail"]]
        if cocktails:
            return cocktails[0]["name"]

        # Fall back to first drink
        return drinks[0]["name"] if drinks else "something special"

    def _format_conversational_output(
        self,
        top_recommendations: list[IngredientRecommendation],
        total_recommendations: int,
        already_makeable_count: int,
        cabinet_size: int,
        drink_type: str,
    ) -> str:
        """Format recommendations as Raja's conversational advice."""
        lines = []

        # Opening line with Raja's personality
        if not top_recommendations:
            return (
                "Arrey yaar, looks like you've got quite the collection already! "
                f"With {cabinet_size} ingredients, you can make {already_makeable_count} drinks. "
                "Maybe time to just enjoy what you have, no?"
            )

        # Calculate total potential unlocks
        total_potential = sum(r["new_drinks_unlocked"] for r in top_recommendations)

        lines.append("Want to grow your bar, bhai? Here's my shopping advice:")
        lines.append("")

        # Format each recommendation
        for i, rec in enumerate(top_recommendations, 1):
            ingredient_name = self._format_ingredient_name(rec["ingredient_id"])
            unlock_count = rec["new_drinks_unlocked"]
            signature = self._get_signature_drink(rec["drinks"])

            # Pluralize correctly
            drink_word = "drink" if unlock_count == 1 else "drinks"

            lines.append(
                f"{i}. **{ingredient_name}** - Unlocks {unlock_count} new {drink_word} "
                f"including the {signature}!"
            )

        # Add summary and encouragement
        lines.append("")

        if total_potential >= 10:
            lines.append(
                f"Kya baat hai! These {len(top_recommendations)} bottles could unlock "
                f"{total_potential} new drinks. That's serious bar growth, yaar!"
            )
        elif total_potential >= 5:
            lines.append(
                f"Acha, these {len(top_recommendations)} additions would give you "
                f"{total_potential} more options. Not bad at all!"
            )
        else:
            lines.append(
                f"Bilkul, even small additions help. "
                f"These would unlock {total_potential} new recipes."
            )

        # Add context about current status
        lines.append(
            f"Right now with {cabinet_size} ingredients, you can make "
            f"{already_makeable_count} drinks. Want to level up?"
        )

        return "\n".join(lines)
