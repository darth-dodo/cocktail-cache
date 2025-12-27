"""Pydantic models for cocktail and mocktail drinks.

These models define the schema for drink recipes and are used for:
- JSON data validation
- API request/response schemas
- Type-safe data manipulation
"""

from pydantic import BaseModel, Field


class IngredientAmount(BaseModel):
    """A single ingredient with its amount in a recipe."""

    amount: str = Field(..., description="Quantity as string (e.g., '2', '0.75')")
    unit: str = Field(..., description="Unit of measurement (oz, dash, leaves, etc.)")
    item: str = Field(..., description="Ingredient ID reference")


class MethodStep(BaseModel):
    """A single step in the drink preparation method."""

    action: str = Field(..., description="The action verb (Shake, Stir, Muddle, etc.)")
    detail: str = Field(..., description="Detailed instruction for this step")


class FlavorProfile(BaseModel):
    """Flavor characteristics of a drink on 0-100 scales."""

    sweet: int = Field(ge=0, le=100, description="Sweetness level")
    sour: int = Field(ge=0, le=100, description="Sourness/acidity level")
    bitter: int = Field(ge=0, le=100, description="Bitterness level")
    spirit: int = Field(
        ge=0, le=100, description="Spirit-forward intensity (0 for mocktails)"
    )


class Drink(BaseModel):
    """A cocktail or mocktail recipe."""

    id: str = Field(..., description="Unique drink identifier (kebab-case)")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(..., description="Short catchy description")
    ingredients: list[IngredientAmount] = Field(..., min_length=1)
    method: list[MethodStep] = Field(..., min_length=1)
    glassware: str = Field(..., description="Type of glass to serve in")
    garnish: str = Field(..., description="Garnish description")
    flavor_profile: FlavorProfile
    tags: list[str] = Field(default_factory=list)
    difficulty: str = Field(..., pattern="^(easy|medium|hard|advanced)$")
    timing_minutes: int = Field(ge=1, le=30)
    is_mocktail: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "old-fashioned",
                "name": "Old Fashioned",
                "tagline": "The original cocktail, simple and timeless",
                "ingredients": [
                    {"amount": "2", "unit": "oz", "item": "bourbon"},
                    {"amount": "1", "unit": "tsp", "item": "simple-syrup"},
                    {"amount": "2", "unit": "dashes", "item": "angostura-bitters"},
                ],
                "method": [
                    {"action": "Add", "detail": "bitters and syrup to rocks glass"},
                    {"action": "Stir", "detail": "briefly to combine"},
                    {"action": "Add", "detail": "large ice cube"},
                ],
                "glassware": "rocks",
                "garnish": "orange peel, expressed",
                "flavor_profile": {"sweet": 25, "sour": 0, "bitter": 30, "spirit": 80},
                "tags": ["whiskey", "stirred", "classic"],
                "difficulty": "easy",
                "timing_minutes": 3,
                "is_mocktail": False,
            }
        }
