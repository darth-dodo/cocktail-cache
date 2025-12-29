"""CrewAI crew compositions for cocktail recommendation workflows.

This module provides factory functions for creating crews that orchestrate
multiple agents to deliver complete recommendation workflows:

- Analysis Crew: Cabinet Analyst -> Mood Matcher
  Finds makeable drinks and ranks them by mood fit

- Recipe Crew: Recipe Writer -> Bottle Advisor
  Generates recipes with technique tips and purchase advice

- Bar Growth Crew: Bar Growth Advisor
  Provides strategic bottle purchase recommendations
"""

from src.app.crews.analysis_crew import create_analysis_crew, run_analysis_crew
from src.app.crews.bar_growth_crew import create_bar_growth_crew, run_bar_growth_crew
from src.app.crews.recipe_crew import create_recipe_crew, run_recipe_crew

__all__ = [
    # Analysis workflow
    "create_analysis_crew",
    "run_analysis_crew",
    # Recipe generation workflow
    "create_recipe_crew",
    "run_recipe_crew",
    # Bar growth workflow
    "create_bar_growth_crew",
    "run_bar_growth_crew",
]
