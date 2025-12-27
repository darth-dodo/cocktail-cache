"""Pydantic models for user's home bar cabinet.

The cabinet represents the ingredients a user has available
for making cocktails and mocktails.
"""

from pydantic import BaseModel, Field


class Cabinet(BaseModel):
    """User's home bar cabinet containing available ingredients.

    The cabinet is the foundation for recipe matching - only drinks
    that can be made with these ingredients (or close substitutes)
    will be recommended.
    """

    ingredients: list[str] = Field(
        default_factory=list,
        description="List of ingredient IDs available in the user's cabinet",
    )

    def has_ingredient(self, ingredient_id: str) -> bool:
        """Check if a specific ingredient is in the cabinet."""
        return ingredient_id in self.ingredients

    def has_all(self, ingredient_ids: list[str]) -> bool:
        """Check if all specified ingredients are in the cabinet."""
        return all(ing in self.ingredients for ing in ingredient_ids)

    def missing(self, ingredient_ids: list[str]) -> list[str]:
        """Get list of ingredients not in the cabinet."""
        return [ing for ing in ingredient_ids if ing not in self.ingredients]

    def __len__(self) -> int:
        """Return the number of ingredients in the cabinet."""
        return len(self.ingredients)

    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": [
                    "bourbon",
                    "sweet-vermouth",
                    "angostura-bitters",
                    "simple-syrup",
                    "fresh-lemon-juice",
                    "egg-white",
                ]
            }
        }
