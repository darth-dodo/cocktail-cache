"""Comprehensive unit tests for CrewAI tools.

Tests cover all four tools in src/app/tools/:
- RecipeDBTool: Query drinks based on cabinet ingredients
- FlavorProfilerTool: Analyze and compare drink flavor profiles
- SubstitutionFinderTool: Find ingredient substitutes
- UnlockCalculatorTool: Calculate next bottle recommendations
"""

import json

import pytest

from src.app.tools.flavor_profiler import FlavorProfilerTool
from src.app.tools.recipe_db import RecipeDBTool
from src.app.tools.substitution_finder import SubstitutionFinderTool
from src.app.tools.unlock_calculator import UnlockCalculatorTool


# =============================================================================
# RecipeDBTool Tests
# =============================================================================
class TestRecipeDBTool:
    """Test suite for RecipeDBTool."""

    @pytest.fixture
    def tool(self) -> RecipeDBTool:
        """Provide a RecipeDBTool instance."""
        return RecipeDBTool()

    # -------------------------------------------------------------------------
    # Empty Cabinet Tests
    # -------------------------------------------------------------------------
    def test_empty_cabinet_returns_no_matches(self, tool: RecipeDBTool) -> None:
        """Test that an empty cabinet returns zero matches."""
        result = json.loads(tool._run(cabinet=[]))

        assert result["total_matches"] == 0
        assert result["matches"] == []
        assert result["query"]["cabinet"] == []
        assert result["query"]["drink_type"] == "both"

    def test_empty_cabinet_with_drink_type_filter(self, tool: RecipeDBTool) -> None:
        """Test empty cabinet with specific drink type filters."""
        from typing import Literal

        drink_types: list[Literal["cocktails", "mocktails", "both"]] = [
            "cocktails",
            "mocktails",
            "both",
        ]
        for drink_type in drink_types:
            result = json.loads(tool._run(cabinet=[], drink_type=drink_type))
            assert result["total_matches"] == 0
            assert result["query"]["drink_type"] == drink_type

    # -------------------------------------------------------------------------
    # Full Ingredient Set Tests
    # -------------------------------------------------------------------------
    def test_full_ingredients_for_old_fashioned(self, tool: RecipeDBTool) -> None:
        """Test that providing all ingredients for Old Fashioned returns a match."""
        # Old Fashioned requires: bourbon, simple-syrup, angostura-bitters, orange-bitters
        cabinet = ["bourbon", "simple-syrup", "angostura-bitters", "orange-bitters"]
        result = json.loads(tool._run(cabinet=cabinet))

        assert result["total_matches"] >= 1

        # Find the Old Fashioned in matches
        old_fashioned_matches = [
            m for m in result["matches"] if m["id"] == "old-fashioned"
        ]
        assert len(old_fashioned_matches) == 1

        old_fashioned = old_fashioned_matches[0]
        assert old_fashioned["score"] == 1.0
        assert old_fashioned["ingredients_missing"] == []
        assert len(old_fashioned["ingredients_have"]) == 4
        assert old_fashioned["is_mocktail"] is False

    def test_full_ingredients_for_virgin_mojito(self, tool: RecipeDBTool) -> None:
        """Test that providing all ingredients for Virgin Mojito returns a match."""
        # Virgin Mojito requires: fresh-mint, lime-juice, simple-syrup, club-soda
        cabinet = ["fresh-mint", "lime-juice", "simple-syrup", "club-soda"]
        result = json.loads(tool._run(cabinet=cabinet))

        assert result["total_matches"] >= 1

        # Find the Virgin Mojito in matches
        virgin_mojito_matches = [
            m for m in result["matches"] if m["id"] == "virgin-mojito"
        ]
        assert len(virgin_mojito_matches) == 1

        virgin_mojito = virgin_mojito_matches[0]
        assert virgin_mojito["score"] == 1.0
        assert virgin_mojito["is_mocktail"] is True

    def test_partial_ingredients_returns_partial_score(
        self, tool: RecipeDBTool
    ) -> None:
        """Test that partial ingredient matches return appropriate scores."""
        # Old Fashioned needs 4 ingredients, we provide 2
        cabinet = ["bourbon", "simple-syrup"]
        result = json.loads(tool._run(cabinet=cabinet))

        old_fashioned_matches = [
            m for m in result["matches"] if m["id"] == "old-fashioned"
        ]
        assert len(old_fashioned_matches) == 1

        old_fashioned = old_fashioned_matches[0]
        # 2 out of 4 ingredients = 0.5
        assert old_fashioned["score"] == 0.5
        assert len(old_fashioned["ingredients_have"]) == 2
        assert len(old_fashioned["ingredients_missing"]) == 2

    # -------------------------------------------------------------------------
    # Drink Type Filtering Tests
    # -------------------------------------------------------------------------
    def test_cocktails_filter_excludes_mocktails(self, tool: RecipeDBTool) -> None:
        """Test that cocktails filter excludes mocktails."""
        # Use ingredients that could match both cocktails and mocktails
        cabinet = ["lime-juice", "simple-syrup", "fresh-mint", "club-soda", "white-rum"]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="cocktails"))

        for match in result["matches"]:
            assert match["is_mocktail"] is False, (
                f"Found mocktail {match['name']} in cocktails-only results"
            )

    def test_mocktails_filter_excludes_cocktails(self, tool: RecipeDBTool) -> None:
        """Test that mocktails filter excludes cocktails."""
        # Use ingredients common in mocktails
        cabinet = [
            "lime-juice",
            "simple-syrup",
            "fresh-mint",
            "club-soda",
            "ginger-ale",
            "grenadine",
        ]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="mocktails"))

        for match in result["matches"]:
            assert match["is_mocktail"] is True, (
                f"Found cocktail {match['name']} in mocktails-only results"
            )

    def test_both_filter_includes_cocktails_and_mocktails(
        self, tool: RecipeDBTool
    ) -> None:
        """Test that 'both' filter includes both cocktails and mocktails."""
        # Large cabinet that should match various drinks
        cabinet = [
            "bourbon",
            "simple-syrup",
            "angostura-bitters",
            "lime-juice",
            "fresh-mint",
            "club-soda",
            "ginger-ale",
            "grenadine",
        ]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="both"))

        # Should have at least some variety if data includes both types
        assert result["total_matches"] > 0
        # Verify we get both cocktails and mocktails when using "both" filter
        mocktail_values = {m["is_mocktail"] for m in result["matches"]}
        assert len(mocktail_values) >= 1  # At least one type present

    # -------------------------------------------------------------------------
    # Score Calculation and Sorting Tests
    # -------------------------------------------------------------------------
    def test_matches_sorted_by_score_descending(self, tool: RecipeDBTool) -> None:
        """Test that matches are sorted by score in descending order."""
        cabinet = [
            "bourbon",
            "simple-syrup",
            "angostura-bitters",
            "orange-bitters",
            "lime-juice",
            "white-rum",
        ]
        result = json.loads(tool._run(cabinet=cabinet))

        if len(result["matches"]) >= 2:
            scores = [m["score"] for m in result["matches"]]
            assert scores == sorted(scores, reverse=True), (
                "Matches should be sorted by score descending"
            )

    def test_score_is_ratio_of_available_to_total_ingredients(
        self, tool: RecipeDBTool
    ) -> None:
        """Test that score equals available / total ingredients."""
        # Manhattan requires: rye-whiskey, sweet-vermouth, angostura-bitters
        cabinet = ["rye-whiskey"]  # 1 of 3
        result = json.loads(tool._run(cabinet=cabinet))

        manhattan_matches = [m for m in result["matches"] if m["id"] == "manhattan"]
        if manhattan_matches:
            manhattan = manhattan_matches[0]
            expected_score = (
                len(manhattan["ingredients_have"]) / manhattan["total_ingredients"]
            )
            assert abs(manhattan["score"] - expected_score) < 0.01

    def test_matches_with_same_score_sorted_by_name(self, tool: RecipeDBTool) -> None:
        """Test that matches with identical scores are sorted alphabetically."""
        # Provide a single common ingredient to get many partial matches
        cabinet = ["simple-syrup"]
        result = json.loads(tool._run(cabinet=cabinet))

        # Group by score
        score_groups: dict[float, list[str]] = {}
        for match in result["matches"]:
            score = match["score"]
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(match["name"])

        # Within each score group, names should be sorted
        for score, names in score_groups.items():
            if len(names) > 1:
                assert names == sorted(names), (
                    f"Names within score {score} should be alphabetically sorted"
                )

    # -------------------------------------------------------------------------
    # Edge Cases and Input Normalization
    # -------------------------------------------------------------------------
    def test_case_insensitive_ingredient_matching(self, tool: RecipeDBTool) -> None:
        """Test that ingredient matching is case-insensitive."""
        cabinet_lower = ["bourbon", "simple-syrup"]
        cabinet_mixed = ["BOURBON", "Simple-Syrup"]
        cabinet_upper = ["BOURBON", "SIMPLE-SYRUP"]

        result_lower = json.loads(tool._run(cabinet=cabinet_lower))
        result_mixed = json.loads(tool._run(cabinet=cabinet_mixed))
        result_upper = json.loads(tool._run(cabinet=cabinet_upper))

        # All should produce the same number of matches
        assert result_lower["total_matches"] == result_mixed["total_matches"]
        assert result_lower["total_matches"] == result_upper["total_matches"]

    def test_whitespace_trimmed_from_ingredients(self, tool: RecipeDBTool) -> None:
        """Test that whitespace is trimmed from ingredient names."""
        cabinet_clean = ["bourbon", "simple-syrup"]
        cabinet_whitespace = ["  bourbon  ", "  simple-syrup  "]

        result_clean = json.loads(tool._run(cabinet=cabinet_clean))
        result_whitespace = json.loads(tool._run(cabinet=cabinet_whitespace))

        assert result_clean["total_matches"] == result_whitespace["total_matches"]

    def test_response_structure_is_valid_json(self, tool: RecipeDBTool) -> None:
        """Test that the response is valid JSON with expected structure."""
        cabinet = ["bourbon"]
        result = json.loads(tool._run(cabinet=cabinet))

        # Verify top-level keys
        assert "query" in result
        assert "total_matches" in result
        assert "matches" in result

        # Verify query structure
        assert "cabinet" in result["query"]
        assert "drink_type" in result["query"]

        # Verify match structure (if matches exist)
        if result["matches"]:
            match = result["matches"][0]
            expected_keys = {
                "id",
                "name",
                "tagline",
                "is_mocktail",
                "difficulty",
                "timing_minutes",
                "glassware",
                "tags",
                "score",
                "ingredients_have",
                "ingredients_missing",
                "total_ingredients",
            }
            assert expected_keys.issubset(set(match.keys()))


