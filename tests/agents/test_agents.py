"""Unit tests for CrewAI agent factory functions.

Tests verify that agent factory functions return properly configured
Agent instances with correct attributes. These tests do not require
an LLM connection as they only test object configuration.
"""

import os

import pytest

# Set mock API keys before importing CrewAI to bypass validation
# These keys are never used for actual API calls in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from crewai import Agent
from crewai.tools import BaseTool

from src.app.agents import (
    create_bottle_advisor,
    create_cabinet_analyst,
    create_mood_matcher,
    create_recipe_writer,
)


class MockTool(BaseTool):
    """Simple mock tool for testing agent configuration."""

    name: str = "mock_tool"
    description: str = "A mock tool for testing"

    def _run(self, *args, **kwargs) -> str:
        return "mock result"


class TestCabinetAnalyst:
    """Tests for the Cabinet Analyst agent factory."""

    def test_create_cabinet_analyst_returns_agent(self):
        """Factory should return a CrewAI Agent instance."""
        agent = create_cabinet_analyst()
        assert isinstance(agent, Agent)

    def test_create_cabinet_analyst_default_no_tools(self):
        """Agent should have empty tools list by default."""
        agent = create_cabinet_analyst()
        assert agent.tools == []

    def test_create_cabinet_analyst_with_custom_tools(self):
        """Agent should accept and use custom tools list."""
        mock_tools = [MockTool(), MockTool()]
        agent = create_cabinet_analyst(tools=mock_tools)
        assert len(agent.tools) == 2

    def test_create_cabinet_analyst_role(self):
        """Agent should have correct role."""
        agent = create_cabinet_analyst()
        assert agent.role == "Cabinet Analyst"

    def test_create_cabinet_analyst_goal(self):
        """Agent should have correct goal."""
        agent = create_cabinet_analyst()
        assert agent.goal == "Identify all drinks makeable with available ingredients"

    def test_create_cabinet_analyst_backstory_set(self):
        """Agent should have a non-empty backstory."""
        agent = create_cabinet_analyst()
        assert agent.backstory is not None
        assert len(agent.backstory) > 0

    def test_create_cabinet_analyst_backstory_content(self):
        """Backstory should mention key concepts."""
        agent = create_cabinet_analyst()
        backstory = agent.backstory.lower()
        assert "mixologist" in backstory
        assert "cocktail" in backstory
        assert "mocktail" in backstory

    def test_create_cabinet_analyst_verbose_false(self):
        """Agent should have verbose=False."""
        agent = create_cabinet_analyst()
        assert agent.verbose is False

    def test_create_cabinet_analyst_allow_delegation_false(self):
        """Agent should have allow_delegation=False."""
        agent = create_cabinet_analyst()
        assert agent.allow_delegation is False

    def test_create_cabinet_analyst_with_none_tools(self):
        """Explicitly passing None should result in empty tools list."""
        agent = create_cabinet_analyst(tools=None)
        assert agent.tools == []


class TestMoodMatcher:
    """Tests for the Mood Matcher agent factory."""

    def test_create_mood_matcher_returns_agent(self):
        """Factory should return a CrewAI Agent instance."""
        agent = create_mood_matcher()
        assert isinstance(agent, Agent)

    def test_create_mood_matcher_default_no_tools(self):
        """Agent should have empty tools list by default."""
        agent = create_mood_matcher()
        assert agent.tools == []

    def test_create_mood_matcher_with_custom_tools(self):
        """Agent should accept and use custom tools list."""
        mock_tools = [MockTool()]
        agent = create_mood_matcher(tools=mock_tools)
        assert len(agent.tools) == 1

    def test_create_mood_matcher_role(self):
        """Agent should have correct role."""
        agent = create_mood_matcher()
        assert agent.role == "Mood Matcher"

    def test_create_mood_matcher_goal(self):
        """Agent should have correct goal."""
        agent = create_mood_matcher()
        assert agent.goal == "Rank drinks by mood fit and occasion"

    def test_create_mood_matcher_backstory_set(self):
        """Agent should have a non-empty backstory."""
        agent = create_mood_matcher()
        assert agent.backstory is not None
        assert len(agent.backstory) > 0

    def test_create_mood_matcher_backstory_content(self):
        """Backstory should mention mood-related concepts."""
        agent = create_mood_matcher()
        backstory = agent.backstory.lower()
        assert "mood" in backstory
        assert "emotional" in backstory

    def test_create_mood_matcher_verbose_false(self):
        """Agent should have verbose=False."""
        agent = create_mood_matcher()
        assert agent.verbose is False

    def test_create_mood_matcher_allow_delegation_false(self):
        """Agent should have allow_delegation=False."""
        agent = create_mood_matcher()
        assert agent.allow_delegation is False

    def test_create_mood_matcher_with_none_tools(self):
        """Explicitly passing None should result in empty tools list."""
        agent = create_mood_matcher(tools=None)
        assert agent.tools == []


