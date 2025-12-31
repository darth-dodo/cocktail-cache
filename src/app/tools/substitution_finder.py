"""Substitution finder tool for ingredient replacements.

This tool provides deterministic substitution lookups with Raja's
conversational personality, helping users find alternatives for
missing ingredients in a friendly, bartender-style format.
"""

from crewai.tools import BaseTool

from src.app.models.ingredients import IngredientsDatabase
from src.app.services.data_loader import load_ingredients, load_substitutions

# Raja's conversational phrases for substitution responses
RAJA_PHRASES: dict[str, list[str] | str] = {
    "found": [
        "No problem, bhai! Here are some alternatives:",
        "Don't worry yaar, I've got you covered! Try these:",
        "Acha, no worries! Let me suggest some swaps:",
        "Arrey, happens all the time! These work great instead:",
    ],
    "not_found": [
        "Hmm yaar, I couldn't find that ingredient.",
        "Arrey, that one's not ringing a bell, bhai.",
    ],
    "suggestions": [
        "Did you maybe mean one of these?",
        "Perhaps you're looking for one of these, yaar?",
    ],
    "no_substitutes": [
        "Honestly yaar, this one's pretty unique - hard to substitute!",
        "Acha bhai, this ingredient is special - no easy swaps I'm afraid.",
    ],
    "na_header": "And if you want to keep it non-alcoholic:",
    "alc_header": "Or if you want to add some spirit to it:",
}


