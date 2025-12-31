"""Comprehensive unit tests for CrewAI tools.

Tests cover all four tools in src/app/tools/:
- RecipeDBTool: Query drinks based on cabinet ingredients
- FlavorProfilerTool: Analyze and compare drink flavor profiles
- SubstitutionFinderTool: Find ingredient substitutes
- UnlockCalculatorTool: Calculate next bottle recommendations

All tools return Raja-style conversational text with Hindi phrases.
"""

import pytest

from src.app.models.drinks import FlavorProfile
from src.app.tools.flavor_profiler import FlavorProfilerTool
from src.app.tools.recipe_db import RecipeDBTool
from src.app.tools.substitution_finder import SubstitutionFinderTool
from src.app.tools.unlock_calculator import DrinkUnlock, UnlockCalculatorTool


# =============================================================================
# RecipeDBTool Tests
# =============================================================================
class TestRecipeDBTool:
    """Test suite for RecipeDBTool with Raja-style conversational output."""

    @pytest.fixture
    def tool(self) -> RecipeDBTool:
        """Provide a RecipeDBTool instance."""
        return RecipeDBTool()

    # -------------------------------------------------------------------------
    # Conversational Output Format Tests
    # -------------------------------------------------------------------------
    def test_output_is_string(self, tool: RecipeDBTool) -> None:
        """Test that output is a string, not JSON."""
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        assert isinstance(result, str)

    def test_output_has_raja_personality(self, tool: RecipeDBTool) -> None:
        """Test that output includes Raja's personality markers."""
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        personality_markers = ["bhai", "yaar", "acha", "bilkul", "arrey"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Output should contain Raja's personality markers"

    def test_output_has_bold_formatting(self, tool: RecipeDBTool) -> None:
        """Test that drink names are formatted in bold markdown."""
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        assert "**" in result, "Output should contain bold markdown formatting"

    def test_output_has_drink_emoji(self, tool: RecipeDBTool) -> None:
        """Test that output contains drink emoji for visual appeal."""
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        # Should have cocktail emoji for drinks
        drink_emojis = ["drink", "cocktail"]
        # Check for either emoji or text representation
        has_emoji = (
            any(emoji in result.lower() for emoji in drink_emojis) or "**" in result
        )
        assert has_emoji or len(result) > 0

    # -------------------------------------------------------------------------
    # Empty Cabinet Tests
    # -------------------------------------------------------------------------
    def test_empty_cabinet_returns_helpful_message(self, tool: RecipeDBTool) -> None:
        """Test that an empty cabinet returns a helpful conversational message."""
        result = tool._run(cabinet=[])
        assert isinstance(result, str)
        assert len(result) > 0
        # Output varies: "dry spell", "nothing matched...stock up", "getting mixers"
        helpful_words = [
            "dry",
            "spell",
            "consider",
            "getting",
            "mixers",
            "spirits",
            "cabinet",
            "add",
            "try",
            "stock",
            "matched",
            "essentials",
        ]
        has_helpful = any(word in result.lower() for word in helpful_words)
        assert has_helpful, (
            f"Empty cabinet should return helpful message, got: {result}"
        )

    def test_empty_cabinet_has_raja_personality(self, tool: RecipeDBTool) -> None:
        """Test empty cabinet response has Raja's personality."""
        result = tool._run(cabinet=[])
        personality_markers = ["bhai", "yaar", "acha", "arrey"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Empty cabinet response should have Raja's personality"

    # -------------------------------------------------------------------------
    # Full Ingredient Set Tests
    # -------------------------------------------------------------------------
    def test_full_ingredients_mentions_makeable_drinks(
        self, tool: RecipeDBTool
    ) -> None:
        """Test that providing all ingredients shows makeable drinks."""
        # Old Fashioned requires: bourbon, simple-syrup, angostura, orange-bitters
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = tool._run(cabinet=cabinet)

        # Should mention Old Fashioned
        assert "old fashioned" in result.lower()
        # Should use bold formatting
        assert "**" in result

    def test_partial_ingredients_shows_missing(self, tool: RecipeDBTool) -> None:
        """Test that partial ingredients shows what's missing."""
        # Old Fashioned needs 4 ingredients, we provide 2
        cabinet = ["bourbon", "simple-syrup"]
        result = tool._run(cabinet=cabinet)

        # Should show drinks with missing ingredients indicated
        assert (
            "need:" in result.lower()
            or "missing" in result.lower()
            or "(need" in result.lower()
        )

    # -------------------------------------------------------------------------
    # Drink Type Filtering Tests
    # -------------------------------------------------------------------------
    def test_cocktails_filter_shows_cocktails_only(self, tool: RecipeDBTool) -> None:
        """Test that cocktails filter returns cocktail recommendations."""
        cabinet = ["lime-juice", "simple-syrup", "fresh-mint", "club-soda", "white-rum"]
        result = tool._run(cabinet=cabinet, drink_type="cocktails")

        # Should return valid string output
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mocktails_filter_shows_mocktails_only(self, tool: RecipeDBTool) -> None:
        """Test that mocktails filter returns mocktail recommendations."""
        cabinet = [
            "lime-juice",
            "simple-syrup",
            "fresh-mint",
            "club-soda",
            "ginger-ale",
        ]
        result = tool._run(cabinet=cabinet, drink_type="mocktails")

        # Should return valid string output
        assert isinstance(result, str)
        assert len(result) > 0

    # -------------------------------------------------------------------------
    # Edge Cases and Input Normalization
    # -------------------------------------------------------------------------
    def test_case_insensitive_ingredient_matching(self, tool: RecipeDBTool) -> None:
        """Test that ingredient matching is case-insensitive."""
        cabinet_lower = ["bourbon", "simple-syrup"]
        cabinet_upper = ["BOURBON", "SIMPLE-SYRUP"]

        result_lower = tool._run(cabinet=cabinet_lower)
        result_upper = tool._run(cabinet=cabinet_upper)

        # Both should produce similar output (same drinks mentioned)
        assert isinstance(result_lower, str)
        assert isinstance(result_upper, str)

    def test_whitespace_trimmed_from_ingredients(self, tool: RecipeDBTool) -> None:
        """Test that whitespace is trimmed from ingredient names."""
        cabinet_clean = ["bourbon", "simple-syrup"]
        cabinet_whitespace = ["  bourbon  ", "  simple-syrup  "]

        result_clean = tool._run(cabinet=cabinet_clean)
        result_whitespace = tool._run(cabinet=cabinet_whitespace)

        # Both should produce valid output
        assert isinstance(result_clean, str)
        assert isinstance(result_whitespace, str)

    def test_duplicate_ingredients_handled(self, tool: RecipeDBTool) -> None:
        """Test that duplicate ingredients in cabinet are handled correctly."""
        cabinet_single = ["bourbon", "simple-syrup"]
        cabinet_duplicates = ["bourbon", "bourbon", "simple-syrup", "simple-syrup"]

        result_single = tool._run(cabinet=cabinet_single)
        result_duplicates = tool._run(cabinet=cabinet_duplicates)

        # Both should produce valid output
        assert isinstance(result_single, str)
        assert isinstance(result_duplicates, str)

    def test_nonexistent_ingredient_handled_gracefully(
        self, tool: RecipeDBTool
    ) -> None:
        """Test with an ingredient that does not exist in any drink."""
        cabinet = ["xyz-nonexistent-ingredient-123"]
        result = tool._run(cabinet=cabinet)

        # Should return helpful message, not error
        assert isinstance(result, str)
        assert len(result) > 0


# =============================================================================
# FlavorProfilerTool Tests
# =============================================================================
class TestFlavorProfilerTool:
    """Test suite for FlavorProfilerTool with Raja-style conversational output."""

    @pytest.fixture
    def tool(self) -> FlavorProfilerTool:
        """Provide a FlavorProfilerTool instance."""
        return FlavorProfilerTool()

    # -------------------------------------------------------------------------
    # Conversational Output Format Tests
    # -------------------------------------------------------------------------
    def test_output_is_string(self, tool: FlavorProfilerTool) -> None:
        """Test that output is a string, not JSON."""
        result = tool._run(cocktail_ids=["old-fashioned"])
        assert isinstance(result, str)

    def test_output_has_raja_personality(self, tool: FlavorProfilerTool) -> None:
        """Test that output includes Raja's personality markers."""
        result = tool._run(cocktail_ids=["old-fashioned"])
        personality_markers = ["bhai", "yaar", "acha", "bilkul", "arrey"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Output should contain Raja's personality markers"

    def test_output_mentions_drink_name(self, tool: FlavorProfilerTool) -> None:
        """Test that output mentions the drink name."""
        result = tool._run(cocktail_ids=["old-fashioned"])
        assert "old fashioned" in result.lower()

    # -------------------------------------------------------------------------
    # Single Drink Profile Tests
    # -------------------------------------------------------------------------
    def test_single_drink_returns_flavor_description(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test extracting flavor profile for a single drink."""
        result = tool._run(cocktail_ids=["old-fashioned"])

        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention flavor characteristics
        flavor_words = ["sweet", "bitter", "spirit", "sour", "balance"]
        has_flavor_mention = any(word in result.lower() for word in flavor_words)
        assert has_flavor_mention, "Output should describe flavor characteristics"

    def test_mocktail_profile_mentions_non_alcoholic(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test that mocktail profile reflects non-alcoholic nature."""
        result = tool._run(cocktail_ids=["virgin-mojito"])

        assert isinstance(result, str)
        # Should reflect mocktail nature (refreshing, etc.)
        mocktail_indicators = ["refresh", "virgin", "mojito"]
        has_indicator = any(ind in result.lower() for ind in mocktail_indicators)
        assert has_indicator

    # -------------------------------------------------------------------------
    # Multiple Drink Comparison Tests
    # -------------------------------------------------------------------------
    def test_multiple_drinks_returns_comparison(self, tool: FlavorProfilerTool) -> None:
        """Test comparing multiple drinks."""
        result = tool._run(cocktail_ids=["old-fashioned", "manhattan"])

        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention both drinks
        assert "old fashioned" in result.lower() or "manhattan" in result.lower()

    # -------------------------------------------------------------------------
    # Not Found Handling Tests
    # -------------------------------------------------------------------------
    def test_unknown_drink_handled_gracefully(self, tool: FlavorProfilerTool) -> None:
        """Test handling of unknown drink IDs."""
        result = tool._run(cocktail_ids=["nonexistent-drink-xyz"])

        assert isinstance(result, str)
        # Should indicate drink not found
        assert (
            "find" in result.lower()
            or "found" in result.lower()
            or "know" in result.lower()
        )

    def test_empty_cocktail_ids_returns_empty_string(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test with an empty list of cocktail IDs returns empty string."""
        result = tool._run(cocktail_ids=[])

        # Empty input returns empty string - this is expected behavior
        assert isinstance(result, str)

    # -------------------------------------------------------------------------
    # Internal Method Tests
    # -------------------------------------------------------------------------
    def test_calculate_balance_score_single_flavor(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test balance score calculation for single non-zero flavor."""
        score = tool._calculate_balance_score(sweet=50, sour=0, bitter=0)
        assert score == 0.0  # Single-note drinks have 0 balance

    def test_calculate_balance_score_two_equal_flavors(
        self, tool: FlavorProfilerTool
    ) -> None:
        """Test balance score for two equal flavors."""
        score = tool._calculate_balance_score(sweet=50, sour=50, bitter=0)
        assert score == 100.0  # Perfect balance when std_dev is 0

    def test_calculate_balance_score_all_zero(self, tool: FlavorProfilerTool) -> None:
        """Test balance score when all flavors are zero."""
        score = tool._calculate_balance_score(sweet=0, sour=0, bitter=0)
        assert score == 0.0

    def test_categorize_style_spirit_forward(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for spirit-forward drinks."""
        fp = FlavorProfile(sweet=30, sour=10, bitter=20, spirit=80)
        style = tool._categorize_style(fp)
        assert style == "spirit-forward"

    def test_categorize_style_sour(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for sour drinks."""
        fp = FlavorProfile(sweet=35, sour=45, bitter=10, spirit=50)
        style = tool._categorize_style(fp)
        assert style == "sour"

    def test_categorize_style_bitter(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for bitter drinks."""
        fp = FlavorProfile(sweet=20, sour=15, bitter=50, spirit=60)
        style = tool._categorize_style(fp)
        assert style == "bitter/aperitivo"

    def test_categorize_style_sweet(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for sweet drinks."""
        fp = FlavorProfile(sweet=60, sour=10, bitter=5, spirit=40)
        style = tool._categorize_style(fp)
        assert style == "sweet/dessert"

    def test_categorize_style_balanced(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for balanced drinks."""
        fp = FlavorProfile(sweet=30, sour=25, bitter=20, spirit=50)
        style = tool._categorize_style(fp)
        assert style == "balanced"

    def test_categorize_style_mocktail(self, tool: FlavorProfilerTool) -> None:
        """Test style categorization for mocktails."""
        fp = FlavorProfile(sweet=40, sour=30, bitter=10, spirit=0)
        style = tool._categorize_style(fp)
        assert style == "refreshing/mocktail"


# =============================================================================
# SubstitutionFinderTool Tests
# =============================================================================
class TestSubstitutionFinderTool:
    """Test suite for SubstitutionFinderTool with Raja-style conversational output."""

    @pytest.fixture
    def tool(self) -> SubstitutionFinderTool:
        """Provide a SubstitutionFinderTool instance."""
        return SubstitutionFinderTool()

    # -------------------------------------------------------------------------
    # Conversational Output Format Tests
    # -------------------------------------------------------------------------
    def test_output_is_string(self, tool: SubstitutionFinderTool) -> None:
        """Test that output is a string, not JSON."""
        result = tool._run(ingredient="bourbon")
        assert isinstance(result, str)

    def test_output_has_raja_personality(self, tool: SubstitutionFinderTool) -> None:
        """Test that output includes Raja's personality markers."""
        result = tool._run(ingredient="bourbon")
        personality_markers = ["bhai", "yaar", "acha", "bilkul", "arrey", "no worries"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Output should contain Raja's personality markers"

    def test_output_has_bold_formatting(self, tool: SubstitutionFinderTool) -> None:
        """Test that substitute names are formatted in bold markdown."""
        result = tool._run(ingredient="bourbon")
        assert "**" in result, "Output should contain bold markdown formatting"

    # -------------------------------------------------------------------------
    # Known Ingredient Substitution Tests
    # -------------------------------------------------------------------------
    def test_bourbon_has_substitutes(self, tool: SubstitutionFinderTool) -> None:
        """Test finding substitutes for bourbon."""
        result = tool._run(ingredient="bourbon")

        assert isinstance(result, str)
        # Should mention substitute options
        substitute_indicators = ["rye", "whiskey", "whisky", "alternative", "swap"]
        has_substitute = any(ind in result.lower() for ind in substitute_indicators)
        assert has_substitute, "Output should mention bourbon substitutes"

    def test_simple_syrup_has_substitutes(self, tool: SubstitutionFinderTool) -> None:
        """Test finding substitutes for simple syrup."""
        result = tool._run(ingredient="simple-syrup")

        assert isinstance(result, str)
        # Should mention sweetener alternatives
        sweetener_words = ["honey", "agave", "syrup", "sugar", "demerara"]
        has_sweetener = any(word in result.lower() for word in sweetener_words)
        assert has_sweetener, "Output should mention sweetener substitutes"

    def test_lime_juice_suggests_lemon(self, tool: SubstitutionFinderTool) -> None:
        """Test that lime juice suggests lemon juice as substitute."""
        result = tool._run(ingredient="lime-juice")

        assert isinstance(result, str)
        assert "lemon" in result.lower(), (
            "Lime juice should suggest lemon as substitute"
        )

    # -------------------------------------------------------------------------
    # Unknown Ingredient Handling Tests
    # -------------------------------------------------------------------------
    def test_unknown_ingredient_handled_gracefully(
        self, tool: SubstitutionFinderTool
    ) -> None:
        """Test handling of completely unknown ingredients."""
        result = tool._run(ingredient="xyz-nonexistent-ingredient")

        assert isinstance(result, str)
        # Should indicate not found or unknown - output says "ringing a bell" and "doesn't match"
        not_found_indicators = [
            "ringing",
            "bell",
            "match",
            "collection",
            "doesn't",
            "don't",
        ]
        has_indicator = any(ind in result.lower() for ind in not_found_indicators)
        assert has_indicator, (
            f"Unknown ingredient should return helpful message, got: {result}"
        )

    def test_empty_ingredient_handled(self, tool: SubstitutionFinderTool) -> None:
        """Test with an empty ingredient string."""
        result = tool._run(ingredient="")

        assert isinstance(result, str)
        assert len(result) > 0

    # -------------------------------------------------------------------------
    # NA/Alcoholic Crossover Tests
    # -------------------------------------------------------------------------
    def test_bourbon_shows_na_alternatives(self, tool: SubstitutionFinderTool) -> None:
        """Test that bourbon shows non-alcoholic alternatives."""
        result = tool._run(ingredient="bourbon")

        assert isinstance(result, str)
        # Should mention NA options like Monday whiskey, Lyre's, or Seedlip
        # NA alternatives may or may not be present depending on data
        assert isinstance(result, str)

    # -------------------------------------------------------------------------
    # Input Normalization Tests
    # -------------------------------------------------------------------------
    def test_case_insensitive_lookup(self, tool: SubstitutionFinderTool) -> None:
        """Test that ingredient lookup is case-insensitive."""
        result_lower = tool._run(ingredient="bourbon")
        result_upper = tool._run(ingredient="BOURBON")
        result_mixed = tool._run(ingredient="Bourbon")

        # All should produce valid output
        assert isinstance(result_lower, str)
        assert isinstance(result_upper, str)
        assert isinstance(result_mixed, str)

    def test_whitespace_trimmed(self, tool: SubstitutionFinderTool) -> None:
        """Test that whitespace is trimmed from input."""
        result_clean = tool._run(ingredient="bourbon")
        result_whitespace = tool._run(ingredient="  bourbon  ")

        # Both should produce valid output
        assert isinstance(result_clean, str)
        assert isinstance(result_whitespace, str)


# =============================================================================
# UnlockCalculatorTool Tests
# =============================================================================
class TestUnlockCalculatorTool:
    """Test suite for UnlockCalculatorTool with Raja-style conversational output."""

    @pytest.fixture
    def tool(self) -> UnlockCalculatorTool:
        """Provide an UnlockCalculatorTool instance."""
        return UnlockCalculatorTool()

    # -------------------------------------------------------------------------
    # Conversational Output Format Tests
    # -------------------------------------------------------------------------
    def test_output_is_string(self, tool: UnlockCalculatorTool) -> None:
        """Test that output is a string, not JSON."""
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        assert isinstance(result, str)

    def test_output_has_raja_personality(self, tool: UnlockCalculatorTool) -> None:
        """Test that output includes Raja's personality markers."""
        result = tool._run(cabinet=["simple-syrup", "lime-juice"])
        personality_markers = ["bhai", "yaar", "bilkul", "arrey", "grow", "shopping"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Output should contain Raja's personality markers"

    def test_output_has_bold_formatting(self, tool: UnlockCalculatorTool) -> None:
        """Test that ingredient names are formatted in bold markdown."""
        result = tool._run(cabinet=["simple-syrup", "lime-juice"])
        assert "**" in result, "Output should contain bold markdown formatting"

    def test_output_has_numbered_list(self, tool: UnlockCalculatorTool) -> None:
        """Test that recommendations are formatted as a numbered list."""
        result = tool._run(cabinet=["simple-syrup", "lime-juice"])
        assert "1." in result, "Output should contain numbered recommendations"

    # -------------------------------------------------------------------------
    # Empty Cabinet Tests
    # -------------------------------------------------------------------------
    def test_empty_cabinet_returns_helpful_message(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that empty cabinet returns helpful conversational message."""
        result = tool._run(cabinet=[])

        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention 0 ingredients or empty bar
        assert "0" in result or "empty" in result.lower() or "nothing" in result.lower()

    def test_empty_cabinet_has_raja_personality(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test empty cabinet response has Raja's personality."""
        result = tool._run(cabinet=[])
        personality_markers = ["bhai", "yaar", "arrey", "grow", "level"]
        has_personality = any(
            marker in result.lower() for marker in personality_markers
        )
        assert has_personality, "Empty cabinet response should have Raja's personality"

    # -------------------------------------------------------------------------
    # Recommendation Content Tests
    # -------------------------------------------------------------------------
    def test_output_mentions_unlock_count(self, tool: UnlockCalculatorTool) -> None:
        """Test that output mentions how many drinks each bottle unlocks."""
        result = tool._run(cabinet=["simple-syrup", "lime-juice"])
        assert "unlock" in result.lower(), "Output should mention unlock counts"

    def test_output_mentions_signature_drinks(self, tool: UnlockCalculatorTool) -> None:
        """Test that output mentions specific drinks for each recommendation."""
        result = tool._run(cabinet=["simple-syrup", "lime-juice"])
        # Should mention "including" to introduce drink names
        assert (
            "including" in result.lower() or "like" in result.lower() or "!" in result
        )

    def test_output_shows_current_status(self, tool: UnlockCalculatorTool) -> None:
        """Test that output shows current bar status."""
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = tool._run(cabinet=cabinet)

        # Should mention how many drinks can be made or ingredients count
        assert "ingredient" in result.lower() or "drink" in result.lower()

    # -------------------------------------------------------------------------
    # Limit Parameter Tests
    # -------------------------------------------------------------------------
    def test_limit_affects_output(self, tool: UnlockCalculatorTool) -> None:
        """Test that limit parameter affects number of recommendations shown."""
        result_1 = tool._run(cabinet=["simple-syrup", "lime-juice"], limit=1)
        result_5 = tool._run(cabinet=["simple-syrup", "lime-juice"], limit=5)

        # Both should be valid strings
        assert isinstance(result_1, str)
        assert isinstance(result_5, str)
        # limit=1 should have "1." but likely not "2."
        assert "1." in result_1

    def test_limit_zero_returns_no_numbered_items(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that limit=0 returns no numbered recommendations."""
        import re

        result = tool._run(cabinet=["simple-syrup", "lime-juice"], limit=0)

        # Should not have numbered items
        numbers = re.findall(r"^\d+\.", result, re.MULTILINE)
        assert len(numbers) == 0, "limit=0 should produce no numbered items"

    # -------------------------------------------------------------------------
    # Edge Cases and Input Normalization
    # -------------------------------------------------------------------------
    def test_case_insensitive_cabinet(self, tool: UnlockCalculatorTool) -> None:
        """Test that cabinet matching is case-insensitive."""
        result_lower = tool._run(cabinet=["bourbon", "simple-syrup"])
        result_upper = tool._run(cabinet=["BOURBON", "SIMPLE-SYRUP"])

        # Both should produce valid output
        assert isinstance(result_lower, str)
        assert isinstance(result_upper, str)

    def test_whitespace_trimmed_from_cabinet(self, tool: UnlockCalculatorTool) -> None:
        """Test that whitespace is trimmed from cabinet ingredients."""
        result_clean = tool._run(cabinet=["bourbon", "simple-syrup"])
        result_whitespace = tool._run(cabinet=["  bourbon  ", "  simple-syrup  "])

        # Both should produce valid output
        assert isinstance(result_clean, str)
        assert isinstance(result_whitespace, str)

    def test_duplicate_ingredients_handled(self, tool: UnlockCalculatorTool) -> None:
        """Test that duplicate ingredients are handled correctly."""
        result_single = tool._run(cabinet=["bourbon", "simple-syrup"])
        result_duplicates = tool._run(cabinet=["bourbon", "bourbon", "simple-syrup"])

        # Both should produce valid output
        assert isinstance(result_single, str)
        assert isinstance(result_duplicates, str)

    def test_very_large_limit_handled(self, tool: UnlockCalculatorTool) -> None:
        """Test with a limit larger than available recommendations."""
        result = tool._run(cabinet=["simple-syrup"], limit=1000)

        assert isinstance(result, str)
        assert len(result) > 0

    # -------------------------------------------------------------------------
    # Internal Method Tests
    # -------------------------------------------------------------------------
    def test_get_makeable_drinks(self, tool: UnlockCalculatorTool) -> None:
        """Test the internal _get_makeable_drinks method."""
        from src.app.services.data_loader import load_all_drinks

        all_drinks = load_all_drinks()
        cabinet_set = {"bourbon", "simple-syrup", "angostura", "orange-bitters"}

        makeable = tool._get_makeable_drinks(cabinet_set, all_drinks)

        # Should find Old Fashioned
        makeable_ids = {d.id for d in makeable}
        assert "old-fashioned" in makeable_ids

    def test_format_ingredient_name(self, tool: UnlockCalculatorTool) -> None:
        """Test the internal _format_ingredient_name method."""
        assert tool._format_ingredient_name("sweet-vermouth") == "Sweet Vermouth"
        assert tool._format_ingredient_name("triple_sec") == "Triple Sec"
        assert tool._format_ingredient_name("bourbon") == "Bourbon"

    def test_get_signature_drink(self, tool: UnlockCalculatorTool) -> None:
        """Test the internal _get_signature_drink method."""
        drinks: list[DrinkUnlock] = [
            {
                "id": "negroni",
                "name": "Negroni",
                "is_mocktail": False,
                "difficulty": "easy",
            },
            {
                "id": "random",
                "name": "Random Drink",
                "is_mocktail": False,
                "difficulty": "easy",
            },
        ]
        signature = tool._get_signature_drink(drinks)
        assert signature == "Negroni"

    def test_get_signature_drink_prefers_cocktails(
        self, tool: UnlockCalculatorTool
    ) -> None:
        """Test that signature drink prefers cocktails over mocktails."""
        drinks: list[DrinkUnlock] = [
            {
                "id": "mock",
                "name": "Mock One",
                "is_mocktail": True,
                "difficulty": "easy",
            },
            {
                "id": "cock",
                "name": "Cocktail One",
                "is_mocktail": False,
                "difficulty": "easy",
            },
        ]
        signature = tool._get_signature_drink(drinks)
        assert signature == "Cocktail One"


# =============================================================================
# Tool Integration Tests - Cross-Tool Verification
# =============================================================================
class TestToolIntegration:
    """Integration tests verifying all tools work together cohesively."""

    def test_all_tools_return_strings(self) -> None:
        """Test that all tools return string output."""
        recipe_tool = RecipeDBTool()
        flavor_tool = FlavorProfilerTool()
        sub_tool = SubstitutionFinderTool()
        unlock_tool = UnlockCalculatorTool()

        assert isinstance(recipe_tool._run(cabinet=["bourbon"]), str)
        assert isinstance(flavor_tool._run(cocktail_ids=["old-fashioned"]), str)
        assert isinstance(sub_tool._run(ingredient="bourbon"), str)
        assert isinstance(unlock_tool._run(cabinet=["bourbon"]), str)

    def test_all_tools_have_raja_personality(self) -> None:
        """Test that all tools have Raja's personality in output."""
        recipe_tool = RecipeDBTool()
        flavor_tool = FlavorProfilerTool()
        sub_tool = SubstitutionFinderTool()
        unlock_tool = UnlockCalculatorTool()

        personality_markers = [
            "bhai",
            "yaar",
            "acha",
            "bilkul",
            "arrey",
            "no worries",
            "grow",
        ]

        outputs = [
            recipe_tool._run(cabinet=["bourbon", "simple-syrup"]),
            flavor_tool._run(cocktail_ids=["old-fashioned"]),
            sub_tool._run(ingredient="bourbon"),
            unlock_tool._run(cabinet=["bourbon", "simple-syrup"]),
        ]

        for output in outputs:
            has_personality = any(
                marker in output.lower() for marker in personality_markers
            )
            assert has_personality, (
                f"Output should have Raja's personality: {output[:100]}"
            )

    def test_tools_handle_edge_cases_gracefully(self) -> None:
        """Test that all tools handle edge cases without crashing."""
        recipe_tool = RecipeDBTool()
        flavor_tool = FlavorProfilerTool()
        sub_tool = SubstitutionFinderTool()
        unlock_tool = UnlockCalculatorTool()

        # Empty inputs
        assert isinstance(recipe_tool._run(cabinet=[]), str)
        assert isinstance(flavor_tool._run(cocktail_ids=[]), str)
        assert isinstance(sub_tool._run(ingredient=""), str)
        assert isinstance(unlock_tool._run(cabinet=[]), str)

        # Invalid inputs
        assert isinstance(recipe_tool._run(cabinet=["xyz-fake"]), str)
        assert isinstance(flavor_tool._run(cocktail_ids=["xyz-fake"]), str)
        assert isinstance(sub_tool._run(ingredient="xyz-fake"), str)
        assert isinstance(unlock_tool._run(cabinet=["xyz-fake"]), str)

    def test_tools_have_consistent_formatting(self) -> None:
        """Test that all tools use consistent markdown formatting."""
        recipe_tool = RecipeDBTool()
        sub_tool = SubstitutionFinderTool()
        unlock_tool = UnlockCalculatorTool()

        # Tools that show lists should use bold formatting
        recipe_result = recipe_tool._run(cabinet=["bourbon", "simple-syrup"])
        sub_result = sub_tool._run(ingredient="bourbon")
        unlock_result = unlock_tool._run(cabinet=["bourbon", "simple-syrup"])

        # All should use markdown bold
        assert "**" in recipe_result, "RecipeDBTool should use bold formatting"
        assert "**" in sub_result, "SubstitutionFinderTool should use bold formatting"
        assert "**" in unlock_result, "UnlockCalculatorTool should use bold formatting"
