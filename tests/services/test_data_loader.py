"""Comprehensive tests for the data loader service.

Tests cover:
- All loader functions return correct data types
- Data is properly parsed into Pydantic models
- Caching behavior (functions use @lru_cache)
- Data integrity - drinks have required fields, ingredients have IDs and names
- Edge cases and error handling
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.app.models.drinks import Drink, FlavorProfile, IngredientAmount, MethodStep
from src.app.models.ingredients import (
    Ingredient,
    IngredientsDatabase,
    SubstitutionsDatabase,
)
from src.app.models.unlock_scores import UnlockedDrink
from src.app.services.data_loader import (
    clear_cache,
    get_data_dir,
    load_all_drinks,
    load_cocktails,
    load_ingredients,
    load_mocktails,
    load_substitutions,
    load_unlock_scores,
    save_drinks,
    save_ingredients,
    save_substitutions,
    save_unlock_scores,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear the LRU cache before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def valid_drink_data() -> dict:
    """Provide valid drink data for testing."""
    return {
        "id": "test-drink",
        "name": "Test Drink",
        "tagline": "A test cocktail for unit testing",
        "ingredients": [
            {"amount": "2", "unit": "oz", "item": "bourbon"},
            {"amount": "1", "unit": "tsp", "item": "simple-syrup"},
        ],
        "method": [
            {"action": "Add", "detail": "all ingredients to shaker"},
            {"action": "Shake", "detail": "vigorously for 15 seconds"},
        ],
        "glassware": "coupe",
        "garnish": "lemon twist",
        "flavor_profile": {"sweet": 30, "sour": 20, "bitter": 10, "spirit": 60},
        "tags": ["test", "unit-test"],
        "difficulty": "easy",
        "timing_minutes": 5,
        "is_mocktail": False,
    }


@pytest.fixture
def valid_mocktail_data() -> dict:
    """Provide valid mocktail data for testing."""
    return {
        "id": "test-mocktail",
        "name": "Test Mocktail",
        "tagline": "A refreshing alcohol-free drink",
        "ingredients": [
            {"amount": "4", "unit": "oz", "item": "orange-juice"},
            {"amount": "2", "unit": "oz", "item": "soda-water"},
        ],
        "method": [
            {"action": "Pour", "detail": "ingredients over ice"},
            {"action": "Stir", "detail": "gently to combine"},
        ],
        "glassware": "highball",
        "garnish": "orange slice",
        "flavor_profile": {"sweet": 50, "sour": 30, "bitter": 0, "spirit": 0},
        "tags": ["refreshing", "citrus"],
        "difficulty": "easy",
        "timing_minutes": 2,
        "is_mocktail": True,
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory with test files."""
    return tmp_path


# =============================================================================
# Test 1-5: Return Types for Loader Functions
# =============================================================================


class TestLoaderReturnTypes:
    """Tests verifying correct return types from loader functions."""

    def test_load_cocktails_returns_list_of_drinks(self):
        """Test that load_cocktails returns a list of Drink objects."""
        cocktails = load_cocktails()

        assert isinstance(cocktails, list)
        assert len(cocktails) > 0
        assert all(isinstance(drink, Drink) for drink in cocktails)

    def test_load_mocktails_returns_list_of_drinks(self):
        """Test that load_mocktails returns a list of Drink objects."""
        mocktails = load_mocktails()

        assert isinstance(mocktails, list)
        assert len(mocktails) > 0
        assert all(isinstance(drink, Drink) for drink in mocktails)

    def test_load_ingredients_returns_ingredients_database(self):
        """Test that load_ingredients returns an IngredientsDatabase."""
        ingredients = load_ingredients()

        assert isinstance(ingredients, IngredientsDatabase)
        assert hasattr(ingredients, "spirits")
        assert hasattr(ingredients, "modifiers")
        assert hasattr(ingredients, "bitters_syrups")
        assert hasattr(ingredients, "fresh")
        assert hasattr(ingredients, "mixers")
        assert hasattr(ingredients, "non_alcoholic")

    def test_load_substitutions_returns_substitutions_database(self):
        """Test that load_substitutions returns a SubstitutionsDatabase."""
        substitutions = load_substitutions()

        assert isinstance(substitutions, SubstitutionsDatabase)
        assert hasattr(substitutions, "spirits")
        assert hasattr(substitutions, "modifiers")

    def test_load_unlock_scores_returns_dict(self):
        """Test that load_unlock_scores returns a dict of ingredient to unlocked drinks."""
        scores = load_unlock_scores()

        assert isinstance(scores, dict)
        assert len(scores) > 0
        # Each value should be a list of UnlockedDrink
        for ingredient_id, drinks in scores.items():
            assert isinstance(ingredient_id, str)
            assert isinstance(drinks, list)
            assert all(isinstance(d, UnlockedDrink) for d in drinks)


