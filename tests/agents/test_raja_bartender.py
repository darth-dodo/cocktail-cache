"""Unit tests for the Raja Bartender agent.

Tests verify that the Raja Bartender agent is properly configured with
the correct role, goal, backstory, and LLM settings.
"""

import os

# Set mock API keys before importing CrewAI to bypass validation
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from crewai import LLM, Agent

from src.app.agents.raja_bartender import create_raja_bartender


class TestCreateRajaBartender:
    """Tests for the create_raja_bartender factory function."""

    def test_returns_agent_instance(self):
        """Factory should return a CrewAI Agent instance."""
        agent = create_raja_bartender()
        assert isinstance(agent, Agent)

    def test_agent_role_contains_raja(self):
        """Agent role should identify as Raja."""
        agent = create_raja_bartender()
        assert "Raja" in agent.role

    def test_agent_role_contains_bartender(self):
        """Agent role should identify as bartender."""
        agent = create_raja_bartender()
        assert "Bartender" in agent.role or "bartender" in agent.role.lower()

    def test_agent_goal_mentions_conversations(self):
        """Agent goal should mention conversations or chat."""
        agent = create_raja_bartender()
        goal_lower = agent.goal.lower()
        assert "conversation" in goal_lower or "snappy" in goal_lower

    def test_agent_goal_mentions_cocktails(self):
        """Agent goal should mention cocktails or mixology."""
        agent = create_raja_bartender()
        goal_lower = agent.goal.lower()
        assert "cocktail" in goal_lower or "mixology" in goal_lower


class TestRajaBartenderBackstory:
    """Tests for Raja Bartender backstory configuration."""

    def test_backstory_mentions_bombay(self):
        """Backstory should mention Bombay/Colaba origin."""
        agent = create_raja_bartender()
        backstory_lower = agent.backstory.lower()
        assert "bombay" in backstory_lower or "colaba" in backstory_lower

    def test_backstory_mentions_respectful_hindi(self):
        """Backstory should mention respectful Hindi terms."""
        agent = create_raja_bartender()
        backstory_lower = agent.backstory.lower()
        # Should mention Hindi phrases like yaar, bhai, etc.
        assert "yaar" in backstory_lower or "bhai" in backstory_lower

    def test_backstory_mentions_second_hand_stories(self):
        """Backstory should mention using second-hand stories."""
        agent = create_raja_bartender()
        backstory_lower = agent.backstory.lower()
        assert "second-hand" in backstory_lower or "legend" in backstory_lower

    def test_backstory_mentions_snappy_responses(self):
        """Backstory should mention snappy/concise responses."""
        agent = create_raja_bartender()
        backstory_lower = agent.backstory.lower()
        assert "snappy" in backstory_lower or "2-3 sentences" in backstory_lower


class TestRajaBartenderTools:
    """Tests for Raja Bartender tool configuration."""

    def test_default_no_tools(self):
        """Agent should have no tools by default."""
        agent = create_raja_bartender()
        assert len(agent.tools) == 0

    def test_empty_tools_list(self):
        """Agent should accept empty tools list."""
        agent = create_raja_bartender(tools=[])
        assert len(agent.tools) == 0

    def test_none_tools_defaults_to_empty(self):
        """Agent with tools=None should have empty tools list."""
        agent = create_raja_bartender(tools=None)
        assert len(agent.tools) == 0


class TestRajaBartenderLLM:
    """Tests for Raja Bartender LLM configuration."""

    def test_default_uses_conversational_profile(self):
        """Agent should use conversational LLM profile by default."""
        agent = create_raja_bartender()
        assert agent.llm is not None

    def test_accepts_custom_llm(self):
        """Agent should use provided custom LLM."""
        custom_llm = LLM(model="anthropic/claude-3-haiku-20240307", temperature=0.5)
        agent = create_raja_bartender(llm=custom_llm)

        assert agent.llm == custom_llm


class TestRajaBartenderConfiguration:
    """Tests for Raja Bartender configuration options."""

    def test_verbose_is_false(self):
        """Agent should have verbose=False for clean output."""
        agent = create_raja_bartender()
        assert agent.verbose is False

    def test_allow_delegation_is_false(self):
        """Agent should have allow_delegation=False."""
        agent = create_raja_bartender()
        assert agent.allow_delegation is False


class TestRajaBartenderConsistency:
    """Tests for consistent agent creation."""

    def test_agent_is_reproducible(self):
        """Creating multiple agents should yield consistent configurations."""
        agent1 = create_raja_bartender()
        agent2 = create_raja_bartender()

        assert agent1.role == agent2.role
        assert agent1.goal == agent2.goal
        assert agent1.backstory == agent2.backstory
        assert agent1.verbose == agent2.verbose
        assert agent1.allow_delegation == agent2.allow_delegation

    def test_agent_with_none_vs_empty_tools_has_same_role(self):
        """Agents with None vs empty tools should have same role/goal."""
        agent_none_tools = create_raja_bartender(tools=None)
        agent_empty_tools = create_raja_bartender(tools=[])

        assert agent_none_tools.role == agent_empty_tools.role
        assert agent_none_tools.goal == agent_empty_tools.goal
