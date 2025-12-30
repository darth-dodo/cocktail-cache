"""Pydantic models for the Cocktail Cache application."""

from src.app.models.cabinet import Cabinet
from src.app.models.chat import (
    ChatHistory,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSession,
    DrinkReference,
    MessageIntent,
    MessageRole,
    RajaChatOutput,
)
from src.app.models.cocktail import CocktailMatch
from src.app.models.config import AgentConfig, LLMConfig, TaskConfig
from src.app.models.crew_io import (
    AnalysisInput,
    AnalysisOutput,
    BottleAdvisorOutput,
    BottleRecommendation,
    DrinkCandidate,
    RecipeCrewOutput,
    RecipeInput,
    RecipeOutput,
)
from src.app.models.drinks import (
    Drink,
    FlavorProfile,
    IngredientAmount,
    MethodStep,
)
from src.app.models.history import HistoryEntry, RecipeHistory
from src.app.models.ingredients import (
    Ingredient,
    IngredientsDatabase,
    SubstitutionMap,
    SubstitutionsDatabase,
)
from src.app.models.recipe import Recipe, RecipeIngredient, RecipeStep, TechniqueTip
from src.app.models.recommendation import BottleRec, Recommendation
from src.app.models.unlock_scores import UnlockedDrink, UnlockScores
from src.app.models.user_prefs import DrinkType, SkillLevel, UserPreferences

__all__ = [
    # Cabinet
    "Cabinet",
    # Chat Models
    "ChatHistory",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ChatSession",
    "DrinkReference",
    "MessageIntent",
    "MessageRole",
    "RajaChatOutput",
    # Config Models
    "AgentConfig",
    "LLMConfig",
    "TaskConfig",
    # Cocktail Matching
    "CocktailMatch",
    # Crew I/O Models
    "AnalysisInput",
    "AnalysisOutput",
    "BottleAdvisorOutput",
    "BottleRecommendation",
    "DrinkCandidate",
    "RecipeCrewOutput",
    "RecipeInput",
    "RecipeOutput",
    # Drinks (existing)
    "Drink",
    "FlavorProfile",
    "IngredientAmount",
    "MethodStep",
    # History
    "HistoryEntry",
    "RecipeHistory",
    # Ingredients (existing)
    "Ingredient",
    "IngredientsDatabase",
    "SubstitutionMap",
    "SubstitutionsDatabase",
    # Recipe (API responses)
    "Recipe",
    "RecipeIngredient",
    "RecipeStep",
    "TechniqueTip",
    # Recommendation
    "BottleRec",
    "Recommendation",
    # Unlock Scores (existing)
    "UnlockedDrink",
    "UnlockScores",
    # User Preferences
    "DrinkType",
    "SkillLevel",
    "UserPreferences",
]
