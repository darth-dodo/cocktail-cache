"""Pydantic models for CrewAI crew inputs and outputs.

These models provide structured, typed data for crew task inputs
and outputs, ensuring reliable data flow through the AI pipeline.
"""

from pydantic import BaseModel, Field

from src.app.models.drinks import FlavorProfile
from src.app.models.recipe import RecipeIngredient, RecipeStep, TechniqueTip

# ============================================================================
# Analysis Crew Models
# ============================================================================


class AnalysisInput(BaseModel):
    """Input parameters for the Analysis Crew."""

    cabinet: list[str] = Field(
        ...,
        min_length=1,
        description="List of ingredient IDs available in user's cabinet",
    )
    drink_type: str = Field(
        default="both",
        pattern="^(cocktails|mocktails|both)$",
        description="Filter for drink type preference",
    )
    mood: str = Field(
        default="",
        description="User's current mood or occasion description",
    )
    skill_level: str = Field(
        default="intermediate",
        pattern="^(beginner|intermediate|adventurous)$",
        description="User's bartending skill level",
    )
    exclude: list[str] = Field(
        default_factory=list,
        description="List of drink IDs to exclude from recommendations",
    )


class DrinkCandidate(BaseModel):
    """A candidate drink from cabinet analysis with mood scoring."""

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(default="", description="Short description")
    difficulty: str = Field(
        default="easy",
        pattern="^(easy|medium|hard|advanced)$",
        description="Skill level required",
    )
    timing_minutes: int = Field(default=5, ge=1, description="Preparation time")
    tags: list[str] = Field(default_factory=list, description="Flavor/style tags")
    is_mocktail: bool = Field(default=False, description="Whether it's a mocktail")
    mood_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="How well this drink matches the mood (0-100)",
    )
    mood_reasoning: str = Field(
        default="",
        description="Brief explanation of why this matches the mood",
    )


class AnalysisOutput(BaseModel):
    """Output from the Analysis Crew with ranked drink candidates."""

    candidates: list[DrinkCandidate] = Field(
        default_factory=list,
        description="Ranked list of candidate drinks, best match first",
    )
    total_found: int = Field(
        default=0,
        ge=0,
        description="Total number of makeable drinks found",
    )
    mood_summary: str = Field(
        default="",
        description="Summary of how mood influenced rankings",
    )


# ============================================================================
# Recipe Crew Models
# ============================================================================


class RecipeInput(BaseModel):
    """Input parameters for the Recipe Crew."""

    cocktail_id: str = Field(
        ..., description="ID of the cocktail to generate recipe for"
    )
    skill_level: str = Field(
        default="intermediate",
        pattern="^(beginner|intermediate|adventurous)$",
        description="User's skill level for technique tip tailoring",
    )
    cabinet: list[str] = Field(
        default_factory=list,
        description="User's available ingredients for substitution suggestions",
    )
    drink_type: str = Field(
        default="cocktail",
        description="Preferred drink type",
    )


class RecipeOutput(BaseModel):
    """Structured recipe output from Recipe Writer task."""

    id: str = Field(..., description="Unique drink identifier")
    name: str = Field(..., description="Display name of the drink")
    tagline: str = Field(..., description="Short catchy description")
    why: str = Field(
        ...,
        description="Explanation of why this drink was recommended for the user's mood",
    )
    flavor_profile: FlavorProfile = Field(
        default_factory=lambda: FlavorProfile(sweet=50, sour=25, bitter=25, spirit=50)
    )
    ingredients: list[RecipeIngredient] = Field(..., min_length=1)
    method: list[RecipeStep] = Field(..., min_length=1)
    glassware: str = Field(..., description="Type of glass to serve in")
    garnish: str = Field(..., description="Garnish description")
    timing: str = Field(..., description="Preparation time (e.g., '3 minutes')")
    difficulty: str = Field(
        default="easy",
        pattern="^(easy|medium|hard|advanced)$",
    )
    technique_tips: list[TechniqueTip] = Field(
        default_factory=list,
        description="Skill-appropriate technique tips",
    )
    substitutions: list[str] = Field(
        default_factory=list,
        description="Suggested ingredient substitutions if any are missing",
    )
    is_mocktail: bool = Field(default=False)


class BottleRecommendation(BaseModel):
    """A single bottle purchase recommendation."""

    ingredient: str = Field(..., description="Ingredient ID to purchase")
    ingredient_name: str = Field(..., description="Display name of the ingredient")
    unlocks: int = Field(..., ge=0, description="Number of new drinks this unlocks")
    drinks: list[str] = Field(
        default_factory=list,
        description="Names of specific drinks this ingredient would unlock",
    )
    reasoning: str = Field(
        default="",
        description="Why this is a good purchase for the user",
    )


class BottleAdvisorOutput(BaseModel):
    """Output from Bottle Advisor task with purchase recommendations."""

    recommendations: list[BottleRecommendation] = Field(
        default_factory=list,
        max_length=3,
        description="Top bottle recommendations, best value first",
    )
    total_new_drinks: int = Field(
        default=0,
        ge=0,
        description="Total new drinks available if all recommendations purchased",
    )


class RecipeCrewOutput(BaseModel):
    """Combined output from the Recipe Crew (both tasks)."""

    recipe: RecipeOutput = Field(..., description="The generated recipe")
    bottle_advice: BottleAdvisorOutput = Field(
        default_factory=BottleAdvisorOutput,
        description="Bottle purchase recommendations",
    )
