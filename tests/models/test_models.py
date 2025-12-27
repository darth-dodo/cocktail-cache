"""Comprehensive unit tests for Pydantic models in src/app/models/.

This module tests all core Pydantic models including:
- Cabinet: User's home bar ingredient management
- UserPreferences: Skill level, drink type, and exclusion settings
- Recipe: Complete recipe with ingredients, steps, and technique tips
- Recommendation: Bottle recommendations and unlock tracking
- History: Recipe history tracking and queries
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.app.models.cabinet import Cabinet
from src.app.models.cocktail import CocktailMatch
from src.app.models.drinks import FlavorProfile
from src.app.models.history import HistoryEntry, RecipeHistory
from src.app.models.recipe import Recipe, RecipeIngredient, RecipeStep, TechniqueTip
from src.app.models.recommendation import BottleRec, Recommendation
from src.app.models.user_prefs import DrinkType, SkillLevel, UserPreferences

# =============================================================================
# Cabinet Model Tests
# =============================================================================


class TestCabinet:
    """Test suite for the Cabinet model."""

    def test_cabinet_creation_empty(self):
        """Test creating a cabinet with no ingredients."""
        cabinet = Cabinet()
        assert cabinet.ingredients == []
        assert len(cabinet) == 0

    def test_cabinet_creation_with_ingredients(self):
        """Test creating a cabinet with a list of ingredients."""
        ingredients = ["bourbon", "sweet-vermouth", "angostura-bitters"]
        cabinet = Cabinet(ingredients=ingredients)
        assert cabinet.ingredients == ingredients
        assert len(cabinet) == 3

    def test_cabinet_has_ingredient_present(self):
        """Test has_ingredient returns True for present ingredient."""
        cabinet = Cabinet(ingredients=["bourbon", "gin", "vodka"])
        assert cabinet.has_ingredient("bourbon") is True
        assert cabinet.has_ingredient("gin") is True

    def test_cabinet_has_ingredient_absent(self):
        """Test has_ingredient returns False for absent ingredient."""
        cabinet = Cabinet(ingredients=["bourbon", "gin"])
        assert cabinet.has_ingredient("tequila") is False
        assert cabinet.has_ingredient("rum") is False

    def test_cabinet_has_ingredient_empty_cabinet(self):
        """Test has_ingredient on empty cabinet."""
        cabinet = Cabinet()
        assert cabinet.has_ingredient("bourbon") is False

    def test_cabinet_has_ingredient_case_sensitive(self):
        """Test has_ingredient is case-sensitive (uses exact ingredient IDs)."""
        cabinet = Cabinet(ingredients=["bourbon"])
        # Ingredient IDs are expected to be lowercase kebab-case
        assert cabinet.has_ingredient("bourbon") is True
        assert cabinet.has_ingredient("Bourbon") is False
        assert cabinet.has_ingredient("BOURBON") is False

    def test_cabinet_has_all_full_match(self):
        """Test has_all returns True when all ingredients present."""
        cabinet = Cabinet(
            ingredients=["bourbon", "sweet-vermouth", "angostura-bitters"]
        )
        assert cabinet.has_all(["bourbon", "sweet-vermouth"]) is True
        assert cabinet.has_all(["bourbon"]) is True
        assert cabinet.has_all([]) is True

    def test_cabinet_has_all_partial_match(self):
        """Test has_all returns False when some ingredients missing."""
        cabinet = Cabinet(ingredients=["bourbon", "gin"])
        assert cabinet.has_all(["bourbon", "tequila"]) is False
        assert cabinet.has_all(["vodka", "rum"]) is False

    def test_cabinet_has_all_no_match(self):
        """Test has_all returns False when no ingredients match."""
        cabinet = Cabinet(ingredients=["bourbon", "gin"])
        assert cabinet.has_all(["tequila", "rum"]) is False

    def test_cabinet_has_all_empty_cabinet(self):
        """Test has_all on empty cabinet."""
        cabinet = Cabinet()
        assert cabinet.has_all([]) is True
        assert cabinet.has_all(["bourbon"]) is False

    def test_cabinet_missing_returns_missing_ingredients(self):
        """Test missing returns list of ingredients not in cabinet."""
        cabinet = Cabinet(ingredients=["bourbon", "sweet-vermouth"])
        missing = cabinet.missing(["bourbon", "angostura-bitters", "cherry"])
        assert missing == ["angostura-bitters", "cherry"]

    def test_cabinet_missing_all_present(self):
        """Test missing returns empty list when all ingredients present."""
        cabinet = Cabinet(ingredients=["bourbon", "gin", "vodka"])
        missing = cabinet.missing(["bourbon", "gin"])
        assert missing == []

    def test_cabinet_missing_empty_input(self):
        """Test missing with empty ingredient list."""
        cabinet = Cabinet(ingredients=["bourbon"])
        missing = cabinet.missing([])
        assert missing == []

    def test_cabinet_missing_empty_cabinet(self):
        """Test missing on empty cabinet returns all ingredients."""
        cabinet = Cabinet()
        missing = cabinet.missing(["bourbon", "gin"])
        assert missing == ["bourbon", "gin"]

    def test_cabinet_len(self):
        """Test __len__ returns correct count."""
        assert len(Cabinet()) == 0
        assert len(Cabinet(ingredients=["bourbon"])) == 1
        assert len(Cabinet(ingredients=["bourbon", "gin", "vodka"])) == 3

    def test_cabinet_json_serialization(self):
        """Test cabinet can be serialized to JSON."""
        cabinet = Cabinet(ingredients=["bourbon", "gin"])
        json_data = cabinet.model_dump()
        assert json_data == {"ingredients": ["bourbon", "gin"]}

    def test_cabinet_duplicate_ingredients(self):
        """Test cabinet allows duplicate ingredients (no deduplication)."""
        # Note: The model does not enforce uniqueness
        cabinet = Cabinet(ingredients=["bourbon", "bourbon", "gin"])
        assert len(cabinet) == 3
        assert cabinet.ingredients.count("bourbon") == 2


# =============================================================================
# UserPreferences Model Tests
# =============================================================================


class TestUserPreferences:
    """Test suite for the UserPreferences model."""

    def test_user_preferences_defaults(self):
        """Test default values for UserPreferences."""
        prefs = UserPreferences()
        assert prefs.skill_level == SkillLevel.INTERMEDIATE
        assert prefs.drink_type == DrinkType.COCKTAIL
        assert prefs.exclude_count == 5

    def test_user_preferences_custom_values(self):
        """Test UserPreferences with custom values."""
        prefs = UserPreferences(
            skill_level=SkillLevel.BEGINNER,
            drink_type=DrinkType.MOCKTAIL,
            exclude_count=10,
        )
        assert prefs.skill_level == SkillLevel.BEGINNER
        assert prefs.drink_type == DrinkType.MOCKTAIL
        assert prefs.exclude_count == 10

    def test_skill_level_enum_values(self):
        """Test all SkillLevel enum values."""
        assert SkillLevel.BEGINNER.value == "beginner"
        assert SkillLevel.INTERMEDIATE.value == "intermediate"
        assert SkillLevel.ADVENTUROUS.value == "adventurous"

    def test_skill_level_enum_from_string(self):
        """Test SkillLevel enum can be created from string."""
        prefs = UserPreferences(skill_level="beginner")
        assert prefs.skill_level == SkillLevel.BEGINNER
        prefs = UserPreferences(skill_level="adventurous")
        assert prefs.skill_level == SkillLevel.ADVENTUROUS

    def test_skill_level_invalid_value(self):
        """Test invalid SkillLevel raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferences(skill_level="expert")
        assert "skill_level" in str(exc_info.value)

    def test_drink_type_enum_values(self):
        """Test all DrinkType enum values."""
        assert DrinkType.COCKTAIL.value == "cocktail"
        assert DrinkType.MOCKTAIL.value == "mocktail"
        assert DrinkType.BOTH.value == "both"

    def test_drink_type_enum_from_string(self):
        """Test DrinkType enum can be created from string."""
        prefs = UserPreferences(drink_type="mocktail")
        assert prefs.drink_type == DrinkType.MOCKTAIL
        prefs = UserPreferences(drink_type="both")
        assert prefs.drink_type == DrinkType.BOTH

    def test_drink_type_invalid_value(self):
        """Test invalid DrinkType raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferences(drink_type="beer")
        assert "drink_type" in str(exc_info.value)

    def test_exclude_count_minimum(self):
        """Test exclude_count minimum value (0)."""
        prefs = UserPreferences(exclude_count=0)
        assert prefs.exclude_count == 0

    def test_exclude_count_maximum(self):
        """Test exclude_count maximum value (20)."""
        prefs = UserPreferences(exclude_count=20)
        assert prefs.exclude_count == 20

    def test_exclude_count_below_minimum(self):
        """Test exclude_count below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferences(exclude_count=-1)
        assert "exclude_count" in str(exc_info.value)

    def test_exclude_count_above_maximum(self):
        """Test exclude_count above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserPreferences(exclude_count=21)
        assert "exclude_count" in str(exc_info.value)

    def test_allows_cocktails_cocktail_type(self):
        """Test allows_cocktails returns True for COCKTAIL type."""
        prefs = UserPreferences(drink_type=DrinkType.COCKTAIL)
        assert prefs.allows_cocktails() is True

    def test_allows_cocktails_both_type(self):
        """Test allows_cocktails returns True for BOTH type."""
        prefs = UserPreferences(drink_type=DrinkType.BOTH)
        assert prefs.allows_cocktails() is True

    def test_allows_cocktails_mocktail_type(self):
        """Test allows_cocktails returns False for MOCKTAIL type."""
        prefs = UserPreferences(drink_type=DrinkType.MOCKTAIL)
        assert prefs.allows_cocktails() is False

    def test_allows_mocktails_mocktail_type(self):
        """Test allows_mocktails returns True for MOCKTAIL type."""
        prefs = UserPreferences(drink_type=DrinkType.MOCKTAIL)
        assert prefs.allows_mocktails() is True

    def test_allows_mocktails_both_type(self):
        """Test allows_mocktails returns True for BOTH type."""
        prefs = UserPreferences(drink_type=DrinkType.BOTH)
        assert prefs.allows_mocktails() is True

    def test_allows_mocktails_cocktail_type(self):
        """Test allows_mocktails returns False for COCKTAIL type."""
        prefs = UserPreferences(drink_type=DrinkType.COCKTAIL)
        assert prefs.allows_mocktails() is False

    def test_user_preferences_json_serialization(self):
        """Test UserPreferences can be serialized to JSON."""
        prefs = UserPreferences(
            skill_level=SkillLevel.BEGINNER,
            drink_type=DrinkType.BOTH,
            exclude_count=3,
        )
        json_data = prefs.model_dump()
        assert json_data["skill_level"] == "beginner"
        assert json_data["drink_type"] == "both"
        assert json_data["exclude_count"] == 3


# =============================================================================
# Recipe Model Tests
# =============================================================================


class TestRecipeIngredient:
    """Test suite for the RecipeIngredient model."""

    def test_recipe_ingredient_creation(self):
        """Test creating a RecipeIngredient."""
        ingredient = RecipeIngredient(amount="2", unit="oz", item="bourbon")
        assert ingredient.amount == "2"
        assert ingredient.unit == "oz"
        assert ingredient.item == "bourbon"

    def test_recipe_ingredient_fractional_amount(self):
        """Test RecipeIngredient with fractional amount."""
        ingredient = RecipeIngredient(amount="0.75", unit="oz", item="simple syrup")
        assert ingredient.amount == "0.75"

    def test_recipe_ingredient_range_amount(self):
        """Test RecipeIngredient with range amount."""
        ingredient = RecipeIngredient(amount="2-3", unit="dashes", item="bitters")
        assert ingredient.amount == "2-3"

    def test_recipe_ingredient_various_units(self):
        """Test RecipeIngredient with various units."""
        units = ["oz", "dash", "leaves", "tsp", "splash", "ml"]
        for unit in units:
            ingredient = RecipeIngredient(amount="1", unit=unit, item="test")
            assert ingredient.unit == unit

    def test_recipe_ingredient_missing_required_field(self):
        """Test RecipeIngredient requires all fields."""
        with pytest.raises(ValidationError):
            RecipeIngredient(amount="2", unit="oz")  # missing item


class TestRecipeStep:
    """Test suite for the RecipeStep model."""

    def test_recipe_step_creation(self):
        """Test creating a RecipeStep."""
        step = RecipeStep(action="Shake", detail="all ingredients with ice")
        assert step.action == "Shake"
        assert step.detail == "all ingredients with ice"

    def test_recipe_step_various_actions(self):
        """Test RecipeStep with various action verbs."""
        actions = ["Shake", "Stir", "Muddle", "Strain", "Pour", "Add", "Express"]
        for action in actions:
            step = RecipeStep(action=action, detail="test detail")
            assert step.action == action

    def test_recipe_step_missing_required_field(self):
        """Test RecipeStep requires all fields."""
        with pytest.raises(ValidationError):
            RecipeStep(action="Shake")  # missing detail


class TestTechniqueTip:
    """Test suite for the TechniqueTip model."""

    def test_technique_tip_beginner(self):
        """Test TechniqueTip for beginner skill level."""
        tip = TechniqueTip(
            skill_level="beginner",
            tip="Use a large ice cube to slow dilution",
        )
        assert tip.skill_level == "beginner"
        assert "ice cube" in tip.tip

    def test_technique_tip_intermediate(self):
        """Test TechniqueTip for intermediate skill level."""
        tip = TechniqueTip(
            skill_level="intermediate",
            tip="Try adjusting the ratio to your taste",
        )
        assert tip.skill_level == "intermediate"

    def test_technique_tip_adventurous(self):
        """Test TechniqueTip for adventurous skill level."""
        tip = TechniqueTip(
            skill_level="adventurous",
            tip="Experiment with different bitters combinations",
        )
        assert tip.skill_level == "adventurous"

    def test_technique_tip_invalid_skill_level(self):
        """Test TechniqueTip with invalid skill level raises error."""
        with pytest.raises(ValidationError) as exc_info:
            TechniqueTip(skill_level="expert", tip="Some tip")
        assert "skill_level" in str(exc_info.value)

    def test_technique_tip_missing_required_field(self):
        """Test TechniqueTip requires all fields."""
        with pytest.raises(ValidationError):
            TechniqueTip(skill_level="beginner")  # missing tip


class TestRecipe:
    """Test suite for the Recipe model."""

    @pytest.fixture
    def sample_flavor_profile(self):
        """Provide a sample FlavorProfile."""
        return FlavorProfile(sweet=25, sour=0, bitter=30, spirit=80)

    @pytest.fixture
    def sample_ingredients(self):
        """Provide sample recipe ingredients."""
        return [
            RecipeIngredient(amount="2", unit="oz", item="bourbon"),
            RecipeIngredient(amount="1", unit="tsp", item="simple syrup"),
            RecipeIngredient(amount="2", unit="dashes", item="Angostura bitters"),
        ]

    @pytest.fixture
    def sample_method(self):
        """Provide sample method steps."""
        return [
            RecipeStep(action="Add", detail="bitters and syrup to a rocks glass"),
            RecipeStep(action="Stir", detail="briefly to combine"),
            RecipeStep(action="Add", detail="a large ice cube and bourbon"),
        ]

    def test_recipe_creation_full(
        self, sample_flavor_profile, sample_ingredients, sample_method
    ):
        """Test creating a complete Recipe."""
        recipe = Recipe(
            id="old-fashioned",
            name="Old Fashioned",
            tagline="The original cocktail, simple and timeless",
            why="A perfect choice for a contemplative evening",
            flavor_profile=sample_flavor_profile,
            ingredients=sample_ingredients,
            method=sample_method,
            glassware="rocks",
            garnish="orange peel, expressed",
            timing="3 minutes",
            difficulty="easy",
        )
        assert recipe.id == "old-fashioned"
        assert recipe.name == "Old Fashioned"
        assert recipe.is_mocktail is False
        assert len(recipe.ingredients) == 3
        assert len(recipe.method) == 3
        assert recipe.technique_tips == []

    def test_recipe_with_technique_tips(
        self, sample_flavor_profile, sample_ingredients, sample_method
    ):
        """Test Recipe with technique tips."""
        tips = [
            TechniqueTip(skill_level="beginner", tip="Use a large ice cube"),
            TechniqueTip(skill_level="adventurous", tip="Try with rye whiskey"),
        ]
        recipe = Recipe(
            id="old-fashioned",
            name="Old Fashioned",
            tagline="The original cocktail",
            why="Classic choice",
            flavor_profile=sample_flavor_profile,
            ingredients=sample_ingredients,
            method=sample_method,
            glassware="rocks",
            garnish="orange peel",
            timing="3 minutes",
            difficulty="easy",
            technique_tips=tips,
        )
        assert len(recipe.technique_tips) == 2
        assert recipe.technique_tips[0].skill_level == "beginner"

    def test_recipe_mocktail(
        self, sample_flavor_profile, sample_ingredients, sample_method
    ):
        """Test Recipe as mocktail."""
        recipe = Recipe(
            id="virgin-mojito",
            name="Virgin Mojito",
            tagline="Refreshing without the rum",
            why="Perfect for a hot day",
            flavor_profile=FlavorProfile(sweet=40, sour=30, bitter=0, spirit=0),
            ingredients=sample_ingredients,
            method=sample_method,
            glassware="highball",
            garnish="mint sprig",
            timing="5 minutes",
            difficulty="easy",
            is_mocktail=True,
        )
        assert recipe.is_mocktail is True

    def test_recipe_difficulty_validation(
        self, sample_flavor_profile, sample_ingredients, sample_method
    ):
        """Test Recipe difficulty field validation."""
        valid_difficulties = ["easy", "medium", "hard", "advanced"]
        for difficulty in valid_difficulties:
            recipe = Recipe(
                id="test",
                name="Test",
                tagline="Test",
                why="Test",
                flavor_profile=sample_flavor_profile,
                ingredients=sample_ingredients,
                method=sample_method,
                glassware="rocks",
                garnish="none",
                timing="1 minute",
                difficulty=difficulty,
            )
            assert recipe.difficulty == difficulty

    def test_recipe_invalid_difficulty(
        self, sample_flavor_profile, sample_ingredients, sample_method
    ):
        """Test Recipe with invalid difficulty raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Recipe(
                id="test",
                name="Test",
                tagline="Test",
                why="Test",
                flavor_profile=sample_flavor_profile,
                ingredients=sample_ingredients,
                method=sample_method,
                glassware="rocks",
                garnish="none",
                timing="1 minute",
                difficulty="impossible",
            )
        assert "difficulty" in str(exc_info.value)

    def test_recipe_requires_minimum_ingredients(self, sample_flavor_profile):
        """Test Recipe requires at least one ingredient."""
        with pytest.raises(ValidationError) as exc_info:
            Recipe(
                id="test",
                name="Test",
                tagline="Test",
                why="Test",
                flavor_profile=sample_flavor_profile,
                ingredients=[],
                method=[RecipeStep(action="Test", detail="test")],
                glassware="rocks",
                garnish="none",
                timing="1 minute",
                difficulty="easy",
            )
        assert "ingredients" in str(exc_info.value)

    def test_recipe_requires_minimum_method_steps(
        self, sample_flavor_profile, sample_ingredients
    ):
        """Test Recipe requires at least one method step."""
        with pytest.raises(ValidationError) as exc_info:
            Recipe(
                id="test",
                name="Test",
                tagline="Test",
                why="Test",
                flavor_profile=sample_flavor_profile,
                ingredients=sample_ingredients,
                method=[],
                glassware="rocks",
                garnish="none",
                timing="1 minute",
                difficulty="easy",
            )
        assert "method" in str(exc_info.value)


