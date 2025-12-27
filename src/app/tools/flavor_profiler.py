"""Flavor profiler tool for analyzing and comparing drink flavor profiles.

This tool provides deterministic flavor analysis functionality,
allowing agents to understand and compare the taste characteristics of drinks.
"""

import json

from crewai.tools import BaseTool

from src.app.models.drinks import Drink, FlavorProfile
from src.app.services.data_loader import load_all_drinks


class FlavorProfilerTool(BaseTool):
    """Analyze and compare flavor profiles of cocktails and mocktails.

    This tool retrieves flavor profile data for specified drinks and can
    provide comparison analysis between multiple drinks.
    """

    name: str = "flavor_profiler"
    description: str = (
        "Analyze and compare flavor profiles of drinks. "
        "Provide a list of cocktail/mocktail IDs to get their flavor profiles "
        "(sweet, sour, bitter, spirit intensity on 0-100 scales). "
        "Returns individual profiles and comparison statistics."
    )

    def _run(self, cocktail_ids: list[str]) -> str:
        """Get and compare flavor profiles for the given drink IDs.

        Args:
            cocktail_ids: List of drink IDs to analyze.

        Returns:
            JSON string with flavor profiles and comparison data.
        """
        # Normalize IDs
        normalized_ids = [cid.lower().strip() for cid in cocktail_ids]

        # Build a lookup of all drinks
        all_drinks = load_all_drinks()
        drinks_by_id: dict[str, Drink] = {d.id.lower(): d for d in all_drinks}

        # Collect profiles for requested drinks
        profiles = []
        not_found = []

        for drink_id in normalized_ids:
            drink = drinks_by_id.get(drink_id)
            if drink:
                profiles.append(self._extract_profile(drink))
            else:
                not_found.append(drink_id)

        # Calculate comparison statistics if we have multiple drinks
        comparison = None
        if len(profiles) >= 2:
            comparison = self._calculate_comparison(profiles)

        result = {
            "query": {"cocktail_ids": normalized_ids},
            "found": len(profiles),
            "not_found": not_found if not_found else None,
            "profiles": profiles,
            "comparison": comparison,
        }

        # Remove None values for cleaner output
        result = {k: v for k, v in result.items() if v is not None}

        return json.dumps(result, indent=2)

    def _extract_profile(self, drink: Drink) -> dict:
        """Extract flavor profile data from a drink."""
        fp = drink.flavor_profile

        # Calculate derived characteristics
        total_intensity = fp.sweet + fp.sour + fp.bitter
        balance_score = self._calculate_balance_score(fp.sweet, fp.sour, fp.bitter)

        # Determine dominant flavor
        flavors = {"sweet": fp.sweet, "sour": fp.sour, "bitter": fp.bitter}
        dominant = max(flavors, key=lambda k: flavors[k])

        # Categorize the drink style
        style = self._categorize_style(fp)

        return {
            "id": drink.id,
            "name": drink.name,
            "is_mocktail": drink.is_mocktail,
            "flavor_profile": {
                "sweet": fp.sweet,
                "sour": fp.sour,
                "bitter": fp.bitter,
                "spirit": fp.spirit,
            },
            "analysis": {
                "dominant_flavor": dominant,
                "total_intensity": total_intensity,
                "balance_score": round(balance_score, 2),
                "style": style,
                "spirit_forward": fp.spirit >= 60,
            },
            "tags": drink.tags,
        }

    def _calculate_balance_score(self, sweet: int, sour: int, bitter: int) -> float:
        """Calculate how balanced a drink is (0-100 scale).

        A perfectly balanced drink has equal non-zero values.
        Higher score means more balanced.
        """
        values = [sweet, sour, bitter]
        non_zero = [v for v in values if v > 0]

        if len(non_zero) < 2:
            # Single-note drinks are not balanced
            return 0.0

        avg = sum(non_zero) / len(non_zero)
        if avg == 0:
            return 0.0

        # Calculate standard deviation
        variance = sum((v - avg) ** 2 for v in non_zero) / len(non_zero)
        std_dev = variance**0.5

        # Convert to balance score (lower variance = higher balance)
        # Max std_dev for 0-100 scale values is about 50
        balance = max(0.0, 100.0 - (std_dev * 2))
        return float(balance)

    def _categorize_style(self, fp: FlavorProfile) -> str:
        """Categorize the drink style based on flavor profile."""
        # Check mocktail first since it's a hard category
        if fp.spirit == 0:
            return "refreshing/mocktail"
        elif fp.spirit >= 70:
            return "spirit-forward"
        elif fp.sour >= 40 and fp.sweet >= 30:
            return "sour"
        elif fp.bitter >= 40:
            return "bitter/aperitivo"
        elif fp.sweet >= 50:
            return "sweet/dessert"
        else:
            return "balanced"

    def _calculate_comparison(self, profiles: list[dict]) -> dict:
        """Calculate comparison statistics across multiple profiles."""
        # Extract raw flavor values
        sweets = [p["flavor_profile"]["sweet"] for p in profiles]
        sours = [p["flavor_profile"]["sour"] for p in profiles]
        bitters = [p["flavor_profile"]["bitter"] for p in profiles]
        spirits = [p["flavor_profile"]["spirit"] for p in profiles]

        def stats(values: list[int]) -> dict:
            if not values:
                return {"min": 0, "max": 0, "avg": 0, "range": 0}
            return {
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 1),
                "range": max(values) - min(values),
            }

        # Find most/least of each
        most_sweet = max(profiles, key=lambda p: p["flavor_profile"]["sweet"])
        most_sour = max(profiles, key=lambda p: p["flavor_profile"]["sour"])
        most_bitter = max(profiles, key=lambda p: p["flavor_profile"]["bitter"])
        most_spirit = max(profiles, key=lambda p: p["flavor_profile"]["spirit"])

        return {
            "sweet": stats(sweets),
            "sour": stats(sours),
            "bitter": stats(bitters),
            "spirit": stats(spirits),
            "extremes": {
                "sweetest": {
                    "id": most_sweet["id"],
                    "value": most_sweet["flavor_profile"]["sweet"],
                },
                "sourest": {
                    "id": most_sour["id"],
                    "value": most_sour["flavor_profile"]["sour"],
                },
                "most_bitter": {
                    "id": most_bitter["id"],
                    "value": most_bitter["flavor_profile"]["bitter"],
                },
                "strongest": {
                    "id": most_spirit["id"],
                    "value": most_spirit["flavor_profile"]["spirit"],
                },
            },
        }
