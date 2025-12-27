"""Pydantic models for recommendation responses.

These models combine the selected recipe with alternatives
and bottle purchase recommendations.
"""

from pydantic import BaseModel, Field

from src.app.models.cocktail import CocktailMatch
from src.app.models.recipe import Recipe


class BottleRec(BaseModel):
    """Recommendation for the next bottle to purchase.

    Based on which ingredients unlock the most new drink
    possibilities given the user's current cabinet.
    """

    ingredient: str = Field(
        ...,
        description="Ingredient ID to purchase",
    )
    unlocks: int = Field(
        ...,
        ge=0,
        description="Number of new drinks this ingredient unlocks",
    )
    drinks: list[str] = Field(
        default_factory=list,
        description="Names of drinks this ingredient would unlock",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient": "campari",
                "unlocks": 5,
                "drinks": [
                    "Negroni",
                    "Boulevardier",
                    "Americano",
                    "Jungle Bird",
                    "Old Pal",
                ],
            }
        }


class Recommendation(BaseModel):
    """Complete recommendation response from the API.

    Contains the selected recipe, alternatives the user can
    ask for instead, and a suggestion for expanding their bar.
    """

    recipe: Recipe = Field(..., description="The recommended recipe")
    alternatives: list[CocktailMatch] = Field(
        default_factory=list,
        description="Other drinks that also match well",
    )
    next_bottle: BottleRec | None = Field(
        default=None,
        description="Suggested next bottle purchase (if applicable)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recipe": {
                    "id": "whiskey-sour",
                    "name": "Whiskey Sour",
                    "tagline": "The perfect balance of booze and citrus",
                    "why": "This classic is great for a relaxed evening...",
                    "flavor_profile": {
                        "sweet": 40,
                        "sour": 50,
                        "bitter": 10,
                        "spirit": 60,
                    },
                    "ingredients": [
                        {"amount": "2", "unit": "oz", "item": "bourbon"},
                        {"amount": "0.75", "unit": "oz", "item": "fresh lemon juice"},
                        {"amount": "0.75", "unit": "oz", "item": "simple syrup"},
                    ],
                    "method": [
                        {"action": "Shake", "detail": "all ingredients with ice"},
                        {"action": "Strain", "detail": "into a rocks glass with ice"},
                    ],
                    "glassware": "rocks",
                    "garnish": "lemon wheel, cherry",
                    "timing": "3 minutes",
                    "difficulty": "easy",
                    "technique_tips": [],
                    "is_mocktail": False,
                },
                "alternatives": [
                    {
                        "id": "old-fashioned",
                        "name": "Old Fashioned",
                        "score": 0.92,
                        "missing": [],
                        "is_mocktail": False,
                    }
                ],
                "next_bottle": {
                    "ingredient": "sweet-vermouth",
                    "unlocks": 4,
                    "drinks": ["Manhattan", "Negroni", "Rob Roy", "Boulevardier"],
                },
            }
        }