# =============================================================================
# FlavorProfile Model Tests
# =============================================================================


class TestFlavorProfile:
    """Test suite for the FlavorProfile model."""

    def test_flavor_profile_creation(self):
        """Test creating a FlavorProfile."""
        profile = FlavorProfile(sweet=25, sour=0, bitter=30, spirit=80)
        assert profile.sweet == 25
        assert profile.sour == 0
        assert profile.bitter == 30
        assert profile.spirit == 80

    def test_flavor_profile_minimum_values(self):
        """Test FlavorProfile with all zeros."""
        profile = FlavorProfile(sweet=0, sour=0, bitter=0, spirit=0)
        assert profile.sweet == 0
        assert profile.spirit == 0

    def test_flavor_profile_maximum_values(self):
        """Test FlavorProfile with all maximums."""
        profile = FlavorProfile(sweet=100, sour=100, bitter=100, spirit=100)
        assert profile.sweet == 100
        assert profile.spirit == 100

    def test_flavor_profile_below_minimum(self):
        """Test FlavorProfile with value below minimum raises error."""
        with pytest.raises(ValidationError):
            FlavorProfile(sweet=-1, sour=0, bitter=0, spirit=0)

    def test_flavor_profile_above_maximum(self):
        """Test FlavorProfile with value above maximum raises error."""
        with pytest.raises(ValidationError):
            FlavorProfile(sweet=0, sour=101, bitter=0, spirit=0)


