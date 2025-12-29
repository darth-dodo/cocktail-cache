"""CrewAI agents for cocktail recommendations.

This module provides factory functions for creating the specialized
agents that power the cocktail recommendation system:

- Drink Recommender: Unified agent for finding and ranking drinks (fast mode)
- Cabinet Analyst: Identifies makeable drinks from available ingredients
- Mood Matcher: Ranks drinks by mood fit and occasion
- Recipe Writer: Generates skill-appropriate recipes with technique tips
- Bottle Advisor: Recommends strategic bottle purchases
- Bar Growth Advisor: Strategic bar building recommendations

All agents default to using Claude Haiku from Anthropic for fast,
cost-effective inference. Custom LLM configurations can be passed
to each factory function.
"""

from src.app.agents.bar_growth_advisor import create_bar_growth_advisor
from src.app.agents.bottle_advisor import create_bottle_advisor
from src.app.agents.cabinet_analyst import create_cabinet_analyst
from src.app.agents.drink_recommender import create_drink_recommender
from src.app.agents.llm_config import get_default_llm, get_llm
from src.app.agents.mood_matcher import create_mood_matcher
from src.app.agents.recipe_writer import create_recipe_writer

__all__ = [
    # Agent factory functions
    "create_drink_recommender",
    "create_cabinet_analyst",
    "create_mood_matcher",
    "create_recipe_writer",
    "create_bottle_advisor",
    "create_bar_growth_advisor",
    # LLM configuration
    "get_default_llm",
    "get_llm",
]
