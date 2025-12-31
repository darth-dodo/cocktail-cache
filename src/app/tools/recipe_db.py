"""Recipe database tool for querying cocktails and mocktails.

This tool provides deterministic search functionality for the drinks database,
allowing agents to find drinks based on available ingredients. Designed for
Raja the bartender to provide friendly, conversational drink recommendations.
"""

import json
import random
from typing import Literal

from crewai.tools import BaseTool

from src.app.models.drinks import Drink
from src.app.services.data_loader import load_all_drinks, load_cocktails, load_mocktails


class RecipeDBTool(BaseTool):
    """Query cocktails and mocktails database based on available ingredients.

    This tool searches the recipe database and returns drinks that can be made
    with the provided cabinet ingredients. Raja uses this to find perfect drink
    matches and present them in his signature friendly style with Hindi phrases.
    """

    name: str = "recipe_database"
    description: str = (
        "Raja's recipe lookup tool - search cocktails and mocktails by ingredients. "
        "Give me the ingredients from your cabinet, and I'll find drinks you can make. "
        "Optionally filter by 'cocktails', 'mocktails', or 'both'. "
        "Returns conversational recommendations with drink details."
    )

    def _run(
        self,
        cabinet: list[str],
        drink_type: Literal["cocktails", "mocktails", "both"] = "both",
        conversational: bool = True,
    ) -> str:
        """Search for drinks that can be made with the given ingredients.

        Args:
            cabinet: List of ingredient IDs the user has available.
            drink_type: Filter for 'cocktails', 'mocktails', or 'both'.
            conversational: If True, return Raja-style friendly response.
                           If False, return raw JSON data.

        Returns:
            Conversational Raja-style recommendations (default) or
            JSON string with matching drinks and their match scores.
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

        # Return conversational format by default
        if conversational:
            return self._format_conversational(matches, drink_type)

        # Return raw JSON for programmatic use
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

    def _format_conversational(
        self,
        matches: list[dict],
        drink_type: Literal["cocktails", "mocktails", "both"],
    ) -> str:
        """Format matches in Raja's conversational style with Hindi phrases.

        Args:
            matches: List of drink match dictionaries.
            drink_type: The type filter used for the query.

        Returns:
            Raja-style conversational string with drink recommendations.
        """
        # Raja's greeting phrases
        greetings_with_matches = [
            "Arrey yaar, with your cabinet I found these gems:",
            "Bhai, check out what we can make together:",
            "Arrey, your cabinet has some solid options:",
            "Yaar, look at these beauties I found for you:",
            "Bhai sahab, your ingredients unlock these drinks:",
        ]

        greetings_no_matches = [
            "Arrey yaar, no luck with those ingredients. Try adding some basics like lime or simple syrup!",
            "Bhai, nothing matched this time. Maybe stock up on a few essentials?",
            "Yaar, the cabinet needs some love! Add vodka, rum, or gin to unlock more drinks.",
            "Arrey, dry spell here! Consider getting some mixers or base spirits.",
        ]

        # Handle no matches
        if not matches:
            return random.choice(greetings_no_matches)

        # Build conversational response
        lines = [random.choice(greetings_with_matches), ""]

        # Separate perfect matches from partial matches
        perfect_matches = [m for m in matches if m["score"] == 1.0]
        partial_matches = [m for m in matches if m["score"] < 1.0]

        # Show perfect matches first (limit to top 5)
        if perfect_matches:
            for match in perfect_matches[:5]:
                lines.append(self._format_drink_line(match, is_perfect=True))

        # Show top partial matches if we have room
        if partial_matches and len(perfect_matches) < 5:
            remaining_slots = 5 - len(perfect_matches)
            if perfect_matches:
                lines.append("")
                lines.append("Almost there with these (just missing a few things):")
            for match in partial_matches[:remaining_slots]:
                lines.append(self._format_drink_line(match, is_perfect=False))

        # Add summary
        total_perfect = len(perfect_matches)
        total_partial = len(partial_matches)

        lines.append("")
        if total_perfect > 5:
            lines.append(f"...and {total_perfect - 5} more perfect matches, yaar!")
        elif (
            total_partial > 0
            and not partial_matches[: remaining_slots if partial_matches else 0]
        ):
            lines.append(
                f"Plus {total_partial} more drinks if you grab a few extra ingredients!"
            )

        return "\n".join(lines)

    def _format_drink_line(self, match: dict, is_perfect: bool) -> str:
        """Format a single drink in Raja's style.

        Args:
            match: Drink match dictionary.
            is_perfect: Whether all ingredients are available.

        Returns:
            Formatted drink line with emoji and description.
        """
        emoji = "🍹" if match.get("is_mocktail") else "🍸"
        name = match["name"]
        tagline = match.get("tagline", "")

        # Build the drink line
        line = f"{emoji} **{name}**"

        if tagline:
            line += f" - {tagline}"

        # Add missing ingredients note for partial matches
        if not is_perfect:
            missing = match.get("ingredients_missing", [])
            if missing:
                missing_str = ", ".join(missing[:2])
                if len(missing) > 2:
                    missing_str += f" +{len(missing) - 2} more"
                line += f" (need: {missing_str})"

        return line