# =============================================================================
# Recommendation Model Tests
# =============================================================================


class TestBottleRec:
    """Test suite for the BottleRec model."""

    def test_bottle_rec_creation(self):
        """Test creating a BottleRec."""
        rec = BottleRec(
            ingredient="campari",
            unlocks=5,
            drinks=["Negroni", "Boulevardier", "Americano"],
        )
        assert rec.ingredient == "campari"
        assert rec.unlocks == 5
        assert len(rec.drinks) == 3

    def test_bottle_rec_zero_unlocks(self):
        """Test BottleRec with zero unlocks."""
        rec = BottleRec(ingredient="obscure-liqueur", unlocks=0, drinks=[])
        assert rec.unlocks == 0
        assert rec.drinks == []

    def test_bottle_rec_default_drinks(self):
        """Test BottleRec with default empty drinks list."""
        rec = BottleRec(ingredient="campari", unlocks=3)
        assert rec.drinks == []

    def test_bottle_rec_negative_unlocks(self):
        """Test BottleRec with negative unlocks raises error."""
        with pytest.raises(ValidationError) as exc_info:
            BottleRec(ingredient="test", unlocks=-1)
        assert "unlocks" in str(exc_info.value)

    def test_bottle_rec_json_serialization(self):
        """Test BottleRec can be serialized to JSON."""
        rec = BottleRec(
            ingredient="campari",
            unlocks=5,
            drinks=["Negroni", "Americano"],
        )
        json_data = rec.model_dump()
        assert json_data["ingredient"] == "campari"
        assert json_data["unlocks"] == 5
        assert json_data["drinks"] == ["Negroni", "Americano"]


