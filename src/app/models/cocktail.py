"""Pydantic models for cocktail matching and scoring.

These models are used for API responses when matching drinks
to a user's cabinet and preferences.
"""

from pydantic import BaseModel, Field


class CocktailMatch(BaseModel):
    """A cocktail or mocktail that matches the user's cabinet.

    Includes a score indicating how well it matches and what
    ingredients (if any) are missing.
    """

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Match score from 0.0 (poor) to 1.0 (perfect)",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Ingredient IDs missing from cabinet (empty if perfect match)",
    )
    is_mocktail: bool = Field(
        default=False,
        description="Whether this is a non-alcoholic mocktail",
    )

    @property
    def is_perfect_match(self) -> bool:
        """Check if this is a perfect match with no missing ingredients."""
        return len(self.missing) == 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "whiskey-sour",
                "name": "Whiskey Sour",
                "score": 0.95,
                "missing": [],
                "is_mocktail": False,
            }
        }