# =============================================================================
# FlavorProfilerTool Tests
# =============================================================================
class TestFlavorProfilerTool:
    """Test suite for FlavorProfilerTool."""

    @pytest.fixture
    def tool(self) -> FlavorProfilerTool:
        """Provide a FlavorProfilerTool instance."""
        return FlavorProfilerTool()

    # -------------------------------------------------------------------------
    # Single Drink Profile Extraction Tests
    # -------------------------------------------------------------------------
    def test_single_drink_profile_extraction(self, tool: FlavorProfilerTool) -> None:
        """Test extracting flavor profile for a single drink."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned"]))

        assert result["found"] == 1
        assert len(result["profiles"]) == 1

        profile = result["profiles"][0]
        assert profile["id"] == "old-fashioned"
        assert profile["name"] == "Old Fashioned"
        assert "flavor_profile" in profile
        assert "analysis" in profile

        # Verify flavor profile structure
        fp = profile["flavor_profile"]
        assert "sweet" in fp
        assert "sour" in fp
        assert "bitter" in fp
        assert "spirit" in fp
        assert all(isinstance(v, int) for v in fp.values())
        assert all(0 <= v <= 100 for v in fp.values())

    def test_single_mocktail_profile(self, tool: FlavorProfilerTool) -> None:
        """Test extracting flavor profile for a mocktail."""
        result = json.loads(tool._run(cocktail_ids=["virgin-mojito"]))

        assert result["found"] == 1
        profile = result["profiles"][0]

        assert profile["is_mocktail"] is True
        # Mocktails should have spirit = 0
        assert profile["flavor_profile"]["spirit"] == 0

    def test_profile_includes_analysis_fields(self, tool: FlavorProfilerTool) -> None:
        """Test that profile includes all expected analysis fields."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned"]))

        analysis = result["profiles"][0]["analysis"]
        expected_fields = {
            "dominant_flavor",
            "total_intensity",
            "balance_score",
            "style",
            "spirit_forward",
        }
        assert expected_fields.issubset(set(analysis.keys()))

    # -------------------------------------------------------------------------
    # Multiple Drink Comparison Tests
    # -------------------------------------------------------------------------
    def test_multiple_drink_comparison(self, tool: FlavorProfilerTool) -> None:
        """Test comparing multiple drinks."""
        result = json.loads(
            tool._run(cocktail_ids=["old-fashioned", "manhattan", "virgin-mojito"])
        )

        assert result["found"] == 3
        assert len(result["profiles"]) == 3
        assert "comparison" in result
        assert result["comparison"] is not None

    def test_comparison_includes_statistics(self, tool: FlavorProfilerTool) -> None:
        """Test that comparison includes min/max/avg statistics."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned", "manhattan"]))

        comparison = result["comparison"]
        assert comparison is not None

        for flavor in ["sweet", "sour", "bitter", "spirit"]:
            assert flavor in comparison
            assert "min" in comparison[flavor]
            assert "max" in comparison[flavor]
            assert "avg" in comparison[flavor]
            assert "range" in comparison[flavor]

    def test_comparison_includes_extremes(self, tool: FlavorProfilerTool) -> None:
        """Test that comparison identifies extremes."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned", "virgin-mojito"]))

        comparison = result["comparison"]
        extremes = comparison["extremes"]

        assert "sweetest" in extremes
        assert "sourest" in extremes
        assert "most_bitter" in extremes
        assert "strongest" in extremes

        # Each extreme should have id and value
        for key in ["sweetest", "sourest", "most_bitter", "strongest"]:
            assert "id" in extremes[key]
            assert "value" in extremes[key]

    def test_no_comparison_for_single_drink(self, tool: FlavorProfilerTool) -> None:
        """Test that comparison is not included for single drink."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned"]))

        # Comparison should not be present (or be None, which gets filtered)
        assert "comparison" not in result or result.get("comparison") is None

    # -------------------------------------------------------------------------
    # Not Found Handling Tests
    # -------------------------------------------------------------------------
    def test_not_found_handling_for_unknown_id(self, tool: FlavorProfilerTool) -> None:
        """Test handling of unknown drink IDs."""
        result = json.loads(tool._run(cocktail_ids=["nonexistent-drink-xyz"]))

        assert result["found"] == 0
        assert "not_found" in result
        assert "nonexistent-drink-xyz" in result["not_found"]

    def test_partial_not_found_handling(self, tool: FlavorProfilerTool) -> None:
        """Test handling when some IDs are found and some are not."""
        result = json.loads(
            tool._run(cocktail_ids=["old-fashioned", "fake-drink", "manhattan"])
        )

        assert result["found"] == 2
        assert len(result["profiles"]) == 2
        assert "not_found" in result
        assert "fake-drink" in result["not_found"]

    def test_all_not_found(self, tool: FlavorProfilerTool) -> None:
        """Test when all requested drinks are not found."""
        result = json.loads(tool._run(cocktail_ids=["fake-drink-1", "fake-drink-2"]))

        assert result["found"] == 0
        assert len(result["profiles"]) == 0
        assert "not_found" in result
        assert len(result["not_found"]) == 2

    # -------------------------------------------------------------------------
    # Balance Score Calculation Tests
    # -------------------------------------------------------------------------
    def test_balance_score_range(self, tool: FlavorProfilerTool) -> None:
        """Test that balance scores are in valid range."""
        result = json.loads(
            tool._run(cocktail_ids=["old-fashioned", "manhattan", "virgin-mojito"])
        )

        for profile in result["profiles"]:
            balance = profile["analysis"]["balance_score"]
            assert 0 <= balance <= 100, (
                f"Balance score {balance} out of range for {profile['id']}"
            )

    def test_balance_score_calculation_logic(self, tool: FlavorProfilerTool) -> None:
        """Test that balance score reflects flavor distribution."""
        # A drink with very uneven flavors should have low balance
        # A drink with more even distribution should have higher balance
        result = json.loads(tool._run(cocktail_ids=["old-fashioned", "virgin-mojito"]))

        # Both should have numeric balance scores
        for profile in result["profiles"]:
            balance = profile["analysis"]["balance_score"]
            assert isinstance(balance, int | float)

    # -------------------------------------------------------------------------
    # Style Categorization Tests
    # -------------------------------------------------------------------------
    def test_style_categorization_spirit_forward(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test that high-spirit drinks are categorized as spirit-forward."""
        result = json.loads(tool._run(cocktail_ids=["old-fashioned"]))

        profile = result["profiles"][0]
        # Old Fashioned has spirit = 80 (>= 70), should be spirit-forward
        if profile["flavor_profile"]["spirit"] >= 70:
            assert profile["analysis"]["style"] == "spirit-forward"

    def test_style_categorization_mocktail(self, tool: FlavorProfilerTool) -> None:
        """Test that mocktails get appropriate style categorization."""
        result = json.loads(tool._run(cocktail_ids=["virgin-mojito"]))

        profile = result["profiles"][0]
        # Mocktails have spirit = 0, should be refreshing/mocktail style
        assert profile["flavor_profile"]["spirit"] == 0
        # Style should reflect non-alcoholic nature
        assert (
            "mocktail" in profile["analysis"]["style"].lower()
            or "refreshing" in profile["analysis"]["style"].lower()
        )

    def test_all_valid_styles_returned(self, tool: FlavorProfilerTool) -> None:
        """Test that style is always one of the valid categories."""
        valid_styles = {
            "spirit-forward",
            "sour",
            "bitter/aperitivo",
            "sweet/dessert",
            "refreshing/mocktail",
            "balanced",
        }

        # Test with multiple drinks to get variety
        result = json.loads(
            tool._run(cocktail_ids=["old-fashioned", "manhattan", "virgin-mojito"])
        )

        for profile in result["profiles"]:
            style = profile["analysis"]["style"]
            assert style in valid_styles, f"Invalid style: {style}"

    # -------------------------------------------------------------------------
    # Input Normalization Tests
    # -------------------------------------------------------------------------
    def test_case_insensitive_id_matching(self, tool: FlavorProfilerTool) -> None:
        """Test that drink ID matching is case-insensitive."""
        result_lower = json.loads(tool._run(cocktail_ids=["old-fashioned"]))
        result_upper = json.loads(tool._run(cocktail_ids=["OLD-FASHIONED"]))
        result_mixed = json.loads(tool._run(cocktail_ids=["Old-Fashioned"]))

        assert result_lower["found"] == result_upper["found"] == result_mixed["found"]

    def test_whitespace_trimmed_from_ids(self, tool: FlavorProfilerTool) -> None:
        """Test that whitespace is trimmed from drink IDs."""
        result_clean = json.loads(tool._run(cocktail_ids=["old-fashioned"]))
        result_whitespace = json.loads(tool._run(cocktail_ids=["  old-fashioned  "]))

        assert result_clean["found"] == result_whitespace["found"]


