"""Pydantic models for recipe history tracking.

The history tracks which drinks the user has made recently,
enabling the exclusion of recent drinks from recommendations.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A single entry in the user's recipe history.

    Represents one drink that the user marked as "made".
    """

    recipe_id: str = Field(..., description="Unique drink identifier")
    recipe_name: str = Field(..., description="Display name of the drink")
    made_at: datetime = Field(
        default_factory=datetime.now,
        description="When the user made this drink",
    )
    is_mocktail: bool = Field(
        default=False,
        description="Whether this was a mocktail",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recipe_id": "whiskey-sour",
                "recipe_name": "Whiskey Sour",
                "made_at": "2025-01-15T19:30:00",
                "is_mocktail": False,
            }
        }


class RecipeHistory(BaseModel):
    """User's complete recipe history.

    Stored client-side and used to exclude recently made drinks
    from recommendations for variety.
    """

    entries: list[HistoryEntry] = Field(
        default_factory=list,
        description="List of drinks the user has made, most recent first",
    )

    def add(self, recipe_id: str, recipe_name: str, is_mocktail: bool = False) -> None:
        """Add a new entry to the history.

        New entries are added at the beginning of the list.
        """
        entry = HistoryEntry(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            is_mocktail=is_mocktail,
        )
        self.entries.insert(0, entry)

    def recent_ids(self, count: int = 5) -> list[str]:
        """Get IDs of the most recently made drinks.

        Args:
            count: Maximum number of recent IDs to return.

        Returns:
            List of recipe IDs, most recent first.
        """
        return [entry.recipe_id for entry in self.entries[:count]]

    def contains(self, recipe_id: str) -> bool:
        """Check if a recipe has been made before."""
        return any(entry.recipe_id == recipe_id for entry in self.entries)

    def count_by_type(self) -> dict[str, int]:
        """Count drinks by type (cocktail vs mocktail)."""
        cocktails = sum(1 for e in self.entries if not e.is_mocktail)
        mocktails = sum(1 for e in self.entries if e.is_mocktail)
        return {"cocktails": cocktails, "mocktails": mocktails}

    def __len__(self) -> int:
        """Return the number of entries in history."""
        return len(self.entries)

    class Config:
        json_schema_extra = {
            "example": {
                "entries": [
                    {
                        "recipe_id": "margarita",
                        "recipe_name": "Margarita",
                        "made_at": "2025-01-15T20:00:00",
                        "is_mocktail": False,
                    },
                    {
                        "recipe_id": "whiskey-sour",
                        "recipe_name": "Whiskey Sour",
                        "made_at": "2025-01-14T19:30:00",
                        "is_mocktail": False,
                    },
                ]
            }
        }
