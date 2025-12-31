"""Flavor profiler tool for analyzing and comparing drink flavor profiles.

This tool provides deterministic flavor analysis functionality with Raja's
conversational personality, allowing agents to understand and compare
the taste characteristics of drinks in an engaging, bartender-friendly way.
"""

from crewai.tools import BaseTool

from src.app.models.drinks import Drink, FlavorProfile
from src.app.services.data_loader import load_all_drinks


class FlavorProfilerTool(BaseTool):
    """Analyze and compare flavor profiles of cocktails and mocktails.

    This tool retrieves flavor profile data for specified drinks and provides
    Raja-style conversational analysis with flavor descriptions, comparisons,
    and recommendations based on taste similarities.
    """

    name: str = "flavor_profiler"
    description: str = (
        "Raja's flavor analysis tool - get personality-rich flavor profiles "
        "and comparisons for cocktails and mocktails. Provide drink IDs to hear "
        "Raja describe their sweet, sour, bitter, and spirit characteristics "
        "with vivid comparisons and pairing recommendations."
    )

    def _run(self, cocktail_ids: list[str]) -> str:
        """Get and compare flavor profiles for the given drink IDs.

        Args:
            cocktail_ids: List of drink IDs to analyze.

        Returns:
            Conversational flavor analysis with Raja's personality,
            including individual profiles and comparison insights.
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

        # Build conversational output with Raja's personality
        return self._format_conversational_output(profiles, not_found, comparison)

    def _format_conversational_output(
        self,
        profiles: list[dict],
        not_found: list[str],
        comparison: dict | None,
    ) -> str:
        """Format flavor profiles as conversational Raja-style output.

        Args:
            profiles: List of extracted drink profiles.
            not_found: List of drink IDs that were not found.
            comparison: Comparison statistics if multiple drinks.

        Returns:
            Conversational string with Raja's personality.
        """
        lines = []

        # Handle empty input
        if not profiles and not not_found:
            return "Arrey yaar, give me some drink IDs to analyze! I can't tell you about flavors without knowing which drinks you're curious about."

        # Opening line with Raja's warmth
        if profiles:
            if len(profiles) == 1:
                lines.append("Acha, let me tell you about this drink, yaar:\n")
            else:
                lines.append("Let me tell you about these flavors, yaar:\n")

        # Individual drink descriptions
        for profile in profiles:
            drink_line = self._format_drink_description(profile)
            lines.append(drink_line)

        # Handle not found drinks
        if not_found:
            not_found_str = ", ".join(not_found)
            lines.append(
                f"\nArrey, I couldn't find these in my collection: {not_found_str}. "
                "Maybe check the spelling, bhai?"
            )

        # Add comparison insights if multiple drinks
        if comparison and len(profiles) >= 2:
            lines.append(self._format_comparison_insights(profiles, comparison))

        # Add recommendation based on similarity
        if len(profiles) >= 2:
            lines.append(self._format_pairing_recommendation(profiles))

        return "\n".join(lines)

    def _format_drink_description(self, profile: dict) -> str:
        """Format a single drink's flavor profile as a conversational description.

        Args:
            profile: Extracted profile dictionary for a drink.

        Returns:
            Formatted drink description line.
        """
        name = profile["name"]
        fp = profile["flavor_profile"]
        analysis = profile["analysis"]

        # Build flavor description
        flavor_parts = []

        # Dominant flavor with intensity descriptor
        dominant = analysis["dominant_flavor"]
        dominant_value = fp[dominant]
        intensity = self._get_intensity_word(dominant_value)

        if dominant == "sweet":
            flavor_parts.append(f"{intensity} sweet")
        elif dominant == "sour":
            flavor_parts.append(f"{intensity} citrus-forward")
        elif dominant == "bitter":
            flavor_parts.append(f"{intensity} bitter notes")

        # Add secondary characteristics
        if fp["sour"] >= 30 and dominant != "sour":
            flavor_parts.append("tangy brightness")
        if fp["sweet"] >= 30 and dominant != "sweet":
            flavor_parts.append("smooth sweetness")
        if fp["bitter"] >= 25 and dominant != "bitter":
            flavor_parts.append("subtle bitter edge")

        # Spirit description
        spirit_desc = self._get_spirit_description(fp["spirit"], profile["is_mocktail"])

        # Style descriptor
        style = analysis["style"]
        style_desc = self._get_style_vibe(style)

        # Compose the line
        flavor_str = (
            " with ".join(flavor_parts[:2])
            if len(flavor_parts) > 1
            else flavor_parts[0]
            if flavor_parts
            else "balanced"
        )

        return f"  {name} - {flavor_str.capitalize()}, {spirit_desc}. {style_desc}"

    def _get_intensity_word(self, value: int) -> str:
        """Convert a 0-100 intensity value to a descriptive word."""
        if value >= 70:
            return "boldly"
        elif value >= 50:
            return "nicely"
        elif value >= 30:
            return "gently"
        else:
            return "subtly"

    def _get_spirit_description(self, spirit: int, is_mocktail: bool) -> str:
        """Get a description of the spirit intensity."""
        if is_mocktail or spirit == 0:
            return "refreshing and alcohol-free"
        elif spirit >= 70:
            return "that spirit really hits you"
        elif spirit >= 50:
            return "nicely boozy"
        elif spirit >= 30:
            return "light and easy-drinking"
        else:
            return "very sessionable"

    def _get_style_vibe(self, style: str) -> str:
        """Get a conversational vibe description for a style."""
        style_vibes = {
            "refreshing/mocktail": "Perfect for when you want something fresh, bhai!",
            "spirit-forward": "This one's for the serious drinkers, yaar.",
            "sour": "A proper sour classic!",
            "bitter/aperitivo": "That Italian aperitivo vibe, first class!",
            "sweet/dessert": "Like dessert in a glass, kya baat hai!",
            "balanced": "Beautifully balanced, smooth as silk.",
        }
        return style_vibes.get(style, "A solid choice!")

    def _format_comparison_insights(
        self, profiles: list[dict], comparison: dict
    ) -> str:
        """Format comparison insights in Raja's voice.

        Args:
            profiles: List of drink profiles.
            comparison: Comparison statistics.

        Returns:
            Conversational comparison string.
        """
        lines = ["\n**Comparison Notes:**"]

        extremes = comparison["extremes"]

        # Highlight interesting contrasts
        sweet_range = comparison["sweet"]["range"]
        sour_range = comparison["sour"]["range"]
        spirit_range = comparison["spirit"]["range"]

        if sweet_range >= 30:
            sweetest = extremes["sweetest"]["id"]
            lines.append(
                f"  - {sweetest.replace('-', ' ').title()} is noticeably sweeter than the others"
            )

        if sour_range >= 30:
            sourest = extremes["sourest"]["id"]
            lines.append(
                f"  - {sourest.replace('-', ' ').title()} brings more citrus punch"
            )

        if spirit_range >= 30:
            strongest = extremes["strongest"]["id"]
            lines.append(
                f"  - {strongest.replace('-', ' ').title()} has more kick, yaar"
            )

        if len(lines) == 1:
            lines.append("  - These drinks have pretty similar profiles, actually!")

        return "\n".join(lines)

    def _format_pairing_recommendation(self, profiles: list[dict]) -> str:
        """Generate pairing recommendation based on flavor similarity.

        Args:
            profiles: List of drink profiles to compare.

        Returns:
            Recommendation string with Raja's personality.
        """
        # Check if drinks share similar styles
        styles = [p["analysis"]["style"] for p in profiles]
        dominants = [p["analysis"]["dominant_flavor"] for p in profiles]

        # Find common ground
        if len(set(styles)) == 1:
            names = " and ".join(p["name"] for p in profiles)
            return (
                f"\nBilkul, {names} are from the same family! "
                f"If you like one, you'll love the other, bhai!"
            )
        elif len(set(dominants)) == 1:
            dominant = dominants[0]
            names = " and ".join(p["name"] for p in profiles)
            return (
                f"\nBoth have that {dominant} character - "
                f"great picks for someone who enjoys {dominant} drinks, yaar!"
            )
        else:
            # Different profiles - note the variety
            return (
                "\nNice variety here! Different vibes for different moods. "
                "That's the beauty of a good bar, yaar!"
            )

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
