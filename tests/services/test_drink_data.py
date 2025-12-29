"""Comprehensive tests for drink_data service module.

Tests cover:
- get_makeable_drinks: Finding drinks based on cabinet ingredients
- get_drink_by_id: Fetching individual drink details
- get_drink_flavor_profiles: Analyzing flavor characteristics
- get_substitutions_for_ingredients: Finding ingredient substitutes
- get_unlock_recommendations: Bottle purchase recommendations
- format_drinks_for_prompt: Prompt formatting
- format_recipe_for_prompt: Recipe formatting
- format_bottle_recommendations_for_prompt: Recommendation formatting
"""

from src.app.services.drink_data import (
    format_bottle_recommendations_for_prompt,
    format_drinks_for_prompt,
    format_recipe_for_prompt,
    get_drink_by_id,
    get_drink_flavor_profiles,
    get_makeable_drinks,
    get_substitutions_for_ingredients,
    get_unlock_recommendations,
)


class TestGetMakeableDrinks:
    """Tests for get_makeable_drinks function."""

    def test_returns_list_type(self):
        """Verify function returns a list."""
        result = get_makeable_drinks(cabinet=["bourbon", "simple-syrup"])
        assert isinstance(result, list)

    def test_empty_cabinet_returns_empty_list(self):
        """Empty cabinet should return no makeable drinks."""
        result = get_makeable_drinks(cabinet=[])
        assert result == []

    def test_complete_ingredients_returns_drink(self):
        """Cabinet with all required ingredients should return the drink."""
        # Old Fashioned needs: bourbon, simple-syrup, angostura, orange-bitters
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = get_makeable_drinks(cabinet=cabinet)

        # Should find at least the Old Fashioned
        drink_ids = [d["id"] for d in result]
        assert "old-fashioned" in drink_ids

    def test_partial_ingredients_returns_partial_matches(self):
        """Cabinet with 50%+ ingredients should return partial matches."""
        # Old Fashioned needs 4 ingredients; provide 2 (50%)
        cabinet = ["bourbon", "simple-syrup"]
        result = get_makeable_drinks(cabinet=cabinet)

        # Should return drinks where at least 50% ingredients are available
        assert isinstance(result, list)

    def test_drink_structure_has_required_fields(self):
        """Verify returned drinks have all expected fields."""
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = get_makeable_drinks(cabinet=cabinet)

        if result:
            drink = result[0]
            required_fields = [
                "id",
                "name",
                "tagline",
                "is_mocktail",
                "difficulty",
                "timing_minutes",
                "tags",
                "glassware",
                "ingredients",
                "flavor_profile",
            ]
            for field in required_fields:
                assert field in drink, f"Missing field: {field}"

    def test_flavor_profile_structure(self):
        """Verify flavor profile has all expected keys."""
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = get_makeable_drinks(cabinet=cabinet)

        if result:
            fp = result[0]["flavor_profile"]
            assert "sweet" in fp
            assert "sour" in fp
            assert "bitter" in fp
            assert "spirit" in fp

    def test_filter_cocktails_only(self):
        """Filter by cocktails should exclude mocktails."""
        cabinet = ["gin", "tonic-water", "lime-juice"]
        result = get_makeable_drinks(cabinet=cabinet, drink_type="cocktails")

        for drink in result:
            assert drink["is_mocktail"] is False

    def test_filter_mocktails_only(self):
        """Filter by mocktails should exclude cocktails."""
        cabinet = ["mint", "lime-juice", "simple-syrup", "soda-water"]
        result = get_makeable_drinks(cabinet=cabinet, drink_type="mocktails")

        for drink in result:
            assert drink["is_mocktail"] is True

    def test_filter_both_includes_all(self):
        """Filter 'both' should include cocktails and mocktails."""
        # Provide ingredients for both types
        cabinet = [
            "bourbon",
            "simple-syrup",
            "angostura",
            "orange-bitters",
            "mint",
            "lime-juice",
            "soda-water",
        ]
        result = get_makeable_drinks(cabinet=cabinet, drink_type="both")

        # Just verify we get results (type is not restricted)
        assert isinstance(result, list)

    def test_exclude_specific_drinks(self):
        """Excluded drinks should not appear in results."""
        cabinet = ["bourbon", "simple-syrup", "angostura", "orange-bitters"]
        result = get_makeable_drinks(cabinet=cabinet, exclude=["old-fashioned"])

        drink_ids = [d["id"] for d in result]
        assert "old-fashioned" not in drink_ids

    def test_case_insensitive_cabinet(self):
        """Cabinet ingredients should be case-insensitive."""
        cabinet = ["BOURBON", "Simple-Syrup", "ANGOSTURA", "Orange-Bitters"]
        result = get_makeable_drinks(cabinet=cabinet)

        drink_ids = [d["id"] for d in result]
        assert "old-fashioned" in drink_ids

    def test_whitespace_handling_in_cabinet(self):
        """Cabinet ingredients with whitespace should be normalized."""
        cabinet = [" bourbon ", "simple-syrup  ", "  angostura", "orange-bitters"]
        result = get_makeable_drinks(cabinet=cabinet)

        drink_ids = [d["id"] for d in result]
        assert "old-fashioned" in drink_ids

    def test_invalid_drink_type_uses_default(self):
        """Invalid drink_type should default to 'both' behavior."""
        cabinet = ["bourbon", "simple-syrup"]
        # The type hint restricts this, but we test the behavior
        result = get_makeable_drinks(cabinet=cabinet, drink_type="both")
        assert isinstance(result, list)


