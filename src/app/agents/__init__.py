"""CrewAI agents for cocktail recommendations.

This module provides factory functions for creating the four specialized
agents that power the cocktail recommendation system:

- Cabinet Analyst: Identifies makeable drinks from available ingredients
- Mood Matcher: Ranks drinks by mood fit and occasion
- Recipe Writer: Generates skill-appropriate recipes with technique tips
- Bottle Advisor: Recommends strategic bottle purchases
"""

from src.app.agents.bottle_advisor import create_bottle_advisor
from src.app.agents.cabinet_analyst import create_cabinet_analyst
from src.app.agents.mood_matcher import create_mood_matcher
from src.app.agents.recipe_writer import create_recipe_writer

__all__ = [
    "create_cabinet_analyst",
    "create_mood_matcher",
    "create_recipe_writer",
    "create_bottle_advisor",
]