class TestRecipeWriter:
    """Tests for the Recipe Writer agent factory."""

    def test_create_recipe_writer_returns_agent(self):
        """Factory should return a CrewAI Agent instance."""
        agent = create_recipe_writer()
        assert isinstance(agent, Agent)

    def test_create_recipe_writer_default_no_tools(self):
        """Agent should have empty tools list by default."""
        agent = create_recipe_writer()
        assert agent.tools == []

    def test_create_recipe_writer_with_custom_tools(self):
        """Agent should accept and use custom tools list."""
        mock_tools = [MockTool(), MockTool()]
        agent = create_recipe_writer(tools=mock_tools)
        assert len(agent.tools) == 2

    def test_create_recipe_writer_role(self):
        """Agent should have correct role."""
        agent = create_recipe_writer()
        assert agent.role == "Recipe Writer"

    def test_create_recipe_writer_goal(self):
        """Agent should have correct goal."""
        agent = create_recipe_writer()
        assert (
            agent.goal
            == "Generate clear, skill-appropriate recipes with technique tips"
        )

    def test_create_recipe_writer_goal_mentions_clear(self):
        """Goal should emphasize clarity."""
        agent = create_recipe_writer()
        assert "clear" in agent.goal.lower()

    def test_create_recipe_writer_goal_mentions_skill(self):
        """Goal should mention skill-appropriate content."""
        agent = create_recipe_writer()
        assert "skill" in agent.goal.lower()

    def test_create_recipe_writer_backstory_set(self):
        """Agent should have a non-empty backstory."""
        agent = create_recipe_writer()
        assert agent.backstory is not None
        assert len(agent.backstory) > 0

    def test_create_recipe_writer_backstory_mentions_skill_levels(self):
        """Backstory should mention different skill levels."""
        agent = create_recipe_writer()
        backstory = agent.backstory.lower()
        assert "beginner" in backstory
        assert "intermediate" in backstory

    def test_create_recipe_writer_verbose_false(self):
        """Agent should have verbose=False."""
        agent = create_recipe_writer()
        assert agent.verbose is False

    def test_create_recipe_writer_allow_delegation_false(self):
        """Agent should have allow_delegation=False."""
        agent = create_recipe_writer()
        assert agent.allow_delegation is False

    def test_create_recipe_writer_with_none_tools(self):
        """Explicitly passing None should result in empty tools list."""
        agent = create_recipe_writer(tools=None)
        assert agent.tools == []