class TestCocktailMatch:
    """Test suite for the CocktailMatch model."""

    def test_cocktail_match_perfect(self):
        """Test CocktailMatch with perfect score and no missing."""
        match = CocktailMatch(
            id="old-fashioned",
            name="Old Fashioned",
            score=1.0,
            missing=[],
        )
        assert match.id == "old-fashioned"
        assert match.score == 1.0
        assert match.is_perfect_match is True
        assert match.is_mocktail is False

    def test_cocktail_match_partial(self):
        """Test CocktailMatch with partial score and missing ingredients."""
        match = CocktailMatch(
            id="negroni",
            name="Negroni",
            score=0.67,
            missing=["campari"],
        )
        assert match.score == 0.67
        assert match.is_perfect_match is False
        assert match.missing == ["campari"]

    def test_cocktail_match_mocktail(self):
        """Test CocktailMatch for mocktail."""
        match = CocktailMatch(
            id="virgin-mojito",
            name="Virgin Mojito",
            score=0.9,
            is_mocktail=True,
        )
        assert match.is_mocktail is True

    def test_cocktail_match_score_bounds(self):
        """Test CocktailMatch score is bounded 0.0-1.0."""
        # Valid at boundaries
        CocktailMatch(id="test", name="Test", score=0.0)
        CocktailMatch(id="test", name="Test", score=1.0)

        # Invalid below minimum
        with pytest.raises(ValidationError):
            CocktailMatch(id="test", name="Test", score=-0.1)

        # Invalid above maximum
        with pytest.raises(ValidationError):
            CocktailMatch(id="test", name="Test", score=1.1)


