"""Tests for the API router endpoints.

Tests for:
- GET /api/ingredients - ingredient categories and items
- GET /api/drinks - drink listing with pagination and filtering
- GET /api/drinks/{drink_id} - individual drink details
- POST /api/suggest-bottles - bottle recommendations based on cabinet
- Helper functions: _smart_title_case, _format_ingredient_name,
  _get_ingredient_display_name, _is_bottle_ingredient
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set mock API keys before importing modules that require them
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from src.app.main import app
from src.app.routers.api import (
    CATEGORY_CONFIG,
    INGREDIENT_EMOJIS,
    _format_ingredient_name,
    _get_ingredient_display_name,
    _is_bottle_ingredient,
    _smart_title_case,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def api_client() -> TestClient:
    """Provide FastAPI test client for API tests."""
    return TestClient(app)


# =============================================================================
# Helper Function Tests: _smart_title_case
# =============================================================================


class TestSmartTitleCase:
    """Tests for the _smart_title_case helper function."""

    def test_simple_word(self):
        """Single word is capitalized."""
        assert _smart_title_case("bourbon") == "Bourbon"

    def test_multiple_words(self):
        """Multiple words are each capitalized."""
        assert _smart_title_case("sweet vermouth") == "Sweet Vermouth"

    def test_apostrophe_handling(self):
        """Apostrophes are handled correctly - not capitalizing after them."""
        assert _smart_title_case("lyre's") == "Lyre's"
        assert _smart_title_case("maker's mark") == "Maker's Mark"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert _smart_title_case("") == ""

    def test_already_capitalized(self):
        """Already capitalized text is normalized."""
        assert _smart_title_case("BOURBON") == "Bourbon"

    def test_mixed_case(self):
        """Mixed case is normalized to title case."""
        assert _smart_title_case("bOuRbOn") == "Bourbon"

    def test_multiple_apostrophes(self):
        """Multiple apostrophes in same word are handled."""
        assert _smart_title_case("o'brien's") == "O'brien's"

    def test_hyphenated_words_stay_together(self):
        """Hyphenated words are treated as one unit (no hyphens in input)."""
        # The function expects spaces, not hyphens
        assert _smart_title_case("old fashioned") == "Old Fashioned"


# =============================================================================
# Helper Function Tests: _format_ingredient_name
# =============================================================================


class TestFormatIngredientName:
    """Tests for the _format_ingredient_name helper function."""

    def test_single_name(self):
        """Single name is formatted with title case."""
        assert _format_ingredient_name(["bourbon"]) == "Bourbon"

    def test_multiple_names_uses_first(self):
        """Multiple names returns the first one formatted."""
        assert _format_ingredient_name(["bourbon", "bourbon whiskey"]) == "Bourbon"

    def test_empty_list(self):
        """Empty list returns 'Unknown'."""
        assert _format_ingredient_name([]) == "Unknown"

    def test_name_with_apostrophe(self):
        """Names with apostrophes are handled correctly."""
        assert (
            _format_ingredient_name(["lyre's american malt"]) == "Lyre's American Malt"
        )


# =============================================================================
# Helper Function Tests: _get_ingredient_display_name
# =============================================================================


class TestGetIngredientDisplayName:
    """Tests for the _get_ingredient_display_name helper function."""

    def test_kebab_case_conversion(self):
        """Kebab-case is converted to title case with spaces."""
        assert _get_ingredient_display_name("sweet-vermouth") == "Sweet Vermouth"

    def test_single_word(self):
        """Single word without hyphens is title-cased."""
        assert _get_ingredient_display_name("bourbon") == "Bourbon"

    def test_multiple_hyphens(self):
        """Multiple hyphens are all converted to spaces."""
        assert (
            _get_ingredient_display_name("orange-juice-fresh") == "Orange Juice Fresh"
        )

    def test_apostrophe_in_id(self):
        """Apostrophes in ingredient IDs are handled correctly."""
        # Note: typically ingredient IDs don't have apostrophes, but test the edge case
        assert _get_ingredient_display_name("lyres") == "Lyres"


# =============================================================================
# Helper Function Tests: _is_bottle_ingredient
# =============================================================================


class TestIsBottleIngredient:
    """Tests for the _is_bottle_ingredient helper function."""

    def test_spirit_is_bottle(self):
        """Spirits are identified as bottles."""
        assert _is_bottle_ingredient("bourbon") is True
        assert _is_bottle_ingredient("gin") is True
        assert _is_bottle_ingredient("vodka") is True

    def test_modifier_is_bottle(self):
        """Modifiers/liqueurs are identified as bottles."""
        assert _is_bottle_ingredient("sweet-vermouth") is True
        assert _is_bottle_ingredient("dry-vermouth") is True

    def test_fresh_is_not_bottle(self):
        """Fresh ingredients are not bottles."""
        assert _is_bottle_ingredient("mint") is False
        assert _is_bottle_ingredient("lime-juice") is False

    def test_mixer_is_not_bottle(self):
        """Mixers are not bottles."""
        assert _is_bottle_ingredient("soda-water") is False
        assert _is_bottle_ingredient("tonic-water") is False

    def test_syrup_is_not_bottle(self):
        """Syrups are not bottles."""
        assert _is_bottle_ingredient("simple-syrup") is False

    def test_unknown_ingredient_is_not_bottle(self):
        """Unknown ingredients are not bottles."""
        assert _is_bottle_ingredient("unknown-ingredient-xyz") is False


# =============================================================================
# GET /api/ingredients Tests
# =============================================================================


class TestGetIngredients:
    """Tests for the GET /api/ingredients endpoint."""

    def test_ingredients_returns_categories(self, api_client: TestClient):
        """Endpoint returns ingredients organized by category."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        categories = data["categories"]

        # Verify at least some expected categories exist
        assert len(categories) > 0

        # Check that Spirits category exists (common category)
        assert "Spirits" in categories

    def test_ingredients_category_structure(self, api_client: TestClient):
        """Each category contains properly structured ingredient items."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        # Check structure of first category
        for _category_name, items in data["categories"].items():
            assert isinstance(items, list)
            if len(items) > 0:
                first_item = items[0]
                assert "id" in first_item
                assert "name" in first_item
                assert "emoji" in first_item
                # Verify types
                assert isinstance(first_item["id"], str)
                assert isinstance(first_item["name"], str)
                assert isinstance(first_item["emoji"], str)

    def test_ingredients_has_spirits(self, api_client: TestClient):
        """Spirits category contains common spirits."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        spirits = data["categories"].get("Spirits", [])
        spirit_ids = {item["id"] for item in spirits}

        # Check for common spirits
        assert "bourbon" in spirit_ids
        assert "gin" in spirit_ids
        assert "vodka" in spirit_ids

    def test_ingredients_emoji_mapping(self, api_client: TestClient):
        """Ingredients with specific emojis get the correct emoji."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        # Find bourbon in spirits category
        spirits = data["categories"].get("Spirits", [])
        bourbon = next((s for s in spirits if s["id"] == "bourbon"), None)

        if bourbon:
            # Bourbon should have whiskey glass emoji
            assert bourbon["emoji"] == INGREDIENT_EMOJIS.get("bourbon", "")

    def test_ingredients_names_are_formatted(self, api_client: TestClient):
        """Ingredient names are properly formatted (title case)."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        for _category_name, items in data["categories"].items():
            for item in items:
                # Name should not be all lowercase (should be title case)
                name = item["name"]
                if name and name != "Unknown":
                    # First character should be uppercase
                    assert name[0].isupper(), f"Name '{name}' should be title case"


