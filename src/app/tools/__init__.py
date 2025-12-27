"""Deterministic tools for cocktail data operations.

These tools are designed for use with CrewAI agents and provide
pure data lookup functionality without LLM calls. All tools return
JSON strings for easy consumption by agents.

Tools:
    RecipeDBTool: Search and retrieve drink recipes by ingredients
    FlavorProfilerTool: Analyze and compare drink flavor profiles
    SubstitutionFinderTool: Find ingredient substitutions
    UnlockCalculatorTool: Calculate best bottles to buy for maximum ROI
"""

from src.app.tools.flavor_profiler import FlavorProfilerTool
from src.app.tools.recipe_db import RecipeDBTool
from src.app.tools.substitution_finder import SubstitutionFinderTool
from src.app.tools.unlock_calculator import UnlockCalculatorTool

__all__ = [
    "RecipeDBTool",
    "FlavorProfilerTool",
    "SubstitutionFinderTool",
    "UnlockCalculatorTool",
]
