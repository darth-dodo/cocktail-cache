"""Pydantic models for unlock scores (next bottle recommendations).

The unlock scores track which ingredients unlock which drinks,
enabling the "next bottle to buy" recommendation feature.
"""

from pydantic import BaseModel, Field, RootModel


class UnlockedDrink(BaseModel):
    """A drink that an ingredient helps unlock."""

    id: str = Field(..., description="Drink ID")
    name: str = Field(..., description="Drink display name")
    is_mocktail: bool = Field(default=False)
    difficulty: str = Field(..., pattern="^(easy|medium|hard|advanced)$")
    other: list[str] = Field(
        default_factory=list,
        description="Other ingredient IDs needed for this drink",
    )


class UnlockScores(RootModel[dict[str, list[UnlockedDrink]]]):
    """Complete unlock scores database.

    Maps ingredient IDs to lists of drinks they help make.
    Higher unlock counts indicate more versatile ingredients.
    """

    def __getitem__(self, key: str) -> list[UnlockedDrink]:
        return self.root[key]

    def __iter__(self):
        return iter(self.root)

    def __len__(self):
        return len(self.root)

    def items(self):
        return self.root.items()

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()

    def get_unlock_count(self, ingredient_id: str) -> int:
        """Get the number of drinks an ingredient unlocks."""
        return len(self.root.get(ingredient_id, []))

    def get_top_ingredients(self, n: int = 10) -> list[tuple[str, int]]:
        """Get the top N most versatile ingredients."""
        counts = [(ing, len(drinks)) for ing, drinks in self.root.items()]
        counts.sort(key=lambda x: x[1], reverse=True)
        return counts[:n]
