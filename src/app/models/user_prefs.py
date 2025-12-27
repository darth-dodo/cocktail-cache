"""Pydantic models for user preferences.

These models capture user skill level, drink type preferences,
and other settings that influence recommendations.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    """User's bartending skill level.

    Affects recipe complexity and technique tip verbosity.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVENTUROUS = "adventurous"


class DrinkType(str, Enum):
    """User's drink type preference.

    Controls whether to show cocktails, mocktails, or both.
    """

    COCKTAIL = "cocktail"
    MOCKTAIL = "mocktail"
    BOTH = "both"


class UserPreferences(BaseModel):
    """User preferences that influence recommendations.

    These settings are stored client-side and sent with each
    recommendation request.
    """

    skill_level: SkillLevel = Field(
        default=SkillLevel.INTERMEDIATE,
        description="User's bartending skill level",
    )
    drink_type: DrinkType = Field(
        default=DrinkType.COCKTAIL,
        description="Preferred drink type (cocktail/mocktail/both)",
    )
    exclude_count: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Number of recent drinks to exclude from recommendations",
    )

    def allows_cocktails(self) -> bool:
        """Check if preferences allow cocktail recommendations."""
        return self.drink_type in (DrinkType.COCKTAIL, DrinkType.BOTH)

    def allows_mocktails(self) -> bool:
        """Check if preferences allow mocktail recommendations."""
        return self.drink_type in (DrinkType.MOCKTAIL, DrinkType.BOTH)

    class Config:
        json_schema_extra = {
            "example": {
                "skill_level": "intermediate",
                "drink_type": "both",
                "exclude_count": 5,
            }
        }