class SubstitutionFinderTool(BaseTool):
    """Find ingredient substitutions for cocktail making.

    This tool searches the substitutions database to find alternatives
    for missing ingredients, enabling users to make drinks with what they have.
    Returns conversational output in Raja's friendly bartender style.
    """

    name: str = "substitution_finder"
    description: str = (
        "Raja's ingredient swap finder - helps when you're missing something! "
        "Give me an ingredient name and I'll suggest alternatives from my years "
        "behind the bar. I'll tell you what works, what's close, and even "
        "non-alcoholic or alcoholic crossovers if available."
    )

    def _run(self, ingredient: str) -> str:
        """Find substitutes for the given ingredient.

        Args:
            ingredient: Ingredient ID or name to find substitutes for.

        Returns:
            Conversational response with substitutes in Raja's friendly style.
        """
        import random

        # Normalize the ingredient query
        query = ingredient.lower().strip()

        # Load data
        substitutions_db = load_substitutions()
        ingredients_db = load_ingredients()

        # Try to find the ingredient ID
        ingredient_id = self._resolve_ingredient_id(query, ingredients_db)

        if not ingredient_id:
            # If we cannot resolve the ID, try a partial match
            partial_matches = self._find_partial_matches(query, ingredients_db)
            if partial_matches:
                response = random.choice(RAJA_PHRASES["not_found"])
                response += f" {random.choice(RAJA_PHRASES['suggestions'])}\n"
                for match in partial_matches:
                    primary_name = match["names"][0] if match["names"] else match["id"]
                    response += f"  - **{primary_name}**\n"
                return response
            else:
                return (
                    f"{random.choice(RAJA_PHRASES['not_found'])} "
                    f"'{query}' doesn't match anything in my collection."
                )

        # Find substitutes
        substitutes = substitutions_db.find_substitutes(ingredient_id)

        # Also check for NA/alcoholic crossover substitutions
        na_to_alc = substitutions_db.non_alcoholic_to_alcoholic.get(ingredient_id, [])
        alc_to_na = substitutions_db.alcoholic_to_non_alcoholic.get(ingredient_id, [])

        # Get ingredient info
        ingredient_info = ingredients_db.find_by_id(ingredient_id)
        ingredient_name = (
            ingredient_info.names[0]
            if ingredient_info and ingredient_info.names
            else ingredient_id
        )

        # Categorize substitutes
        categorized = self._categorize_substitutes(
            substitutes, na_to_alc, alc_to_na, ingredients_db
        )

        # Build conversational response
        same_category = categorized["same_category"]
        na_alternatives = categorized["na_alternatives"]
        alc_alternatives = categorized["alcoholic_alternatives"]

        # No substitutes at all
        if not same_category and not na_alternatives and not alc_alternatives:
            return (
                f"No {ingredient_name}? {random.choice(RAJA_PHRASES['no_substitutes'])}"
            )

        # Build the response with Raja's personality
        response_parts = []

        # Header with ingredient name
        if same_category:
            header = random.choice(RAJA_PHRASES["found"])
            response_parts.append(f"No {ingredient_name}? {header}")

            # Add each substitute with taste/usage notes
            for sub in same_category:
                sub_name = sub["names"][0] if sub["names"] else sub["id"]
                note = self._get_substitute_note(ingredient_id, sub["id"])
                response_parts.append(f"  - **{sub_name}** - {note}")

        # Non-alcoholic alternatives
        if na_alternatives:
            if response_parts:
                response_parts.append("")  # blank line
            response_parts.append(str(RAJA_PHRASES["na_header"]))
            for sub in na_alternatives:
                sub_name = sub["names"][0] if sub["names"] else sub["id"]
                note = self._get_substitute_note(ingredient_id, sub["id"], is_na=True)
                response_parts.append(f"  - **{sub_name}** - {note}")

        # Alcoholic alternatives
        if alc_alternatives:
            if response_parts:
                response_parts.append("")  # blank line
            response_parts.append(str(RAJA_PHRASES["alc_header"]))
            for sub in alc_alternatives:
                sub_name = sub["names"][0] if sub["names"] else sub["id"]
                note = self._get_substitute_note(ingredient_id, sub["id"], is_alc=True)
                response_parts.append(f"  - **{sub_name}** - {note}")

        return "\n".join(response_parts)

    def _get_substitute_note(
        self,
        original_id: str,
        substitute_id: str,
        is_na: bool = False,
        is_alc: bool = False,
    ) -> str:
        """Get a brief taste/usage note for a substitute.

        Returns contextual notes based on ingredient categories and types.
        """
        # Common substitute patterns with notes
        substitute_notes = {
            # Whiskeys
            (
                "bourbon",
                "rye_whiskey",
            ): "Spicier kick but works perfectly in most recipes",
            ("bourbon", "tennessee_whiskey"): "Smoother and sweeter, very close taste",
            ("bourbon", "canadian_whisky"): "Lighter body, good for highballs",
            ("rye_whiskey", "bourbon"): "Sweeter and rounder, classic swap",
            # Rums
            ("white_rum", "vodka"): "Neutral spirit, works in a pinch",
            ("dark_rum", "aged_rum"): "Similar depth and caramel notes",
            ("aged_rum", "dark_rum"): "Richer molasses flavor",
            # Gins
            ("gin", "vodka"): "Loses the botanicals but keeps the spirit",
            ("london_dry_gin", "plymouth_gin"): "Slightly softer juniper",
            # Vermouths
            ("sweet_vermouth", "dry_vermouth"): "Much drier result, adjust accordingly",
            ("dry_vermouth", "sweet_vermouth"): "Sweeter result, use less",
            # Citrus
            (
                "lemon_juice",
                "lime_juice",
            ): "Different citrus profile but similar acidity",
            ("lime_juice", "lemon_juice"): "Slightly sweeter citrus notes",
            # Sweeteners
            ("simple_syrup", "honey_syrup"): "Adds floral honey notes",
            ("honey_syrup", "simple_syrup"): "Cleaner sweetness without honey flavor",
            ("agave_syrup", "simple_syrup"): "Neutral sweetness, good substitute",
            # Bitters
            (
                "angostura_bitters",
                "orange_bitters",
            ): "Different flavor profile, use carefully",
            # Liqueurs
            ("triple_sec", "cointreau"): "Premium orange flavor, same family",
            ("cointreau", "triple_sec"): "More affordable, slightly sweeter",
            ("triple_sec", "grand_marnier"): "Cognac base adds richness",
        }

        # Check for specific pairing
        key = (original_id.lower(), substitute_id.lower())
        if key in substitute_notes:
            return substitute_notes[key]

        # Generic notes based on context
        if is_na:
            return "Non-alcoholic option, keeps the flavor spirit"
        if is_alc:
            return "Adds spirit to your drink"

        # Fallback generic notes based on ingredient category patterns
        sub_lower = substitute_id.lower()
        if "whiskey" in sub_lower or "whisky" in sub_lower or "bourbon" in sub_lower:
            return "Similar whiskey family, adjust to taste"
        if "rum" in sub_lower:
            return "Rum family swap, flavor varies by age"
        if "gin" in sub_lower:
            return "Botanical profiles may differ"
        if "vodka" in sub_lower:
            return "Clean and neutral base spirit"
        if "vermouth" in sub_lower:
            return "Fortified wine, check sweetness level"
        if "syrup" in sub_lower:
            return "Sweetness similar, flavor may differ"
        if "juice" in sub_lower:
            return "Fresh is always best!"
        if "bitters" in sub_lower:
            return "Different flavor notes, use sparingly"
        if "liqueur" in sub_lower:
            return "Flavor profiles vary, taste as you go"

        return "Good alternative, similar application"

    def _resolve_ingredient_id(
        self, query: str, ingredients_db: IngredientsDatabase
    ) -> str | None:
        """Resolve a query to an ingredient ID.

        Checks both IDs and name aliases.
        """
        # First try direct ID match
        if ingredients_db.find_by_id(query):
            return query

        # Search through all ingredients for name matches
        for ingredient in ingredients_db.all_ingredients():
            # Check if query matches the ID
            if ingredient.id.lower() == query:
                return ingredient.id

            # Check if query matches any name alias
            for name in ingredient.names:
                if name.lower() == query:
                    return ingredient.id

        return None

    def _find_partial_matches(
        self, query: str, ingredients_db: IngredientsDatabase
    ) -> list[dict]:
        """Find ingredients that partially match the query."""
        matches = []

        for ingredient in ingredients_db.all_ingredients():
            # Check ID
            if query in ingredient.id.lower():
                matches.append(
                    {
                        "id": ingredient.id,
                        "names": ingredient.names,
                    }
                )
                continue

            # Check names
            for name in ingredient.names:
                if query in name.lower():
                    matches.append(
                        {
                            "id": ingredient.id,
                            "names": ingredient.names,
                        }
                    )
                    break

        return matches[:5]  # Limit to top 5 suggestions

    def _categorize_substitutes(
        self,
        same_category: list[str],
        na_alternatives: list[str],
        alc_alternatives: list[str],
        ingredients_db: IngredientsDatabase,
    ) -> dict:
        """Categorize substitutes with their details."""

        def enrich(substitute_ids: list[str]) -> list[dict]:
            enriched = []
            for sub_id in substitute_ids:
                info = ingredients_db.find_by_id(sub_id)
                enriched.append(
                    {
                        "id": sub_id,
                        "names": info.names if info else [sub_id],
                    }
                )
            return enriched

        return {
            "same_category": enrich(same_category),
            "na_alternatives": enrich(na_alternatives),
            "alcoholic_alternatives": enrich(alc_alternatives),
        }