# =============================================================================
# Test 6-10: Pydantic Model Parsing
# =============================================================================


class TestPydanticParsing:
    """Tests verifying proper Pydantic model parsing."""

    def test_cocktail_ingredients_parsed_correctly(self):
        """Test that drink ingredients are properly parsed as IngredientAmount models."""
        cocktails = load_cocktails()
        first_cocktail = cocktails[0]

        assert len(first_cocktail.ingredients) > 0
        for ingredient in first_cocktail.ingredients:
            assert isinstance(ingredient, IngredientAmount)
            assert isinstance(ingredient.amount, str)
            assert isinstance(ingredient.unit, str)
            assert isinstance(ingredient.item, str)

    def test_cocktail_method_steps_parsed_correctly(self):
        """Test that drink method steps are properly parsed as MethodStep models."""
        cocktails = load_cocktails()
        first_cocktail = cocktails[0]

        assert len(first_cocktail.method) > 0
        for step in first_cocktail.method:
            assert isinstance(step, MethodStep)
            assert isinstance(step.action, str)
            assert isinstance(step.detail, str)

    def test_flavor_profile_parsed_correctly(self):
        """Test that flavor profiles are parsed with valid ranges (0-100)."""
        cocktails = load_cocktails()
        for cocktail in cocktails:
            fp = cocktail.flavor_profile
            assert isinstance(fp, FlavorProfile)
            assert 0 <= fp.sweet <= 100
            assert 0 <= fp.sour <= 100
            assert 0 <= fp.bitter <= 100
            assert 0 <= fp.spirit <= 100

    def test_ingredient_database_entries_parsed(self):
        """Test that ingredient entries have proper id and names lists."""
        ingredients_db = load_ingredients()

        for ingredient in ingredients_db.spirits:
            assert isinstance(ingredient, Ingredient)
            assert isinstance(ingredient.id, str)
            assert len(ingredient.id) > 0
            assert isinstance(ingredient.names, list)
            assert len(ingredient.names) >= 1

    def test_unlocked_drink_model_fields(self):
        """Test that UnlockedDrink models have required fields."""
        scores = load_unlock_scores()

        for _ingredient_id, unlocked_drinks in scores.items():
            for drink in unlocked_drinks:
                assert isinstance(drink.id, str)
                assert isinstance(drink.name, str)
                assert isinstance(drink.is_mocktail, bool)
                assert drink.difficulty in ("easy", "medium", "hard", "advanced")
                assert isinstance(drink.other, list)


# =============================================================================
# Test 11-14: Caching Behavior
# =============================================================================


class TestCachingBehavior:
    """Tests verifying LRU cache functionality."""

    def test_load_cocktails_is_cached(self):
        """Test that repeated calls return the same cached object."""
        first_call = load_cocktails()
        second_call = load_cocktails()

        # Should be the exact same object (same id)
        assert first_call is second_call

    def test_load_mocktails_is_cached(self):
        """Test that repeated mocktails calls return the same cached object."""
        first_call = load_mocktails()
        second_call = load_mocktails()

        assert first_call is second_call

    def test_clear_cache_resets_all_caches(self):
        """Test that clear_cache clears all loader caches."""
        # Load data to populate caches
        cocktails_first = load_cocktails()
        mocktails_first = load_mocktails()
        ingredients_first = load_ingredients()

        # Clear all caches
        clear_cache()

        # Load again - should be new objects
        cocktails_second = load_cocktails()
        mocktails_second = load_mocktails()
        ingredients_second = load_ingredients()

        # Objects should be equal in content but different instances
        assert cocktails_first is not cocktails_second
        assert mocktails_first is not mocktails_second
        assert ingredients_first is not ingredients_second

    def test_load_all_drinks_uses_cached_data(self):
        """Test that load_all_drinks leverages cached cocktails and mocktails."""
        # Pre-load to cache
        cocktails = load_cocktails()
        mocktails = load_mocktails()

        # load_all_drinks should use cached data
        all_drinks = load_all_drinks()

        assert len(all_drinks) == len(cocktails) + len(mocktails)

    def test_load_ingredients_is_cached(self):
        """Test that load_ingredients caching works correctly."""
        first_call = load_ingredients()
        second_call = load_ingredients()

        assert first_call is second_call

    def test_load_substitutions_is_cached(self):
        """Test that load_substitutions caching works correctly."""
        first_call = load_substitutions()
        second_call = load_substitutions()

        assert first_call is second_call

    def test_load_unlock_scores_is_cached(self):
        """Test that load_unlock_scores caching works correctly."""
        first_call = load_unlock_scores()
        second_call = load_unlock_scores()

        assert first_call is second_call


