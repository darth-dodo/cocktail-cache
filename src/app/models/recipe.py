"""Pydantic models for recipe API responses.

These models provide the full recipe detail for rendering
in the UI, including skill-appropriate technique tips.
"""

from pydantic import BaseModel, Field

from src.app.models.drinks import FlavorProfile


class RecipeIngredient(BaseModel):
    """A single ingredient with amount in a recipe."""

    amount: str = Field(..., description="Quantity (e.g., '2', '0.75', '2-3')")
    unit: str = Field(..., description="Unit of measurement (oz, dash, leaves, etc.)")
    item: str = Field(..., description="Ingredient name for display")


class RecipeStep(BaseModel):
    """A single step in the preparation method."""

    action: str = Field(..., description="The action verb (Shake, Stir, Muddle, etc.)")
    detail: str = Field(..., description="Detailed instruction for this step")


class TechniqueTip(BaseModel):
    """A technique tip tailored to skill level."""

    skill_level: str = Field(
        ...,
        pattern="^(beginner|intermediate|adventurous)$",
        description="Skill level this tip is appropriate for",
    )
    tip: str = Field(..., description="The technique tip or advice")


class Recipe(BaseModel):
    """Complete recipe for API response with all details for rendering.

    This model combines drink data with AI-generated content like
    the 'why' explanation and skill-appropriate technique tips.
    """

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(..., description="Short catchy description")
    why: str = Field(
        ...,
        description="AI-generated explanation of why this drink was recommended",
    )
    flavor_profile: FlavorProfile
    ingredients: list[RecipeIngredient] = Field(..., min_length=1)
    method: list[RecipeStep] = Field(..., min_length=1)
    glassware: str = Field(..., description="Type of glass to serve in")
    garnish: str = Field(..., description="Garnish description")
    timing: str = Field(..., description="Preparation time (e.g., '3 minutes')")
    difficulty: str = Field(..., pattern="^(easy|medium|hard|advanced)$")
    technique_tips: list[TechniqueTip] = Field(
        default_factory=list,
        description="Skill-appropriate technique tips",
    )
    is_mocktail: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "old-fashioned",
                "name": "Old Fashioned",
                "tagline": "The original cocktail, simple and timeless",
                "why": "A perfect choice for a contemplative evening - "
                "this classic whiskey cocktail lets the bourbon shine "
                "with just a touch of sweetness and bitters.",
                "flavor_profile": {
                    "sweet": 25,
                    "sour": 0,
                    "bitter": 30,
                    "spirit": 80,
                },
                "ingredients": [
                    {"amount": "2", "unit": "oz", "item": "bourbon"},
                    {"amount": "1", "unit": "tsp", "item": "simple syrup"},
                    {"amount": "2", "unit": "dashes", "item": "Angostura bitters"},
                ],
                "method": [
                    {
                        "action": "Add",
                        "detail": "bitters and syrup to a rocks glass",
                    },
                    {"action": "Stir", "detail": "briefly to combine"},
                    {"action": "Add", "detail": "a large ice cube and bourbon"},
                    {"action": "Stir", "detail": "gently for 20-30 seconds"},
                    {"action": "Express", "detail": "orange peel over the drink"},
                ],
                "glassware": "rocks",
                "garnish": "orange peel, expressed",
                "timing": "3 minutes",
                "difficulty": "easy",
                "technique_tips": [
                    {
                        "skill_level": "beginner",
                        "tip": "Use a large ice cube to slow dilution - "
                        "regular cubes melt too fast",
                    },
                    {
                        "skill_level": "adventurous",
                        "tip": "Try with rye whiskey for a spicier, "
                        "more complex variation",
                    },
                ],
                "is_mocktail": False,
            }
        }