class TestRecommendation:
    """Test suite for the Recommendation model."""

    @pytest.fixture
    def sample_recipe(self):
        """Provide a sample Recipe for testing."""
        return Recipe(
            id="whiskey-sour",
            name="Whiskey Sour",
            tagline="The perfect balance of booze and citrus",
            why="This classic is great for a relaxed evening",
            flavor_profile=FlavorProfile(sweet=40, sour=50, bitter=10, spirit=60),
            ingredients=[
                RecipeIngredient(amount="2", unit="oz", item="bourbon"),
                RecipeIngredient(amount="0.75", unit="oz", item="fresh lemon juice"),
                RecipeIngredient(amount="0.75", unit="oz", item="simple syrup"),
            ],
            method=[
                RecipeStep(action="Shake", detail="all ingredients with ice"),
                RecipeStep(action="Strain", detail="into a rocks glass with ice"),
            ],
            glassware="rocks",
            garnish="lemon wheel, cherry",
            timing="3 minutes",
            difficulty="easy",
        )

    def test_recommendation_minimal(self, sample_recipe):
        """Test Recommendation with minimal data."""
        rec = Recommendation(recipe=sample_recipe)
        assert rec.recipe.id == "whiskey-sour"
        assert rec.alternatives == []
        assert rec.next_bottle is None

    def test_recommendation_with_alternatives(self, sample_recipe):
        """Test Recommendation with alternatives."""
        alternatives = [
            CocktailMatch(id="old-fashioned", name="Old Fashioned", score=0.92),
            CocktailMatch(
                id="manhattan", name="Manhattan", score=0.85, missing=["sweet-vermouth"]
            ),
        ]
        rec = Recommendation(recipe=sample_recipe, alternatives=alternatives)
        assert len(rec.alternatives) == 2
        assert rec.alternatives[0].id == "old-fashioned"

    def test_recommendation_with_next_bottle(self, sample_recipe):
        """Test Recommendation with next bottle suggestion."""
        bottle = BottleRec(
            ingredient="sweet-vermouth",
            unlocks=4,
            drinks=["Manhattan", "Negroni"],
        )
        rec = Recommendation(recipe=sample_recipe, next_bottle=bottle)
        assert rec.next_bottle is not None
        assert rec.next_bottle.ingredient == "sweet-vermouth"

    def test_recommendation_full(self, sample_recipe):
        """Test Recommendation with all fields populated."""
        alternatives = [
            CocktailMatch(id="old-fashioned", name="Old Fashioned", score=0.92),
        ]
        bottle = BottleRec(ingredient="campari", unlocks=5, drinks=["Negroni"])
        rec = Recommendation(
            recipe=sample_recipe,
            alternatives=alternatives,
            next_bottle=bottle,
        )
        assert rec.recipe.id == "whiskey-sour"
        assert len(rec.alternatives) == 1
        assert rec.next_bottle.unlocks == 5