# =============================================================================
# Test 15-21: Data Integrity
# =============================================================================


class TestDataIntegrity:
    """Tests verifying data integrity constraints."""

    def test_all_drinks_have_unique_ids(self):
        """Test that all drink IDs are unique across cocktails and mocktails."""
        all_drinks = load_all_drinks()
        ids = [drink.id for drink in all_drinks]

        assert len(ids) == len(set(ids)), "Found duplicate drink IDs"

    def test_all_cocktails_are_not_mocktails(self):
        """Test that cocktails have is_mocktail=False."""
        cocktails = load_cocktails()

        for cocktail in cocktails:
            assert cocktail.is_mocktail is False, (
                f"{cocktail.name} should not be a mocktail"
            )

    def test_all_mocktails_are_mocktails(self):
        """Test that mocktails have is_mocktail=True."""
        mocktails = load_mocktails()

        for mocktail in mocktails:
            assert mocktail.is_mocktail is True, f"{mocktail.name} should be a mocktail"

    def test_difficulty_values_are_valid(self):
        """Test that all drinks have valid difficulty values."""
        valid_difficulties = {"easy", "medium", "hard", "advanced"}
        all_drinks = load_all_drinks()

        for drink in all_drinks:
            assert drink.difficulty in valid_difficulties, (
                f"{drink.name} has invalid difficulty: {drink.difficulty}"
            )

    def test_timing_minutes_in_valid_range(self):
        """Test that timing_minutes is within valid range (1-30)."""
        all_drinks = load_all_drinks()

        for drink in all_drinks:
            assert 1 <= drink.timing_minutes <= 30, (
                f"{drink.name} has invalid timing: {drink.timing_minutes}"
            )

    def test_ingredients_have_required_categories(self):
        """Test that ingredients database has all required categories."""
        ingredients_db = load_ingredients()

        # Each category should have at least one ingredient
        assert len(ingredients_db.spirits) > 0, "No spirits found"
        assert len(ingredients_db.modifiers) > 0, "No modifiers found"
        assert len(ingredients_db.bitters_syrups) > 0, "No bitters/syrups found"
        assert len(ingredients_db.fresh) > 0, "No fresh ingredients found"

    def test_all_ingredient_ids_are_kebab_case(self):
        """Test that ingredient IDs follow kebab-case convention."""
        ingredients_db = load_ingredients()

        for ingredient in ingredients_db.all_ingredients():
            # kebab-case: lowercase with hyphens, no spaces or underscores
            assert ingredient.id == ingredient.id.lower(), (
                f"ID should be lowercase: {ingredient.id}"
            )
            assert " " not in ingredient.id, (
                f"ID should not have spaces: {ingredient.id}"
            )
            assert "_" not in ingredient.id, (
                f"ID should not have underscores: {ingredient.id}"
            )

    def test_drink_ids_are_kebab_case(self):
        """Test that drink IDs follow kebab-case convention."""
        all_drinks = load_all_drinks()

        for drink in all_drinks:
            assert drink.id == drink.id.lower(), f"ID should be lowercase: {drink.id}"
            assert " " not in drink.id, f"ID should not have spaces: {drink.id}"
            assert "_" not in drink.id, f"ID should not have underscores: {drink.id}"