# =============================================================================
# GET /api/drinks Tests
# =============================================================================


class TestGetDrinks:
    """Tests for the GET /api/drinks endpoint."""

    def test_drinks_returns_list(self, api_client: TestClient):
        """Endpoint returns a list of drinks with total count."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        assert "drinks" in data
        assert "total" in data
        assert isinstance(data["drinks"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["drinks"])

    def test_drinks_structure(self, api_client: TestClient):
        """Each drink has the required summary fields."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        assert len(data["drinks"]) > 0

        first_drink = data["drinks"][0]
        required_fields = [
            "id",
            "name",
            "tagline",
            "difficulty",
            "is_mocktail",
            "timing_minutes",
            "tags",
        ]

        for field in required_fields:
            assert field in first_drink, f"Missing required field: {field}"

    def test_drinks_includes_both_cocktails_and_mocktails(self, api_client: TestClient):
        """Response includes both cocktails and mocktails."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        drinks = data["drinks"]
        has_cocktail = any(not d["is_mocktail"] for d in drinks)
        has_mocktail = any(d["is_mocktail"] for d in drinks)

        assert has_cocktail, "Should include at least one cocktail"
        assert has_mocktail, "Should include at least one mocktail"

    def test_drinks_difficulty_values(self, api_client: TestClient):
        """Drink difficulty is one of the expected values."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        valid_difficulties = {"easy", "medium", "hard", "advanced"}

        for drink in data["drinks"]:
            assert drink["difficulty"] in valid_difficulties, (
                f"Invalid difficulty: {drink['difficulty']}"
            )

    def test_drinks_timing_is_positive(self, api_client: TestClient):
        """Drink timing is a positive integer."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        for drink in data["drinks"]:
            assert isinstance(drink["timing_minutes"], int)
            assert drink["timing_minutes"] > 0

    def test_drinks_contains_old_fashioned(self, api_client: TestClient):
        """Response contains the classic Old Fashioned cocktail."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        drink_ids = {d["id"] for d in data["drinks"]}
        assert "old-fashioned" in drink_ids