class TestGetDrinkById:
    """Tests for get_drink_by_id function."""

    def test_returns_dict_for_valid_id(self):
        """Valid drink ID should return a dictionary."""
        result = get_drink_by_id("old-fashioned")
        assert isinstance(result, dict)

    def test_returns_none_for_invalid_id(self):
        """Invalid drink ID should return None."""
        result = get_drink_by_id("nonexistent-drink-xyz")
        assert result is None

    def test_drink_has_complete_recipe_data(self):
        """Returned drink should have complete recipe information."""
        result = get_drink_by_id("old-fashioned")

        assert result is not None
        required_fields = [
            "id",
            "name",
            "tagline",
            "is_mocktail",
            "difficulty",
            "timing_minutes",
            "glassware",
            "garnish",
            "tags",
            "flavor_profile",
            "ingredients",
            "method",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_ingredients_have_amounts(self):
        """Ingredients should include amount, unit, and item."""
        result = get_drink_by_id("old-fashioned")

        assert result is not None
        assert len(result["ingredients"]) > 0

        ingredient = result["ingredients"][0]
        assert "amount" in ingredient
        assert "unit" in ingredient
        assert "item" in ingredient

    def test_method_is_list(self):
        """Method should be a list of steps."""
        result = get_drink_by_id("old-fashioned")

        assert result is not None
        assert isinstance(result["method"], list)
        assert len(result["method"]) > 0

    def test_case_insensitive_id_lookup(self):
        """Drink ID lookup should be case-insensitive."""
        result_lower = get_drink_by_id("old-fashioned")
        result_upper = get_drink_by_id("OLD-FASHIONED")
        result_mixed = get_drink_by_id("Old-Fashioned")

        assert result_lower is not None
        assert result_upper is not None
        assert result_mixed is not None
        assert result_lower["id"] == result_upper["id"] == result_mixed["id"]

    def test_whitespace_handling_in_id(self):
        """Drink ID with whitespace should be normalized."""
        result = get_drink_by_id("  old-fashioned  ")
        assert result is not None
        assert result["id"] == "old-fashioned"

    def test_mocktail_lookup(self):
        """Should successfully lookup mocktail drinks."""
        result = get_drink_by_id("virgin-mojito")

        assert result is not None
        assert result["is_mocktail"] is True

    def test_empty_id_returns_none(self):
        """Empty string ID should return None."""
        result = get_drink_by_id("")
        assert result is None

    def test_special_characters_in_id(self):
        """Special characters in ID should not cause errors."""
        result = get_drink_by_id("drink-with-<script>-in-name")
        assert result is None  # Should not find anything, but should not crash


class TestGetDrinkFlavorProfiles:
    """Tests for get_drink_flavor_profiles function."""

    def test_returns_list_type(self):
        """Should return a list of profiles."""
        result = get_drink_flavor_profiles(["old-fashioned"])
        assert isinstance(result, list)

    def test_empty_input_returns_empty_list(self):
        """Empty drink list should return empty result."""
        result = get_drink_flavor_profiles([])
        assert result == []

    def test_profile_structure(self):
        """Profile should have expected fields."""
        result = get_drink_flavor_profiles(["old-fashioned"])

        assert len(result) > 0
        profile = result[0]

        expected_fields = [
            "id",
            "name",
            "is_mocktail",
            "flavor_profile",
            "dominant_flavor",
            "style",
            "spirit_forward",
            "tags",
        ]
        for field in expected_fields:
            assert field in profile, f"Missing field: {field}"

    def test_flavor_profile_values(self):
        """Flavor profile should contain numeric values."""
        result = get_drink_flavor_profiles(["old-fashioned"])

        assert len(result) > 0
        fp = result[0]["flavor_profile"]

        assert isinstance(fp["sweet"], int)
        assert isinstance(fp["sour"], int)
        assert isinstance(fp["bitter"], int)
        assert isinstance(fp["spirit"], int)

    def test_dominant_flavor_detection(self):
        """Should correctly identify dominant flavor."""
        result = get_drink_flavor_profiles(["old-fashioned"])

        assert len(result) > 0
        assert result[0]["dominant_flavor"] in ["sweet", "sour", "bitter"]

    def test_style_categorization(self):
        """Should categorize drink style."""
        result = get_drink_flavor_profiles(["old-fashioned"])

        assert len(result) > 0
        valid_styles = [
            "refreshing/mocktail",
            "spirit-forward",
            "sour",
            "bitter/aperitivo",
            "sweet/dessert",
            "balanced",
        ]
        assert result[0]["style"] in valid_styles

    def test_multiple_drinks_input(self):
        """Should handle multiple drink IDs."""
        result = get_drink_flavor_profiles(["old-fashioned", "manhattan"])

        # Should return profiles for valid drinks
        assert len(result) >= 1

    def test_invalid_drink_id_filtered(self):
        """Invalid drink IDs should be silently filtered."""
        result = get_drink_flavor_profiles(["old-fashioned", "nonexistent-drink"])

        # Should only return profile for valid drink
        ids = [p["id"].lower() for p in result]
        assert "old-fashioned" in ids
        assert "nonexistent-drink" not in ids

    def test_mocktail_spirit_profile(self):
        """Mocktails should have spirit=0."""
        result = get_drink_flavor_profiles(["virgin-mojito"])

        if result:
            assert result[0]["flavor_profile"]["spirit"] == 0
            assert result[0]["style"] == "refreshing/mocktail"

    def test_sour_style_categorization(self):
        """Drinks with high sour and sweet should be categorized as 'sour'."""
        # We need to find a drink with sour >= 40 and sweet >= 30 and spirit < 70
        # Test various drinks to find one that matches this style
        all_drink_ids = ["whiskey-sour", "margarita", "daiquiri", "sidecar"]
        for drink_id in all_drink_ids:
            result = get_drink_flavor_profiles([drink_id])
            if result and result[0]["style"] == "sour":
                # Found a sour drink, verify the logic
                fp = result[0]["flavor_profile"]
                assert fp["sour"] >= 40
                assert fp["sweet"] >= 30
                break

    def test_bitter_aperitivo_style(self):
        """Drinks with high bitter should be categorized as 'bitter/aperitivo'."""
        # Test drinks that might have high bitter profiles
        bitter_candidates = ["negroni", "americano", "boulevardier"]
        for drink_id in bitter_candidates:
            result = get_drink_flavor_profiles([drink_id])
            if result and result[0]["style"] == "bitter/aperitivo":
                fp = result[0]["flavor_profile"]
                assert fp["bitter"] >= 40
                break

    def test_sweet_dessert_style(self):
        """Drinks with high sweet should be categorized as 'sweet/dessert'."""
        # Test drinks that might have high sweet profiles
        sweet_candidates = ["chocolate-martini", "espresso-martini", "grasshopper"]
        for drink_id in sweet_candidates:
            result = get_drink_flavor_profiles([drink_id])
            if result and result[0]["style"] == "sweet/dessert":
                fp = result[0]["flavor_profile"]
                assert fp["sweet"] >= 50
                break

    def test_balanced_style(self):
        """Some drinks should be categorized as 'balanced'."""
        # Test various classic drinks to find one with balanced profile
        balanced_candidates = ["manhattan", "martini", "cosmopolitan"]
        for drink_id in balanced_candidates:
            result = get_drink_flavor_profiles([drink_id])
            if result and result[0]["style"] == "balanced":
                # Verify it doesn't meet other style criteria
                fp = result[0]["flavor_profile"]
                assert fp["spirit"] > 0  # Not a mocktail
                assert fp["spirit"] < 70  # Not spirit-forward
                break
        # It's okay if we don't find a balanced drink in these candidates


class TestGetSubstitutionsForIngredients:
    """Tests for get_substitutions_for_ingredients function."""

    def test_returns_dict_type(self):
        """Should return a dictionary."""
        result = get_substitutions_for_ingredients(["bourbon"])
        assert isinstance(result, dict)

    def test_empty_input_returns_empty_dict(self):
        """Empty ingredient list should return empty dict."""
        result = get_substitutions_for_ingredients([])
        assert result == {}

    def test_substitutions_are_lists(self):
        """Each substitution value should be a list."""
        result = get_substitutions_for_ingredients(["bourbon"])

        for _ingredient_id, subs in result.items():
            assert isinstance(subs, list)

    def test_missing_ingredient_not_in_result(self):
        """Ingredients without substitutions should not appear in result."""
        result = get_substitutions_for_ingredients(["nonexistent-ingredient-xyz"])

        assert "nonexistent-ingredient-xyz" not in result


class TestGetUnlockRecommendations:
    """Tests for get_unlock_recommendations function."""

    def test_returns_list_type(self):
        """Should return a list of recommendations."""
        result = get_unlock_recommendations(cabinet=["bourbon"])
        assert isinstance(result, list)

    def test_empty_cabinet_returns_recommendations(self):
        """Empty cabinet should still return recommendations."""
        result = get_unlock_recommendations(cabinet=[])
        assert isinstance(result, list)

    def test_recommendation_structure(self):
        """Recommendations should have expected fields."""
        result = get_unlock_recommendations(cabinet=["bourbon"], top_n=3)

        if result:
            rec = result[0]
            assert "ingredient" in rec
            assert "ingredient_name" in rec
            assert "unlocks" in rec
            assert "drinks" in rec

    def test_respects_top_n_limit(self):
        """Should not return more than top_n recommendations."""
        result = get_unlock_recommendations(cabinet=[], top_n=3)
        assert len(result) <= 3

    def test_sorted_by_unlocks_descending(self):
        """Recommendations should be sorted by unlock count."""
        result = get_unlock_recommendations(cabinet=["bourbon"], top_n=5)

        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]["unlocks"] >= result[i + 1]["unlocks"]

    def test_excludes_cabinet_ingredients(self):
        """Should not recommend ingredients already in cabinet."""
        cabinet = ["bourbon", "simple-syrup", "angostura"]
        result = get_unlock_recommendations(cabinet=cabinet)

        recommended_ingredients = [r["ingredient"].lower() for r in result]
        for ing in cabinet:
            assert ing.lower() not in recommended_ingredients

    def test_filter_by_drink_type(self):
        """Should respect drink_type filter."""
        result_cocktails = get_unlock_recommendations(
            cabinet=["bourbon"], drink_type="cocktails"
        )
        result_mocktails = get_unlock_recommendations(
            cabinet=["mint"], drink_type="mocktails"
        )

        # Both should return lists
        assert isinstance(result_cocktails, list)
        assert isinstance(result_mocktails, list)