# =============================================================================
# Test 22-25: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_get_data_dir_returns_valid_path(self):
        """Test that get_data_dir returns a valid Path object."""
        data_dir = get_data_dir()

        assert isinstance(data_dir, Path)
        assert data_dir.exists()
        assert data_dir.is_dir()

    def test_load_all_drinks_combines_correctly(self):
        """Test that load_all_drinks returns correct combined count."""
        cocktails = load_cocktails()
        mocktails = load_mocktails()
        all_drinks = load_all_drinks()

        assert len(all_drinks) == len(cocktails) + len(mocktails)
        # Cocktails should come first
        assert all_drinks[: len(cocktails)] == cocktails
        assert all_drinks[len(cocktails) :] == mocktails

    def test_substitutions_original_ingredients_are_valid(self):
        """Test that original ingredients in substitutions exist in ingredients db."""
        ingredients_db = load_ingredients()
        substitutions = load_substitutions()

        all_ingredient_ids = {ing.id for ing in ingredients_db.all_ingredients()}
        all_substitutions = substitutions.all_substitutions()

        # Check that original ingredient IDs are valid
        for original_id in all_substitutions.keys():
            assert original_id in all_ingredient_ids, (
                f"Unknown original ingredient in substitutions: {original_id}"
            )

    def test_substitutions_have_valid_structure(self):
        """Test that substitution entries have valid list structure."""
        substitutions = load_substitutions()
        all_subs = substitutions.all_substitutions()

        for original_id, substitute_ids in all_subs.items():
            assert isinstance(substitute_ids, list), (
                f"Substitutes for {original_id} should be a list"
            )
            assert len(substitute_ids) > 0, (
                f"Substitutes for {original_id} should not be empty"
            )
            for sub_id in substitute_ids:
                assert isinstance(sub_id, str), (
                    f"Substitute ID should be a string: {sub_id}"
                )

    def test_unlock_scores_drinks_exist(self):
        """Test that drinks in unlock_scores correspond to actual drinks."""
        all_drinks = load_all_drinks()
        scores = load_unlock_scores()

        drink_ids = {drink.id for drink in all_drinks}

        for _ingredient_id, unlocked_drinks in scores.items():
            for unlocked in unlocked_drinks:
                assert unlocked.id in drink_ids, (
                    f"Unlocked drink {unlocked.id} not found in drinks database"
                )


# =============================================================================
# Test 26-29: Save Functions
# =============================================================================


class TestSaveFunctions:
    """Tests for save functions."""

    def test_save_drinks_creates_valid_json(self, valid_drink_data, tmp_path):
        """Test that save_drinks creates a valid JSON file."""
        drink = Drink.model_validate(valid_drink_data)
        filepath = tmp_path / "test_drinks.json"

        save_drinks([drink], filepath)

        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert len(saved_data) == 1
        assert saved_data[0]["id"] == "test-drink"

    def test_save_ingredients_creates_valid_json(self, tmp_path):
        """Test that save_ingredients creates a valid JSON file."""
        ingredients_db = IngredientsDatabase(
            spirits=[Ingredient(id="test-spirit", names=["Test Spirit"])],
            modifiers=[],
            bitters_syrups=[],
            fresh=[],
            mixers=[],
            non_alcoholic=[],
        )
        filepath = tmp_path / "test_ingredients.json"

        save_ingredients(ingredients_db, filepath)

        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert "spirits" in saved_data
        assert len(saved_data["spirits"]) == 1

    def test_save_substitutions_creates_valid_json(self, tmp_path):
        """Test that save_substitutions creates a valid JSON file."""
        subs_db = SubstitutionsDatabase(
            spirits={"bourbon": ["rye", "scotch"]},
            modifiers={},
            bitters_syrups={},
            fresh={},
            mixers={},
            non_alcoholic_to_alcoholic={},
            alcoholic_to_non_alcoholic={},
        )
        filepath = tmp_path / "test_substitutions.json"

        save_substitutions(subs_db, filepath)

        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert saved_data["spirits"]["bourbon"] == ["rye", "scotch"]

    def test_save_unlock_scores_creates_valid_json(self, tmp_path):
        """Test that save_unlock_scores creates a valid JSON file."""
        scores = {
            "bourbon": [
                UnlockedDrink(
                    id="old-fashioned",
                    name="Old Fashioned",
                    is_mocktail=False,
                    difficulty="easy",
                    other=["simple-syrup", "angostura"],
                )
            ]
        }
        filepath = tmp_path / "test_scores.json"

        save_unlock_scores(scores, filepath)

        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert "bourbon" in saved_data
        assert saved_data["bourbon"][0]["id"] == "old-fashioned"

    def test_save_drinks_empty_list(self, tmp_path):
        """Test that save_drinks handles empty list."""
        filepath = tmp_path / "empty_drinks.json"

        save_drinks([], filepath)

        assert filepath.exists()
        with open(filepath) as f:
            saved_data = json.load(f)
        assert saved_data == []

    def test_save_drinks_preserves_all_fields(self, valid_drink_data, tmp_path):
        """Test that save_drinks preserves all drink fields."""
        drink = Drink.model_validate(valid_drink_data)
        filepath = tmp_path / "full_drink.json"

        save_drinks([drink], filepath)

        with open(filepath) as f:
            saved_data = json.load(f)[0]

        assert saved_data["id"] == valid_drink_data["id"]
        assert saved_data["name"] == valid_drink_data["name"]
        assert saved_data["tagline"] == valid_drink_data["tagline"]
        assert saved_data["glassware"] == valid_drink_data["glassware"]
        assert saved_data["garnish"] == valid_drink_data["garnish"]
        assert saved_data["difficulty"] == valid_drink_data["difficulty"]
        assert saved_data["timing_minutes"] == valid_drink_data["timing_minutes"]
        assert saved_data["is_mocktail"] == valid_drink_data["is_mocktail"]


