"""Substitution finder tool for ingredient replacements.

This tool provides deterministic substitution lookups,
allowing agents to find alternatives for missing ingredients.
"""

import json

from crewai.tools import BaseTool

from src.app.models.ingredients import IngredientsDatabase
from src.app.services.data_loader import load_ingredients, load_substitutions


class SubstitutionFinderTool(BaseTool):
    """Find ingredient substitutions for cocktail making.

    This tool searches the substitutions database to find alternatives
    for missing ingredients, enabling users to make drinks with what they have.
    """

    name: str = "substitution_finder"
    description: str = (
        "Find substitutes for missing cocktail ingredients. "
        "Provide an ingredient ID or name to get possible alternatives. "
        "Includes both similar-category substitutes and NA/alcoholic swaps."
    )

    def _run(self, ingredient: str) -> str:
        """Find substitutes for the given ingredient.

        Args:
            ingredient: Ingredient ID or name to find substitutes for.

        Returns:
            JSON string with substitute options and their categories.
        """
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
                return json.dumps(
                    {
                        "query": query,
                        "found": False,
                        "message": f"Ingredient '{query}' not found. Did you mean one of these?",
                        "suggestions": partial_matches,
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "query": query,
                        "found": False,
                        "message": f"No ingredient found matching '{query}'.",
                        "substitutes": [],
                    },
                    indent=2,
                )

        # Find substitutes
        substitutes = substitutions_db.find_substitutes(ingredient_id)

        # Also check for NA/alcoholic crossover substitutions
        na_to_alc = substitutions_db.non_alcoholic_to_alcoholic.get(ingredient_id, [])
        alc_to_na = substitutions_db.alcoholic_to_non_alcoholic.get(ingredient_id, [])

        # Get ingredient info
        ingredient_info = ingredients_db.find_by_id(ingredient_id)
        ingredient_names = ingredient_info.names if ingredient_info else [ingredient_id]

        # Categorize substitutes
        categorized = self._categorize_substitutes(
            substitutes, na_to_alc, alc_to_na, ingredients_db
        )

        result = {
            "query": query,
            "found": True,
            "ingredient": {
                "id": ingredient_id,
                "names": ingredient_names,
            },
            "substitutes": categorized["same_category"],
            "total_substitutes": len(categorized["same_category"]),
        }

        # Add crossover options if available
        if categorized["na_alternatives"]:
            result["non_alcoholic_alternatives"] = categorized["na_alternatives"]

        if categorized["alcoholic_alternatives"]:
            result["alcoholic_alternatives"] = categorized["alcoholic_alternatives"]

        return json.dumps(result, indent=2)

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