class TestBottleAdvisor:
    """Tests for the Bottle Advisor agent factory."""

    def test_create_bottle_advisor_returns_agent(self):
        """Factory should return a CrewAI Agent instance."""
        agent = create_bottle_advisor()
        assert isinstance(agent, Agent)

    def test_create_bottle_advisor_default_no_tools(self):
        """Agent should have empty tools list by default."""
        agent = create_bottle_advisor()
        assert agent.tools == []

    def test_create_bottle_advisor_with_custom_tools(self):
        """Agent should accept and use custom tools list."""
        mock_tools = [MockTool()]
        agent = create_bottle_advisor(tools=mock_tools)
        assert len(agent.tools) == 1

    def test_create_bottle_advisor_role(self):
        """Agent should have correct role."""
        agent = create_bottle_advisor()
        assert agent.role == "Bottle Advisor"

    def test_create_bottle_advisor_goal(self):
        """Agent should have correct goal."""
        agent = create_bottle_advisor()
        assert agent.goal == "Recommend the next bottle purchase for maximum value"

    def test_create_bottle_advisor_goal_mentions_value(self):
        """Goal should emphasize value/ROI."""
        agent = create_bottle_advisor()
        assert "value" in agent.goal.lower()

    def test_create_bottle_advisor_backstory_set(self):
        """Agent should have a non-empty backstory."""
        agent = create_bottle_advisor()
        assert agent.backstory is not None
        assert len(agent.backstory) > 0

    def test_create_bottle_advisor_backstory_mentions_unlock(self):
        """Backstory should mention unlocking new drinks."""
        agent = create_bottle_advisor()
        backstory = agent.backstory.lower()
        assert "unlock" in backstory

    def test_create_bottle_advisor_backstory_mentions_budget(self):
        """Backstory should mention budget considerations."""
        agent = create_bottle_advisor()
        backstory = agent.backstory.lower()
        assert "budget" in backstory

    def test_create_bottle_advisor_verbose_false(self):
        """Agent should have verbose=False."""
        agent = create_bottle_advisor()
        assert agent.verbose is False

    def test_create_bottle_advisor_allow_delegation_false(self):
        """Agent should have allow_delegation=False."""
        agent = create_bottle_advisor()
        assert agent.allow_delegation is False

    def test_create_bottle_advisor_with_none_tools(self):
        """Explicitly passing None should result in empty tools list."""
        agent = create_bottle_advisor(tools=None)
        assert agent.tools == []


class TestAgentConsistency:
    """Cross-agent consistency tests."""

    @pytest.fixture
    def all_agents(self):
        """Create all agents for comparison tests."""
        return {
            "cabinet_analyst": create_cabinet_analyst(),
            "mood_matcher": create_mood_matcher(),
            "recipe_writer": create_recipe_writer(),
            "bottle_advisor": create_bottle_advisor(),
        }

    def test_all_agents_are_agent_instances(self, all_agents):
        """All factories should return Agent instances."""
        for name, agent in all_agents.items():
            assert isinstance(agent, Agent), f"{name} is not an Agent instance"

    def test_all_agents_have_unique_roles(self, all_agents):
        """All agents should have distinct roles."""
        roles = [agent.role for agent in all_agents.values()]
        assert len(roles) == len(set(roles)), "Agent roles are not unique"

    def test_all_agents_have_verbose_false(self, all_agents):
        """All agents should have verbose=False."""
        for name, agent in all_agents.items():
            assert agent.verbose is False, f"{name} has verbose=True"

    def test_all_agents_have_allow_delegation_false(self, all_agents):
        """All agents should have allow_delegation=False."""
        for name, agent in all_agents.items():
            assert agent.allow_delegation is False, f"{name} allows delegation"

    def test_all_agents_have_non_empty_goals(self, all_agents):
        """All agents should have meaningful goals."""
        for name, agent in all_agents.items():
            assert agent.goal is not None, f"{name} has no goal"
            assert len(agent.goal) > 10, f"{name} has a suspiciously short goal"

    def test_all_agents_have_non_empty_backstories(self, all_agents):
        """All agents should have substantial backstories."""
        for name, agent in all_agents.items():
            assert agent.backstory is not None, f"{name} has no backstory"
            assert (
                len(agent.backstory) > 50
            ), f"{name} has a suspiciously short backstory"

    def test_all_agents_default_to_empty_tools(self, all_agents):
        """All agents should default to empty tools list."""
        for name, agent in all_agents.items():
            assert agent.tools == [], f"{name} has non-empty default tools"