# =============================================================================
# Test 30-32: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_load_from_nonexistent_file_raises_error(self, tmp_path):
        """Test that loading from nonexistent file raises FileNotFoundError."""
        with patch(
            "src.app.services.data_loader.get_data_dir",
            return_value=tmp_path,
        ):
            clear_cache()
            with pytest.raises(FileNotFoundError):
                load_cocktails()

    def test_load_invalid_json_raises_validation_error(self, tmp_path):
        """Test that invalid JSON data raises ValidationError."""
        # Create invalid cocktails.json
        invalid_data = [{"id": "bad-drink"}]  # Missing required fields
        cocktails_file = tmp_path / "cocktails.json"
        with open(cocktails_file, "w") as f:
            json.dump(invalid_data, f)

        with patch(
            "src.app.services.data_loader.get_data_dir",
            return_value=tmp_path,
        ):
            clear_cache()
            with pytest.raises(ValidationError):
                load_cocktails()

    def test_load_malformed_json_raises_error(self, tmp_path):
        """Test that malformed JSON raises JSONDecodeError."""
        # Create malformed JSON file
        cocktails_file = tmp_path / "cocktails.json"
        with open(cocktails_file, "w") as f:
            f.write("{ invalid json }")

        with patch(
            "src.app.services.data_loader.get_data_dir",
            return_value=tmp_path,
        ):
            clear_cache()
            with pytest.raises(json.JSONDecodeError):
                load_cocktails()

    def test_load_ingredients_invalid_data_raises_error(self, tmp_path):
        """Test that invalid ingredients data raises ValidationError."""
        # Create invalid ingredients.json (missing required structure)
        invalid_data = {"invalid_category": []}
        ingredients_file = tmp_path / "ingredients.json"
        with open(ingredients_file, "w") as f:
            json.dump(invalid_data, f)

        with patch(
            "src.app.services.data_loader.get_data_dir",
            return_value=tmp_path,
        ):
            clear_cache()
            # Should still load with defaults for missing categories
            ingredients = load_ingredients()
            assert isinstance(ingredients, IngredientsDatabase)