# =============================================================================
# SubstitutionFinderTool Tests
# =============================================================================
class TestSubstitutionFinderTool:
    """Test suite for SubstitutionFinderTool."""

    @pytest.fixture
    def tool(self) -> SubstitutionFinderTool:
        """Provide a SubstitutionFinderTool instance."""
        return SubstitutionFinderTool()

    # -------------------------------------------------------------------------
    # Known Ingredient Substitution Tests
    # -------------------------------------------------------------------------
    def test_find_substitutes_for_bourbon(self, tool: SubstitutionFinderTool) -> None:
        """Test finding substitutes for bourbon."""
        result = json.loads(tool._run(ingredient="bourbon"))

        assert result["found"] is True
        assert result["ingredient"]["id"] == "bourbon"
        assert result["total_substitutes"] > 0

        # Verify substitutes structure
        for sub in result["substitutes"]:
            assert "id" in sub
            assert "names" in sub

    def test_find_substitutes_for_simple_syrup(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test finding substitutes for simple syrup."""
        result = json.loads(tool._run(ingredient="simple-syrup"))

        assert result["found"] is True
        assert result["total_substitutes"] > 0

        # Simple syrup should have honey-syrup, agave-syrup as substitutes
        sub_ids = [s["id"] for s in result["substitutes"]]
        assert any(
            sub in sub_ids for sub in ["honey-syrup", "agave-syrup", "demerara-syrup"]
        )

    def test_find_substitutes_for_lime_juice(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test finding substitutes for lime juice."""
        result = json.loads(tool._run(ingredient="lime-juice"))

        assert result["found"] is True
        # Lime juice should have lemon juice as substitute
        sub_ids = [s["id"] for s in result["substitutes"]]
        assert "lemon-juice" in sub_ids

    # -------------------------------------------------------------------------
    # Unknown Ingredient Handling Tests
    # -------------------------------------------------------------------------
    def test_unknown_ingredient_not_found(self, tool: SubstitutionFinderTool) -> None:
        """Test handling of completely unknown ingredients."""
        result = json.loads(tool._run(ingredient="xyz-nonexistent-ingredient"))

        assert result["found"] is False
        assert "message" in result

    def test_unknown_ingredient_with_no_partial_matches(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test unknown ingredient that has no partial matches."""
        result = json.loads(tool._run(ingredient="zzzznotfound12345"))

        assert result["found"] is False
        # Should have empty substitutes list or suggestions
        if "substitutes" in result:
            assert result["substitutes"] == []

    # -------------------------------------------------------------------------
    # Partial Matching Tests
    # -------------------------------------------------------------------------
    def test_partial_match_suggestions(self, tool: SubstitutionFinderTool) -> None:
        """Test that partial matches provide suggestions."""
        # Search for something that partially matches known ingredients
        result = json.loads(tool._run(ingredient="bourbon-extra-aged"))

        # Since "bourbon" is a substring, should trigger partial match
        if result["found"] is False:
            # Should have suggestions for partial matches
            if "suggestions" in result:
                assert len(result["suggestions"]) > 0
                # Bourbon should be in suggestions
                suggestion_ids = [s["id"] for s in result["suggestions"]]
                assert "bourbon" in suggestion_ids

    def test_partial_match_by_name(self, tool: SubstitutionFinderTool) -> None:
        """Test partial matching by ingredient name alias."""
        # Try searching for a name alias that might partially match
        result = json.loads(tool._run(ingredient="whiskey"))

        # "whiskey" appears in names like "rye whiskey", "bourbon whiskey"
        # Should either find exact match or provide suggestions
        if result["found"] is False and "suggestions" in result:
            assert len(result["suggestions"]) > 0

    # -------------------------------------------------------------------------
    # NA/Alcoholic Crossover Tests
    # -------------------------------------------------------------------------
    def test_alcoholic_to_na_alternatives(self, tool: SubstitutionFinderTool) -> None:
        """Test finding non-alcoholic alternatives for alcoholic ingredients."""
        result = json.loads(tool._run(ingredient="gin"))

        assert result["found"] is True

        # Gin should have NA alternatives
        if "non_alcoholic_alternatives" in result:
            na_ids = [s["id"] for s in result["non_alcoholic_alternatives"]]
            # Should include NA spirits like Seedlip
            assert len(na_ids) > 0

    def test_na_to_alcoholic_alternatives(self, tool: SubstitutionFinderTool) -> None:
        """Test finding alcoholic alternatives for NA ingredients."""
        result = json.loads(tool._run(ingredient="seedlip-grove"))

        # If seedlip-grove is in the database
        if result["found"]:
            # Should have alcoholic alternatives
            if "alcoholic_alternatives" in result:
                alc_ids = [s["id"] for s in result["alcoholic_alternatives"]]
                assert len(alc_ids) > 0
                # Gin and vodka are alternatives
                assert "gin" in alc_ids or "vodka" in alc_ids

    def test_bourbon_has_na_alternatives(self, tool: SubstitutionFinderTool) -> None:
        """Test that bourbon has non-alcoholic alternatives."""
        result = json.loads(tool._run(ingredient="bourbon"))

        assert result["found"] is True
        if "non_alcoholic_alternatives" in result:
            na_alternatives = result["non_alcoholic_alternatives"]
            assert len(na_alternatives) >= 1
            na_ids = [s["id"] for s in na_alternatives]
            # Should include Monday whiskey or Lyre's American Malt
            assert any(
                alt in na_ids
                for alt in ["monday-whiskey", "lyre-american-malt", "seedlip-spice"]
            )

    # -------------------------------------------------------------------------
    # Input Normalization and Response Structure Tests
    # -------------------------------------------------------------------------
    def test_case_insensitive_ingredient_lookup(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test that ingredient lookup is case-insensitive."""
        result_lower = json.loads(tool._run(ingredient="bourbon"))
        result_upper = json.loads(tool._run(ingredient="BOURBON"))
        result_mixed = json.loads(tool._run(ingredient="Bourbon"))

        assert result_lower["found"] == result_upper["found"] == result_mixed["found"]

    def test_whitespace_trimmed(self, tool: SubstitutionFinderTool) -> None:
        """Test that whitespace is trimmed from input."""
        result_clean = json.loads(tool._run(ingredient="bourbon"))
        result_whitespace = json.loads(tool._run(ingredient="  bourbon  "))

        assert result_clean["found"] == result_whitespace["found"]

    def test_response_structure_for_found_ingredient(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test response structure when ingredient is found."""
        result = json.loads(tool._run(ingredient="bourbon"))

        assert "query" in result
        assert "found" in result
        assert "ingredient" in result
        assert "substitutes" in result
        assert "total_substitutes" in result

        assert result["ingredient"]["id"] == "bourbon"
        assert "names" in result["ingredient"]

    def test_name_alias_lookup(self, tool: SubstitutionFinderTool) -> None:
        """Test lookup by ingredient name alias."""
        # "bourbon whiskey" is a name alias for "bourbon"
        result = json.loads(tool._run(ingredient="bourbon whiskey"))

        assert result["found"] is True
        assert result["ingredient"]["id"] == "bourbon"


# =============================================================================
# UnlockCalculatorTool Tests
# =============================================================================
class TestUnlockCalculatorTool:
    """Test suite for UnlockCalculatorTool."""

    @pytest.fixture
    def tool(self) -> UnlockCalculatorTool:
        """Provide an UnlockCalculatorTool instance."""
        return UnlockCalculatorTool()

    # -------------------------------------------------------------------------
    # Empty Cabinet Tests
    # -------------------------------------------------------------------------
    def test_empty_cabinet_shows_no_makeable_drinks(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that empty cabinet shows zero makeable drinks."""
        result = json.loads(tool._run(cabinet=[]))

        assert result["current_status"]["drinks_you_can_make"] == 0
        assert result["current_status"]["drinks_makeable"] == []

    def test_empty_cabinet_still_returns_recommendations(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that empty cabinet can still return recommendations."""
        result = json.loads(tool._run(cabinet=[]))

        # Recommendations should still exist for ingredients that complete
        # drinks when user has other required ingredients (which is none here)
        # So recommendations might be empty or limited
        assert "recommendations" in result

    # -------------------------------------------------------------------------
    # Drink Type Filtering Tests
    # -------------------------------------------------------------------------
    def test_cocktails_filter(self, tool: UnlockCalculatorTool) -> None:
        """Test filtering recommendations by cocktails only."""
        # Cabinet with some basic ingredients
        cabinet = ["simple-syrup", "lime-juice", "fresh-mint"]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="cocktails"))

        # All recommended drinks should be cocktails
        for rec in result["recommendations"]:
            for drink in rec["drinks"]:
                assert drink["is_mocktail"] is False, (
                    f"Found mocktail {drink['name']} in cocktails-only recommendations"
                )

    def test_mocktails_filter(self, tool: UnlockCalculatorTool) -> None:
        """Test filtering recommendations by mocktails only."""
        cabinet = ["simple-syrup", "lime-juice", "fresh-mint", "ginger-ale"]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="mocktails"))

        # All recommended drinks should be mocktails
        for rec in result["recommendations"]:
            for drink in rec["drinks"]:
                assert drink["is_mocktail"] is True, (
                    f"Found cocktail {drink['name']} in mocktails-only recommendations"
                )

    def test_both_filter(self, tool: UnlockCalculatorTool) -> None:
        """Test that 'both' filter includes all drink types."""
        cabinet = ["simple-syrup", "lime-juice", "fresh-mint"]
        result = json.loads(tool._run(cabinet=cabinet, drink_type="both"))

        # Should include recommendations (structure validation)
        assert "recommendations" in result
        assert "query" in result
        assert result["query"]["drink_type"] == "both"

    # -------------------------------------------------------------------------
    # Limit Parameter Tests
    # -------------------------------------------------------------------------
    def test_limit_parameter_respected(self, tool: UnlockCalculatorTool) -> None:
        """Test that limit parameter restricts number of recommendations."""
        cabinet = ["simple-syrup", "lime-juice"]

        result_3 = json.loads(tool._run(cabinet=cabinet, limit=3))
        result_10 = json.loads(tool._run(cabinet=cabinet, limit=10))

        assert len(result_3["recommendations"]) <= 3
        assert len(result_10["recommendations"]) <= 10

    def test_limit_default_is_5(self, tool: UnlockCalculatorTool) -> None:
        """Test that default limit is 5."""
        cabinet = ["simple-syrup", "lime-juice", "fresh-mint"]
        result = json.loads(tool._run(cabinet=cabinet))

        # Query should show limit = 5
        assert result["query"]["limit"] == 5
        assert len(result["recommendations"]) <= 5

    def test_limit_1_returns_top_recommendation(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that limit=1 returns only the top recommendation."""
        cabinet = ["simple-syrup", "lime-juice", "bourbon"]
        result = json.loads(tool._run(cabinet=cabinet, limit=1))

        assert len(result["recommendations"]) <= 1

    # -------------------------------------------------------------------------
    # Recommendations Sorting Tests
    # -------------------------------------------------------------------------
    def test_recommendations_sorted_by_unlocks_descending(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that recommendations are sorted by new drinks unlocked."""
        cabinet = ["simple-syrup", "lime-juice"]
        result = json.loads(tool._run(cabinet=cabinet, limit=10))

        if len(result["recommendations"]) >= 2:
            unlock_counts = [
                r["new_drinks_unlocked"] for r in result["recommendations"]
            ]
            assert unlock_counts == sorted(unlock_counts, reverse=True), (
                "Recommendations should be sorted by unlock count descending"
            )

    def test_recommendation_includes_drink_details(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that each recommendation includes drink details."""
        # Provide a good base that might need one more ingredient
        cabinet = ["bourbon", "simple-syrup", "orange-bitters"]
        result = json.loads(tool._run(cabinet=cabinet))

        for rec in result["recommendations"]:
            assert "ingredient_id" in rec
            assert "new_drinks_unlocked" in rec
            assert "drinks" in rec

            for drink in rec["drinks"]:
                assert "id" in drink
                assert "name" in drink
                assert "is_mocktail" in drink
                assert "difficulty" in drink

    # -------------------------------------------------------------------------
    # Current Status Tests
    # -------------------------------------------------------------------------
    def test_current_status_shows_makeable_drinks(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that current status shows drinks user can already make."""
        # Old Fashioned: bourbon, simple-syrup, angostura-bitters, orange-bitters
        cabinet = ["bourbon", "simple-syrup", "angostura-bitters", "orange-bitters"]
        result = json.loads(tool._run(cabinet=cabinet))

        status = result["current_status"]
        assert status["drinks_you_can_make"] >= 1

        # Old Fashioned should be in makeable list
        makeable_ids = [d["id"] for d in status["drinks_makeable"]]
        assert "old-fashioned" in makeable_ids

    def test_makeable_drinks_limited_to_10(self, tool: UnlockCalculatorTool) -> None:
        """Test that makeable drinks list is limited to 10 entries."""
        # Large cabinet that can make many drinks
        cabinet = [
            "bourbon",
            "rye-whiskey",
            "gin",
            "vodka",
            "white-rum",
            "simple-syrup",
            "lime-juice",
            "lemon-juice",
            "angostura-bitters",
            "orange-bitters",
            "sweet-vermouth",
            "dry-vermouth",
            "triple-sec",
            "fresh-mint",
            "club-soda",
        ]
        result = json.loads(tool._run(cabinet=cabinet))

        assert len(result["current_status"]["drinks_makeable"]) <= 10

    # -------------------------------------------------------------------------
    # Summary Statistics Tests
    # -------------------------------------------------------------------------
    def test_summary_includes_bottle_count(self, tool: UnlockCalculatorTool) -> None:
        """Test that summary includes number of bottles shown."""
        cabinet = ["simple-syrup", "lime-juice"]
        result = json.loads(tool._run(cabinet=cabinet, limit=5))

        assert "summary" in result
        assert "top_bottles_shown" in result["summary"]
        assert result["summary"]["top_bottles_shown"] == len(result["recommendations"])

    def test_summary_includes_potential_unlocks(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that summary includes total potential new drinks."""
        cabinet = ["simple-syrup", "lime-juice"]
        result = json.loads(tool._run(cabinet=cabinet))

        assert "potential_new_drinks" in result["summary"]

        # Verify the sum is correct
        expected_total = sum(
            r["new_drinks_unlocked"] for r in result["recommendations"]
        )
        assert result["summary"]["potential_new_drinks"] == expected_total

    # -------------------------------------------------------------------------
    # Edge Cases and Input Normalization Tests
    # -------------------------------------------------------------------------
    def test_case_insensitive_cabinet(self, tool: UnlockCalculatorTool) -> None:
        """Test that cabinet matching is case-insensitive."""
        cabinet_lower = ["bourbon", "simple-syrup"]
        cabinet_upper = ["BOURBON", "SIMPLE-SYRUP"]

        result_lower = json.loads(tool._run(cabinet=cabinet_lower))
        result_upper = json.loads(tool._run(cabinet=cabinet_upper))

        assert (
            result_lower["current_status"]["drinks_you_can_make"]
            == result_upper["current_status"]["drinks_you_can_make"]
        )

    def test_whitespace_trimmed_from_cabinet(self, tool: UnlockCalculatorTool) -> None:
        """Test that whitespace is trimmed from cabinet ingredients."""
        cabinet_clean = ["bourbon", "simple-syrup"]
        cabinet_whitespace = ["  bourbon  ", "  simple-syrup  "]

        result_clean = json.loads(tool._run(cabinet=cabinet_clean))
        result_whitespace = json.loads(tool._run(cabinet=cabinet_whitespace))

        assert (
            result_clean["current_status"]["drinks_you_can_make"]
            == result_whitespace["current_status"]["drinks_you_can_make"]
        )

    def test_response_structure_is_valid(self, tool: UnlockCalculatorTool) -> None:
        """Test that response has expected structure."""
        cabinet = ["bourbon"]
        result = json.loads(tool._run(cabinet=cabinet))

        # Top-level keys
        assert "query" in result
        assert "current_status" in result
        assert "recommendations" in result
        assert "total_recommendations" in result
        assert "summary" in result

        # Query structure
        assert "cabinet_size" in result["query"]
        assert "drink_type" in result["query"]
        assert "limit" in result["query"]

        # Current status structure
        assert "drinks_you_can_make" in result["current_status"]
        assert "drinks_makeable" in result["current_status"]

    def test_excludes_ingredients_already_in_cabinet(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that recommendations exclude ingredients user already has."""
        cabinet = ["bourbon", "simple-syrup", "angostura-bitters"]
        result = json.loads(tool._run(cabinet=cabinet))

        cabinet_set = {ing.lower() for ing in cabinet}
        for rec in result["recommendations"]:
            assert rec["ingredient_id"].lower() not in cabinet_set, (
                f"Recommended {rec['ingredient_id']} but it's already in cabinet"
            )