# =============================================================================
# History Model Tests
# =============================================================================


class TestHistoryEntry:
    """Test suite for the HistoryEntry model."""

    def test_history_entry_creation(self):
        """Test creating a HistoryEntry."""
        entry = HistoryEntry(
            recipe_id="whiskey-sour",
            recipe_name="Whiskey Sour",
        )
        assert entry.recipe_id == "whiskey-sour"
        assert entry.recipe_name == "Whiskey Sour"
        assert entry.is_mocktail is False
        # made_at should be set to now by default
        assert isinstance(entry.made_at, datetime)

    def test_history_entry_custom_datetime(self):
        """Test HistoryEntry with custom datetime."""
        custom_time = datetime(2025, 1, 15, 19, 30, 0)
        entry = HistoryEntry(
            recipe_id="margarita",
            recipe_name="Margarita",
            made_at=custom_time,
        )
        assert entry.made_at == custom_time

    def test_history_entry_mocktail(self):
        """Test HistoryEntry for mocktail."""
        entry = HistoryEntry(
            recipe_id="virgin-mojito",
            recipe_name="Virgin Mojito",
            is_mocktail=True,
        )
        assert entry.is_mocktail is True

    def test_history_entry_json_serialization(self):
        """Test HistoryEntry can be serialized to JSON."""
        entry = HistoryEntry(
            recipe_id="old-fashioned",
            recipe_name="Old Fashioned",
            made_at=datetime(2025, 1, 15, 20, 0, 0),
            is_mocktail=False,
        )
        json_data = entry.model_dump()
        assert json_data["recipe_id"] == "old-fashioned"
        assert json_data["recipe_name"] == "Old Fashioned"