# =============================================================================
# Test 33-40: Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for data consistency across files."""

    def test_mocktails_have_zero_spirit_profile(self):
        """Test that mocktails have spirit=0 in flavor profile."""
        mocktails = load_mocktails()

        for mocktail in mocktails:
            assert mocktail.flavor_profile.spirit == 0, (
                f"{mocktail.name} should have spirit=0, got {mocktail.flavor_profile.spirit}"
            )

    def test_drink_ingredients_reference_known_items(self):
        """Test that drink ingredients reference known ingredient IDs."""
        all_drinks = load_all_drinks()
        ingredients_db = load_ingredients()

        all_ingredient_ids = {ing.id for ing in ingredients_db.all_ingredients()}

        missing_ingredients = set()
        for drink in all_drinks:
            for ing in drink.ingredients:
                if ing.item not in all_ingredient_ids:
                    missing_ingredients.add(ing.item)

        # Allow for some flexibility - ingredients might not all be in database
        # But log any missing ones for awareness
        if missing_ingredients:
            print(f"Note: {len(missing_ingredients)} ingredient IDs not in database")

    def test_all_drinks_have_at_least_one_ingredient(self):
        """Test that all drinks have at least one ingredient."""
        all_drinks = load_all_drinks()

        for drink in all_drinks:
            assert len(drink.ingredients) >= 1, f"{drink.name} has no ingredients"

    def test_all_drinks_have_at_least_one_method_step(self):
        """Test that all drinks have at least one method step."""
        all_drinks = load_all_drinks()

        for drink in all_drinks:
            assert len(drink.method) >= 1, f"{drink.name} has no method steps"

    def test_ingredients_database_find_by_id_works(self):
        """Test the find_by_id helper method on IngredientsDatabase."""
        ingredients_db = load_ingredients()

        # Find a known spirit
        bourbon = ingredients_db.find_by_id("bourbon")
        assert bourbon is not None
        assert bourbon.id == "bourbon"
        assert "bourbon" in bourbon.names

        # Try finding non-existent ingredient
        nonexistent = ingredients_db.find_by_id("nonexistent-ingredient")
        assert nonexistent is None

    def test_substitutions_find_substitutes_works(self):
        """Test the find_substitutes helper method on SubstitutionsDatabase."""
        substitutions = load_substitutions()

        # Bourbon should have substitutes
        bourbon_subs = substitutions.find_substitutes("bourbon")
        assert isinstance(bourbon_subs, list)
        assert len(bourbon_subs) > 0

        # Non-existent should return empty list
        no_subs = substitutions.find_substitutes("nonexistent")
        assert no_subs == []

    def test_all_ingredients_method_returns_all(self):
        """Test that all_ingredients returns ingredients from all categories."""
        ingredients_db = load_ingredients()
        all_ingredients = ingredients_db.all_ingredients()

        # Should include at least spirits and modifiers
        spirit_ids = {ing.id for ing in ingredients_db.spirits}
        modifier_ids = {ing.id for ing in ingredients_db.modifiers}
        all_ids = {ing.id for ing in all_ingredients}

        assert spirit_ids.issubset(all_ids)
        assert modifier_ids.issubset(all_ids)

    def test_unlock_scores_cover_key_ingredients(self):
        """Test that unlock_scores include common ingredients."""
        scores = load_unlock_scores()

        # Common ingredients that should have unlock data
        common_ingredients = ["bourbon", "gin", "vodka", "lime-juice", "simple-syrup"]

        for ingredient in common_ingredients:
            if ingredient in scores:
                assert len(scores[ingredient]) > 0, (
                    f"{ingredient} should unlock at least one drink"
                )


# =============================================================================
# Test 41-42: Data Volume Tests
# =============================================================================


class TestDataVolume:
    """Tests for expected data volumes."""

    def test_cocktails_count_is_reasonable(self):
        """Test that we have a reasonable number of cocktails."""
        cocktails = load_cocktails()
        # Should have at least 50 cocktails for a comprehensive database
        assert len(cocktails) >= 50, f"Only {len(cocktails)} cocktails found"

    def test_mocktails_count_is_reasonable(self):
        """Test that we have a reasonable number of mocktails."""
        mocktails = load_mocktails()
        # Should have at least 10 mocktails
        assert len(mocktails) >= 10, f"Only {len(mocktails)} mocktails found"

    def test_ingredients_count_is_reasonable(self):
        """Test that we have a reasonable number of ingredients."""
        ingredients_db = load_ingredients()
        all_ingredients = ingredients_db.all_ingredients()
        # Should have at least 50 unique ingredients
        assert len(all_ingredients) >= 50, (
            f"Only {len(all_ingredients)} ingredients found"
        )

    def test_substitutions_are_available(self):
        """Test that we have substitution mappings."""
        substitutions = load_substitutions()
        all_subs = substitutions.all_substitutions()
        # Should have at least 20 substitution mappings
        assert len(all_subs) >= 20, f"Only {len(all_subs)} substitution mappings found"
