"""Pydantic models for ingredients and substitutions.

These models define the schema for the ingredient database and
substitution mappings used for recipe flexibility.
"""

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """A single ingredient in the database."""

    id: str = Field(..., description="Unique ingredient identifier (kebab-case)")
    names: list[str] = Field(
        ..., min_length=1, description="List of names/aliases for matching"
    )


class IngredientsDatabase(BaseModel):
    """Complete ingredients database organized by category."""

    spirits: list[Ingredient] = Field(default_factory=list)
    modifiers: list[Ingredient] = Field(default_factory=list)
    bitters_syrups: list[Ingredient] = Field(default_factory=list)
    fresh: list[Ingredient] = Field(default_factory=list)
    mixers: list[Ingredient] = Field(default_factory=list)
    non_alcoholic: list[Ingredient] = Field(default_factory=list)

    def all_ingredients(self) -> list[Ingredient]:
        """Get all ingredients across all categories."""
        return (
            self.spirits
            + self.modifiers
            + self.bitters_syrups
            + self.fresh
            + self.mixers
            + self.non_alcoholic
        )

    def find_by_id(self, ingredient_id: str) -> Ingredient | None:
        """Find an ingredient by its ID."""
        for ing in self.all_ingredients():
            if ing.id == ingredient_id:
                return ing
        return None


# Type alias for substitution mappings (ingredient_id -> list of substitute IDs)
SubstitutionMap = dict[str, list[str]]


class SubstitutionsDatabase(BaseModel):
    """Complete substitutions database organized by category.

    Each category maps original ingredient IDs to lists of substitute IDs.
    """

    spirits: SubstitutionMap = Field(default_factory=dict)
    modifiers: SubstitutionMap = Field(default_factory=dict)
    bitters_syrups: SubstitutionMap = Field(default_factory=dict)
    fresh: SubstitutionMap = Field(default_factory=dict)
    mixers: SubstitutionMap = Field(default_factory=dict)
    non_alcoholic_to_alcoholic: SubstitutionMap = Field(default_factory=dict)
    alcoholic_to_non_alcoholic: SubstitutionMap = Field(default_factory=dict)

    def find_substitutes(self, ingredient_id: str) -> list[str]:
        """Find all substitutes for a given ingredient."""
        # Check each category
        for category in [
            self.spirits,
            self.modifiers,
            self.bitters_syrups,
            self.fresh,
            self.mixers,
            self.non_alcoholic_to_alcoholic,
            self.alcoholic_to_non_alcoholic,
        ]:
            if ingredient_id in category:
                return category[ingredient_id]
        return []

    def all_substitutions(self) -> SubstitutionMap:
        """Get all substitutions as a single dict."""
        result: SubstitutionMap = {}
        for category in [
            self.spirits,
            self.modifiers,
            self.bitters_syrups,
            self.fresh,
            self.mixers,
            self.non_alcoholic_to_alcoholic,
            self.alcoholic_to_non_alcoholic,
        ]:
            result.update(category)
        return result