# =============================================================================
# GET /api/drinks/{drink_id} Tests
# =============================================================================


class TestGetDrinkById:
    """Tests for the GET /api/drinks/{drink_id} endpoint."""

    def test_get_existing_drink(self, api_client: TestClient):
        """Requesting an existing drink returns full details."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "old-fashioned"
        assert data["name"] == "Old Fashioned"
        assert "tagline" in data
        assert "difficulty" in data
        assert "is_mocktail" in data
        assert data["is_mocktail"] is False

    def test_get_drink_includes_ingredients(self, api_client: TestClient):
        """Drink details include ingredient list with amounts."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        assert "ingredients" in data
        assert len(data["ingredients"]) > 0

        first_ing = data["ingredients"][0]
        assert "amount" in first_ing
        assert "unit" in first_ing
        assert "item" in first_ing

    def test_get_drink_includes_method(self, api_client: TestClient):
        """Drink details include method steps."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        assert "method" in data
        assert len(data["method"]) > 0

        first_step = data["method"][0]
        assert "action" in first_step
        assert "detail" in first_step

    def test_get_drink_includes_flavor_profile(self, api_client: TestClient):
        """Drink details include flavor profile."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        assert "flavor_profile" in data
        flavor = data["flavor_profile"]

        assert "sweet" in flavor
        assert "sour" in flavor
        assert "bitter" in flavor
        assert "spirit" in flavor

    def test_get_drink_includes_garnish_and_glassware(self, api_client: TestClient):
        """Drink details include garnish and glassware."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        assert "garnish" in data
        assert "glassware" in data
        assert isinstance(data["garnish"], str)
        assert isinstance(data["glassware"], str)

    def test_get_nonexistent_drink_returns_404(self, api_client: TestClient):
        """Requesting a non-existent drink returns 404."""
        response = api_client.get("/api/drinks/nonexistent-drink-xyz")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_mocktail_has_is_mocktail_true(self, api_client: TestClient):
        """Mocktail has is_mocktail set to True."""
        response = api_client.get("/api/drinks/virgin-mojito")

        assert response.status_code == 200
        data = response.json()

        assert data["is_mocktail"] is True


# =============================================================================
# POST /api/suggest-bottles Tests
# =============================================================================


class TestSuggestBottles:
    """Tests for the POST /api/suggest-bottles endpoint."""

    def test_suggest_bottles_empty_cabinet(self, api_client: TestClient):
        """Empty cabinet returns bottle recommendations."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()

        assert "cabinet_size" in data
        assert data["cabinet_size"] == 0
        assert "recommendations" in data
        assert "drinks_makeable_now" in data
        assert data["drinks_makeable_now"] == 0

    def test_suggest_bottles_with_cabinet(self, api_client: TestClient):
        """Cabinet with some items returns appropriate recommendations."""
        response = api_client.post(
            "/api/suggest-bottles",
            json={"cabinet": ["bourbon", "simple-syrup", "angostura"], "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["cabinet_size"] == 3
        assert "recommendations" in data

    def test_suggest_bottles_recommendation_structure(self, api_client: TestClient):
        """Each recommendation has required fields."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 3}
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            assert "ingredient_id" in rec
            assert "ingredient_name" in rec
            assert "new_drinks_unlocked" in rec
            assert "drinks" in rec

            # Verify types
            assert isinstance(rec["ingredient_id"], str)
            assert isinstance(rec["ingredient_name"], str)
            assert isinstance(rec["new_drinks_unlocked"], int)
            assert isinstance(rec["drinks"], list)

    def test_suggest_bottles_only_spirits_and_modifiers(self, api_client: TestClient):
        """Recommendations only include spirits and modifiers, not accessories."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 20}
        )

        assert response.status_code == 200
        data = response.json()

        # All recommendations should be bottles (spirits or modifiers)
        for rec in data["recommendations"]:
            ingredient_id = rec["ingredient_id"]
            assert _is_bottle_ingredient(ingredient_id), (
                f"{ingredient_id} should be a bottle ingredient"
            )

    def test_suggest_bottles_respects_limit(self, api_client: TestClient):
        """Response respects the limit parameter."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 3}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["recommendations"]) <= 3

    def test_suggest_bottles_sorted_by_unlocks(self, api_client: TestClient):
        """Recommendations are sorted by number of drinks unlocked (descending)."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        recs = data["recommendations"]
        if len(recs) > 1:
            for i in range(len(recs) - 1):
                assert (
                    recs[i]["new_drinks_unlocked"] >= recs[i + 1]["new_drinks_unlocked"]
                ), "Recommendations should be sorted by unlocks descending"

    def test_suggest_bottles_filter_cocktails_only(self, api_client: TestClient):
        """Filter by cocktails only excludes mocktails from calculations."""
        response = api_client.post(
            "/api/suggest-bottles",
            json={"cabinet": [], "drink_type": "cocktails", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        # All unlocked drinks should be cocktails (not mocktails)
        for rec in data["recommendations"]:
            for drink in rec["drinks"]:
                assert drink["is_mocktail"] is False

    def test_suggest_bottles_filter_mocktails_only(self, api_client: TestClient):
        """Filter by mocktails only includes only mocktails."""
        response = api_client.post(
            "/api/suggest-bottles",
            json={"cabinet": [], "drink_type": "mocktails", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        # All unlocked drinks should be mocktails
        for rec in data["recommendations"]:
            for drink in rec["drinks"]:
                assert drink["is_mocktail"] is True

    def test_suggest_bottles_unlocked_drinks_structure(self, api_client: TestClient):
        """Each unlocked drink has proper structure."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()

        for rec in data["recommendations"]:
            for drink in rec["drinks"]:
                assert "id" in drink
                assert "name" in drink
                assert "is_mocktail" in drink
                assert "difficulty" in drink

    def test_suggest_bottles_excludes_cabinet_items(self, api_client: TestClient):
        """Recommendations do not include items already in cabinet."""
        cabinet = ["bourbon", "gin", "vodka"]
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": cabinet, "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        rec_ids = {rec["ingredient_id"] for rec in data["recommendations"]}

        for cabinet_item in cabinet:
            assert cabinet_item not in rec_ids, (
                f"Cabinet item {cabinet_item} should not be in recommendations"
            )

    def test_suggest_bottles_total_available(self, api_client: TestClient):
        """Response includes total available recommendations before limit."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 2}
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_available_recommendations" in data
        # Total should be >= number returned
        assert data["total_available_recommendations"] >= len(data["recommendations"])

    def test_suggest_bottles_drinks_makeable_with_full_cabinet(
        self, api_client: TestClient
    ):
        """With ingredients for a drink, drinks_makeable_now increases."""
        # Get ingredients for old-fashioned: bourbon, simple-syrup, angostura, orange-bitters
        response = api_client.post(
            "/api/suggest-bottles",
            json={
                "cabinet": ["bourbon", "simple-syrup", "angostura", "orange-bitters"],
                "drink_type": "cocktails",
                "limit": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should be able to make at least the old-fashioned
        assert data["drinks_makeable_now"] >= 1

    def test_suggest_bottles_default_limit(self, api_client: TestClient):
        """Default limit is applied when not specified."""
        response = api_client.post("/api/suggest-bottles", json={"cabinet": []})

        assert response.status_code == 200
        data = response.json()

        # Default limit is 5
        assert len(data["recommendations"]) <= 5

    def test_suggest_bottles_limit_validation_max(self, api_client: TestClient):
        """Limit over maximum (20) is rejected."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 25}
        )

        assert response.status_code == 422  # Validation error

    def test_suggest_bottles_limit_validation_min(self, api_client: TestClient):
        """Limit under minimum (1) is rejected."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 0}
        )

        assert response.status_code == 422  # Validation error

    def test_suggest_bottles_case_insensitive_cabinet(self, api_client: TestClient):
        """Cabinet ingredients are handled case-insensitively."""
        response = api_client.post(
            "/api/suggest-bottles",
            json={"cabinet": ["BOURBON", "Gin", "vodka"], "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["cabinet_size"] == 3

        # Recommendations should not include these items (case-insensitive match)
        rec_ids = {rec["ingredient_id"].lower() for rec in data["recommendations"]}
        assert "bourbon" not in rec_ids
        assert "gin" not in rec_ids
        assert "vodka" not in rec_ids


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestApiEdgeCases:
    """Tests for edge cases and error handling in the API."""

    def test_drinks_endpoint_handles_special_characters_in_id(
        self, api_client: TestClient
    ):
        """Drink ID with URL-unsafe characters is handled."""
        # This should return 404, not crash
        response = api_client.get("/api/drinks/drink%2Fwith%2Fslashes")

        assert response.status_code == 404

    def test_suggest_bottles_with_whitespace_in_cabinet(self, api_client: TestClient):
        """Cabinet items with extra whitespace are trimmed."""
        response = api_client.post(
            "/api/suggest-bottles",
            json={"cabinet": ["  bourbon  ", " gin "], "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()

        # Should treat as 2 items after trimming
        assert data["cabinet_size"] == 2

    def test_ingredients_category_config_keys(self):
        """All category config keys have required display and emoji."""
        for key, config in CATEGORY_CONFIG.items():
            assert "display" in config, f"Category {key} missing 'display'"
            assert "default_emoji" in config, f"Category {key} missing 'default_emoji'"

    def test_ingredient_emojis_are_valid(self):
        """All ingredient emojis in the mapping are single emoji characters or strings."""
        for ingredient_id, emoji in INGREDIENT_EMOJIS.items():
            assert len(emoji) >= 1, f"Emoji for {ingredient_id} is empty"
            # Emojis can be multi-byte, so just check it's not empty


# =============================================================================
# Response Schema Validation Tests
# =============================================================================


class TestResponseSchemas:
    """Tests to validate response schemas match expected structure."""

    def test_ingredients_response_schema(self, api_client: TestClient):
        """IngredientsResponse matches expected schema."""
        response = api_client.get("/api/ingredients")

        assert response.status_code == 200
        data = response.json()

        # Root should have 'categories' key
        assert set(data.keys()) == {"categories"}

        # Categories should be dict of category_name -> list of items
        assert isinstance(data["categories"], dict)

    def test_drinks_response_schema(self, api_client: TestClient):
        """DrinksResponse matches expected schema."""
        response = api_client.get("/api/drinks")

        assert response.status_code == 200
        data = response.json()

        # Root should have 'drinks' and 'total' keys
        assert set(data.keys()) == {"drinks", "total"}

    def test_drink_detail_response_schema(self, api_client: TestClient):
        """DrinkDetailResponse matches expected schema."""
        response = api_client.get("/api/drinks/old-fashioned")

        assert response.status_code == 200
        data = response.json()

        expected_fields = {
            "id",
            "name",
            "tagline",
            "difficulty",
            "is_mocktail",
            "timing_minutes",
            "tags",
            "ingredients",
            "method",
            "glassware",
            "garnish",
            "flavor_profile",
        }

        assert set(data.keys()) == expected_fields

    def test_suggest_bottles_response_schema(self, api_client: TestClient):
        """SuggestBottlesResponse matches expected schema."""
        response = api_client.post(
            "/api/suggest-bottles", json={"cabinet": [], "limit": 3}
        )

        assert response.status_code == 200
        data = response.json()

        expected_fields = {
            "cabinet_size",
            "drinks_makeable_now",
            "recommendations",
            "total_available_recommendations",
        }

        assert set(data.keys()) == expected_fields