class TestRecipeHistory:
    """Test suite for the RecipeHistory model."""

    def test_recipe_history_empty(self):
        """Test RecipeHistory with no entries."""
        history = RecipeHistory()
        assert history.entries == []
        assert len(history) == 0

    def test_recipe_history_with_entries(self):
        """Test RecipeHistory with populated entries."""
        entries = [
            HistoryEntry(recipe_id="margarita", recipe_name="Margarita"),
            HistoryEntry(recipe_id="whiskey-sour", recipe_name="Whiskey Sour"),
        ]
        history = RecipeHistory(entries=entries)
        assert len(history) == 2

    def test_recipe_history_add(self):
        """Test adding entries to RecipeHistory."""
        history = RecipeHistory()
        history.add("margarita", "Margarita")
        assert len(history) == 1
        assert history.entries[0].recipe_id == "margarita"

    def test_recipe_history_add_prepends(self):
        """Test add prepends to beginning of list."""
        history = RecipeHistory()
        history.add("first", "First Drink")
        history.add("second", "Second Drink")
        # Most recent should be first
        assert history.entries[0].recipe_id == "second"
        assert history.entries[1].recipe_id == "first"

    def test_recipe_history_add_mocktail(self):
        """Test adding mocktail to history."""
        history = RecipeHistory()
        history.add("virgin-mojito", "Virgin Mojito", is_mocktail=True)
        assert history.entries[0].is_mocktail is True

    def test_recipe_history_recent_ids(self):
        """Test recent_ids returns correct IDs."""
        history = RecipeHistory()
        history.add("drink1", "Drink 1")
        history.add("drink2", "Drink 2")
        history.add("drink3", "Drink 3")

        recent = history.recent_ids(count=2)
        assert recent == ["drink3", "drink2"]

    def test_recipe_history_recent_ids_default_count(self):
        """Test recent_ids with default count of 5."""
        history = RecipeHistory()
        for i in range(10):
            history.add(f"drink{i}", f"Drink {i}")

        recent = history.recent_ids()
        assert len(recent) == 5
        assert recent[0] == "drink9"

    def test_recipe_history_recent_ids_fewer_entries(self):
        """Test recent_ids when history has fewer entries than count."""
        history = RecipeHistory()
        history.add("drink1", "Drink 1")
        history.add("drink2", "Drink 2")

        recent = history.recent_ids(count=5)
        assert len(recent) == 2

    def test_recipe_history_contains_present(self):
        """Test contains returns True for present recipe."""
        history = RecipeHistory()
        history.add("margarita", "Margarita")
        history.add("whiskey-sour", "Whiskey Sour")

        assert history.contains("margarita") is True
        assert history.contains("whiskey-sour") is True

    def test_recipe_history_contains_absent(self):
        """Test contains returns False for absent recipe."""
        history = RecipeHistory()
        history.add("margarita", "Margarita")

        assert history.contains("old-fashioned") is False

    def test_recipe_history_contains_empty(self):
        """Test contains on empty history."""
        history = RecipeHistory()
        assert history.contains("any-drink") is False

    def test_recipe_history_count_by_type(self):
        """Test count_by_type returns correct counts."""
        history = RecipeHistory()
        history.add("cocktail1", "Cocktail 1", is_mocktail=False)
        history.add("cocktail2", "Cocktail 2", is_mocktail=False)
        history.add("mocktail1", "Mocktail 1", is_mocktail=True)

        counts = history.count_by_type()
        assert counts["cocktails"] == 2
        assert counts["mocktails"] == 1

    def test_recipe_history_count_by_type_empty(self):
        """Test count_by_type on empty history."""
        history = RecipeHistory()
        counts = history.count_by_type()
        assert counts["cocktails"] == 0
        assert counts["mocktails"] == 0

    def test_recipe_history_count_by_type_all_cocktails(self):
        """Test count_by_type with all cocktails."""
        history = RecipeHistory()
        for i in range(5):
            history.add(f"cocktail{i}", f"Cocktail {i}")

        counts = history.count_by_type()
        assert counts["cocktails"] == 5
        assert counts["mocktails"] == 0

    def test_recipe_history_count_by_type_all_mocktails(self):
        """Test count_by_type with all mocktails."""
        history = RecipeHistory()
        for i in range(3):
            history.add(f"mocktail{i}", f"Mocktail {i}", is_mocktail=True)

        counts = history.count_by_type()
        assert counts["cocktails"] == 0
        assert counts["mocktails"] == 3

    def test_recipe_history_len(self):
        """Test __len__ returns correct count."""
        history = RecipeHistory()
        assert len(history) == 0

        history.add("drink1", "Drink 1")
        assert len(history) == 1

        history.add("drink2", "Drink 2")
        history.add("drink3", "Drink 3")
        assert len(history) == 3

    def test_recipe_history_json_serialization(self):
        """Test RecipeHistory can be serialized to JSON."""
        history = RecipeHistory()
        history.add("margarita", "Margarita")

        json_data = history.model_dump()
        assert "entries" in json_data
        assert len(json_data["entries"]) == 1
        assert json_data["entries"][0]["recipe_id"] == "margarita"