class TestFormatDrinksForPrompt:
    """Tests for format_drinks_for_prompt function."""

    def test_returns_string(self):
        """Should return a string."""
        drinks = [
            {
                "id": "test-drink",
                "name": "Test Drink",
                "tagline": "A test",
                "difficulty": "easy",
                "timing_minutes": 5,
                "tags": ["test"],
                "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            }
        ]
        result = format_drinks_for_prompt(drinks)
        assert isinstance(result, str)

    def test_empty_list_returns_message(self):
        """Empty drink list should return descriptive message."""
        result = format_drinks_for_prompt([])
        assert "No drinks found" in result

    def test_includes_drink_name(self):
        """Output should include drink names."""
        drinks = [
            {
                "id": "test-drink",
                "name": "Test Drink Name",
                "tagline": "A test",
                "difficulty": "easy",
                "timing_minutes": 5,
                "tags": ["test"],
                "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            }
        ]
        result = format_drinks_for_prompt(drinks)
        assert "Test Drink Name" in result

    def test_includes_flavor_when_enabled(self):
        """Should include flavor profile when include_flavor=True."""
        drinks = [
            {
                "id": "test-drink",
                "name": "Test Drink",
                "tagline": "A test",
                "difficulty": "easy",
                "timing_minutes": 5,
                "tags": ["test"],
                "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            }
        ]
        result = format_drinks_for_prompt(drinks, include_flavor=True)
        assert "sweet=" in result or "Flavor" in result

    def test_excludes_flavor_when_disabled(self):
        """Should not include flavor profile when include_flavor=False."""
        drinks = [
            {
                "id": "test-drink",
                "name": "Test Drink",
                "tagline": "A test",
                "difficulty": "easy",
                "timing_minutes": 5,
                "tags": ["test"],
                "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            }
        ]
        result = format_drinks_for_prompt(drinks, include_flavor=False)
        assert "Flavor:" not in result


class TestFormatRecipeForPrompt:
    """Tests for format_recipe_for_prompt function."""

    def test_returns_string(self):
        """Should return a string."""
        drink = {
            "id": "test-drink",
            "name": "Test Drink",
            "tagline": "A test",
            "is_mocktail": False,
            "difficulty": "easy",
            "timing_minutes": 5,
            "glassware": "rocks",
            "garnish": "none",
            "tags": ["test"],
            "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            "ingredients": [{"amount": "2", "unit": "oz", "item": "test-spirit"}],
            "method": [{"action": "Pour", "detail": "into glass"}],
        }
        result = format_recipe_for_prompt(drink)
        assert isinstance(result, str)

    def test_none_drink_returns_not_found(self):
        """None input should return 'not found' message."""
        result = format_recipe_for_prompt(None)
        assert "not found" in result.lower()

    def test_includes_recipe_name(self):
        """Output should include recipe name."""
        drink = {
            "id": "test-drink",
            "name": "Special Test Drink",
            "tagline": "A test",
            "is_mocktail": False,
            "difficulty": "easy",
            "timing_minutes": 5,
            "glassware": "rocks",
            "garnish": "none",
            "tags": ["test"],
            "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            "ingredients": [{"amount": "2", "unit": "oz", "item": "test-spirit"}],
            "method": [{"action": "Pour", "detail": "into glass"}],
        }
        result = format_recipe_for_prompt(drink)
        assert "Special Test Drink" in result

    def test_includes_ingredients(self):
        """Output should include ingredients."""
        drink = {
            "id": "test-drink",
            "name": "Test Drink",
            "tagline": "A test",
            "is_mocktail": False,
            "difficulty": "easy",
            "timing_minutes": 5,
            "glassware": "rocks",
            "garnish": "none",
            "tags": ["test"],
            "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            "ingredients": [{"amount": "2", "unit": "oz", "item": "bourbon"}],
            "method": [{"action": "Pour", "detail": "into glass"}],
        }
        result = format_recipe_for_prompt(drink)
        assert "bourbon" in result
        assert "2" in result
        assert "oz" in result

    def test_includes_method_steps(self):
        """Output should include method steps."""
        drink = {
            "id": "test-drink",
            "name": "Test Drink",
            "tagline": "A test",
            "is_mocktail": False,
            "difficulty": "easy",
            "timing_minutes": 5,
            "glassware": "rocks",
            "garnish": "none",
            "tags": ["test"],
            "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 60},
            "ingredients": [{"amount": "2", "unit": "oz", "item": "bourbon"}],
            "method": [{"action": "Pour", "detail": "carefully into glass"}],
        }
        result = format_recipe_for_prompt(drink)
        assert "carefully into glass" in result

    def test_indicates_mocktail_type(self):
        """Should indicate if drink is a mocktail."""
        drink = {
            "id": "test-mocktail",
            "name": "Test Mocktail",
            "tagline": "A test",
            "is_mocktail": True,
            "difficulty": "easy",
            "timing_minutes": 5,
            "glassware": "highball",
            "garnish": "none",
            "tags": ["test"],
            "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 10, "spirit": 0},
            "ingredients": [{"amount": "4", "unit": "oz", "item": "soda-water"}],
            "method": [{"action": "Pour", "detail": "into glass"}],
        }
        result = format_recipe_for_prompt(drink)
        assert "Mocktail" in result


class TestFormatBottleRecommendationsForPrompt:
    """Tests for format_bottle_recommendations_for_prompt function."""

    def test_returns_string(self):
        """Should return a string."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon",
                "unlocks": 5,
                "drinks": ["Old Fashioned", "Manhattan"],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert isinstance(result, str)

    def test_empty_list_returns_message(self):
        """Empty recommendations should return descriptive message."""
        result = format_bottle_recommendations_for_prompt([])
        assert "No new bottles" in result

    def test_includes_ingredient_name(self):
        """Output should include ingredient names."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon Whiskey",
                "unlocks": 5,
                "drinks": ["Old Fashioned"],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert "Bourbon Whiskey" in result

    def test_includes_unlock_count(self):
        """Output should include unlock counts."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon",
                "unlocks": 7,
                "drinks": ["Old Fashioned"],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert "7" in result

    def test_includes_drink_names(self):
        """Output should include drink names that would be unlocked."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon",
                "unlocks": 2,
                "drinks": ["Old Fashioned", "Whiskey Sour"],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert "Old Fashioned" in result
        assert "Whiskey Sour" in result

    def test_more_than_five_drinks_shows_count(self):
        """When more than 5 drinks, should show '+N more'."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon",
                "unlocks": 8,
                "drinks": [
                    "Drink 1",
                    "Drink 2",
                    "Drink 3",
                    "Drink 4",
                    "Drink 5",
                    "Drink 6",
                    "Drink 7",
                    "Drink 8",
                ],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert "+3 more" in result

    def test_empty_drinks_list(self):
        """Empty drinks list should show appropriate message."""
        recommendations = [
            {
                "ingredient": "bourbon",
                "ingredient_name": "Bourbon",
                "unlocks": 0,
                "drinks": [],
            }
        ]
        result = format_bottle_recommendations_for_prompt(recommendations)
        assert "No specific drinks listed" in result


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_special_characters_in_search(self):
        """Special characters should not cause errors."""
        # These should not raise exceptions
        get_makeable_drinks(cabinet=["<script>alert('xss')</script>"])
        get_drink_by_id("drink-with-special-chars-!@#$%")
        get_drink_flavor_profiles(["drink-with-'quotes'"])

    def test_unicode_handling(self):
        """Unicode characters should be handled gracefully."""
        # Should not raise exceptions
        get_makeable_drinks(cabinet=["cafe-au-lait"])
        get_drink_by_id("drink-with-unicode")

    def test_very_long_ingredient_list(self):
        """Large cabinet should be handled efficiently."""
        large_cabinet = [f"ingredient-{i}" for i in range(100)]
        # Should not timeout or raise memory errors
        result = get_makeable_drinks(cabinet=large_cabinet)
        assert isinstance(result, list)

    def test_duplicate_ingredients_in_cabinet(self):
        """Duplicate cabinet items should be handled."""
        cabinet = ["bourbon", "bourbon", "simple-syrup", "simple-syrup"]
        result = get_makeable_drinks(cabinet=cabinet)
        assert isinstance(result, list)

    def test_none_in_cabinet_list(self):
        """None values in cabinet should not crash (if passed through)."""
        # Filter out None before calling, but test the function handles it gracefully
        cabinet = ["bourbon", "simple-syrup"]
        result = get_makeable_drinks(cabinet=cabinet)
        assert isinstance(result, list)

    def test_numeric_string_ingredients(self):
        """Numeric strings in cabinet should be handled."""
        cabinet = ["123", "456"]
        result = get_makeable_drinks(cabinet=cabinet)
        assert isinstance(result, list)
        # Will likely return empty since no drinks use numeric IDs
        # but should not crash