# =============================================================================
# Integration Tests - Cross-Model Interactions
# =============================================================================


class TestModelIntegration:
    """Test suite for cross-model interactions."""

    def test_cabinet_to_cocktail_match_workflow(self):
        """Test workflow from Cabinet to CocktailMatch scoring."""
        cabinet = Cabinet(ingredients=["bourbon", "simple-syrup", "angostura-bitters"])
        recipe_ingredients = [
            "bourbon",
            "simple-syrup",
            "angostura-bitters",
            "orange-peel",
        ]

        missing = cabinet.missing(recipe_ingredients)
        has_all = cabinet.has_all(recipe_ingredients)

        # Calculate a simple score based on missing ingredients
        score = 1.0 - (len(missing) / len(recipe_ingredients))

        match = CocktailMatch(
            id="old-fashioned",
            name="Old Fashioned",
            score=score,
            missing=missing,
        )

        assert match.score == 0.75  # 3/4 ingredients available
        assert match.missing == ["orange-peel"]
        assert not has_all

    def test_user_prefs_filter_history(self):
        """Test filtering history based on user preferences."""
        prefs = UserPreferences(drink_type=DrinkType.COCKTAIL)
        history = RecipeHistory()
        history.add("margarita", "Margarita", is_mocktail=False)
        history.add("virgin-mojito", "Virgin Mojito", is_mocktail=True)
        history.add("old-fashioned", "Old Fashioned", is_mocktail=False)

        # Filter based on preferences
        if prefs.allows_cocktails() and not prefs.allows_mocktails():
            cocktails_only = [e for e in history.entries if not e.is_mocktail]
            assert len(cocktails_only) == 2

    def test_recommendation_history_exclusion(self):
        """Test using history to exclude recent drinks from recommendations."""
        history = RecipeHistory()
        # Added first (oldest)
        history.add("margarita", "Margarita")
        # Added second
        history.add("whiskey-sour", "Whiskey Sour")
        # Added last (most recent - prepended to list)
        history.add("old-fashioned", "Old Fashioned")

        prefs = UserPreferences(exclude_count=2)
        recent_ids = history.recent_ids(count=prefs.exclude_count)

        # The two most recently made drinks should be excluded
        # Since add() prepends, order is: [old-fashioned, whiskey-sour, margarita]
        assert "old-fashioned" in recent_ids
        assert "whiskey-sour" in recent_ids
        assert "margarita" not in recent_ids
