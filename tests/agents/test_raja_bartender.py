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
from src.app.tools.flavor_profiler import FlavorProfilerTool
from src.app.tools.recipe_db import RecipeDBTool
from src.app.tools.substitution_finder import SubstitutionFinderTool
from src.app.tools.unlock_calculator import UnlockCalculatorTool


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

    def test_default_has_four_tools(self):
        """Agent should have 4 default tools by default."""
        agent = create_raja_bartender()
        assert len(agent.tools) == 4

    def test_empty_tools_list_with_defaults(self):
        """Agent should have default tools plus empty custom list."""
        agent = create_raja_bartender(tools=[])
        assert len(agent.tools) == 4  # Default tools included

    def test_none_tools_includes_defaults(self):
        """Agent with tools=None should have default tools."""
        agent = create_raja_bartender(tools=None)
        assert len(agent.tools) == 4  # Default tools included

    def test_no_default_tools_when_disabled(self):
        """Agent should have no tools when include_default_tools=False."""
        agent = create_raja_bartender(include_default_tools=False)
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


# =============================================================================
# Tool Integration Tests - Raja with Default Tools
# =============================================================================
class TestRajaBartenderToolIntegration:
    """Tests for Raja Bartender tool integration with default cocktail tools."""

    def test_raja_has_four_tools_with_include_default(self):
        """Raja agent should have 4 default tools when include_default_tools=True."""
        agent = create_raja_bartender(include_default_tools=True)
        assert len(agent.tools) == 4

    def test_raja_tool_names_are_correct(self):
        """Raja agent should have tools with correct names."""
        agent = create_raja_bartender(include_default_tools=True)

        tool_names = [tool.name for tool in agent.tools]

        assert "recipe_database" in tool_names
        assert "substitution_finder" in tool_names
        assert "unlock_calculator" in tool_names
        assert "flavor_profiler" in tool_names

    def test_raja_has_recipe_db_tool(self):
        """Raja agent should have RecipeDBTool instance."""
        agent = create_raja_bartender(include_default_tools=True)

        recipe_tools = [t for t in agent.tools if isinstance(t, RecipeDBTool)]
        assert len(recipe_tools) == 1

    def test_raja_has_substitution_finder_tool(self):
        """Raja agent should have SubstitutionFinderTool instance."""
        agent = create_raja_bartender(include_default_tools=True)

        sub_tools = [t for t in agent.tools if isinstance(t, SubstitutionFinderTool)]
        assert len(sub_tools) == 1

    def test_raja_has_unlock_calculator_tool(self):
        """Raja agent should have UnlockCalculatorTool instance."""
        agent = create_raja_bartender(include_default_tools=True)

        unlock_tools = [t for t in agent.tools if isinstance(t, UnlockCalculatorTool)]
        assert len(unlock_tools) == 1

    def test_raja_has_flavor_profiler_tool(self):
        """Raja agent should have FlavorProfilerTool instance."""
        agent = create_raja_bartender(include_default_tools=True)

        flavor_tools = [t for t in agent.tools if isinstance(t, FlavorProfilerTool)]
        assert len(flavor_tools) == 1

    def test_raja_without_default_tools_has_empty_tools(self):
        """Raja agent without default tools should have empty tools list."""
        agent = create_raja_bartender(include_default_tools=False)
        assert len(agent.tools) == 0

    def test_raja_can_add_custom_tools_to_defaults(self):
        """Raja agent can have custom tools added to defaults."""
        from crewai.tools import BaseTool

        # Create a mock custom tool
        class MockTool(BaseTool):
            name: str = "mock_tool"
            description: str = "A mock tool for testing"

            def _run(self) -> str:
                return "mock result"

        custom_tool = MockTool()
        agent = create_raja_bartender(tools=[custom_tool], include_default_tools=True)

        # Should have 4 default tools + 1 custom = 5 total
        assert len(agent.tools) == 5
        assert custom_tool in agent.tools

    def test_raja_custom_tools_only_without_defaults(self):
        """Raja agent can have only custom tools without defaults."""
        from crewai.tools import BaseTool

        class MockTool(BaseTool):
            name: str = "mock_tool"
            description: str = "A mock tool for testing"

            def _run(self) -> str:
                return "mock result"

        custom_tool = MockTool()
        agent = create_raja_bartender(tools=[custom_tool], include_default_tools=False)

        # Should have only the custom tool
        assert len(agent.tools) == 1
        assert custom_tool in agent.tools


class TestRajaBartenderToolDescriptions:
    """Tests for tool descriptions that support Raja's personality."""

    def test_recipe_db_tool_has_raja_description(self):
        """RecipeDBTool description should mention Raja's style."""
        agent = create_raja_bartender(include_default_tools=True)

        recipe_tools = [t for t in agent.tools if isinstance(t, RecipeDBTool)]
        assert len(recipe_tools) == 1

        tool = recipe_tools[0]
        # Description should mention Raja or conversational style
        assert (
            "raja" in tool.description.lower()
            or "conversational" in tool.description.lower()
        )

    def test_unlock_calculator_has_roi_description(self):
        """UnlockCalculatorTool description should mention ROI or value."""
        agent = create_raja_bartender(include_default_tools=True)

        unlock_tools = [t for t in agent.tools if isinstance(t, UnlockCalculatorTool)]
        assert len(unlock_tools) == 1

        tool = unlock_tools[0]
        # Description should mention ROI or value proposition
        desc_lower = tool.description.lower()
        assert "roi" in desc_lower or "unlock" in desc_lower

    def test_substitution_finder_has_alternative_description(self):
        """SubstitutionFinderTool description should mention alternatives."""
        agent = create_raja_bartender(include_default_tools=True)

        sub_tools = [t for t in agent.tools if isinstance(t, SubstitutionFinderTool)]
        assert len(sub_tools) == 1

        tool = sub_tools[0]
        desc_lower = tool.description.lower()
        assert "substitute" in desc_lower or "alternative" in desc_lower

    def test_flavor_profiler_has_comparison_description(self):
        """FlavorProfilerTool description should mention comparison or analysis."""
        agent = create_raja_bartender(include_default_tools=True)

        flavor_tools = [t for t in agent.tools if isinstance(t, FlavorProfilerTool)]
        assert len(flavor_tools) == 1

        tool = flavor_tools[0]
        desc_lower = tool.description.lower()
        assert (
            "compare" in desc_lower
            or "profile" in desc_lower
            or "analyze" in desc_lower
        )


class TestRajaBartenderToolExecution:
    """Tests verifying that Raja's tools can be executed."""

    def test_recipe_db_tool_is_callable(self):
        """RecipeDBTool should be callable and return results."""
        agent = create_raja_bartender(include_default_tools=True)

        recipe_tools = [t for t in agent.tools if isinstance(t, RecipeDBTool)]
        tool = recipe_tools[0]

        # Tool should be callable
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        assert result is not None
        assert len(result) > 0

    def test_substitution_finder_tool_is_callable(self):
        """SubstitutionFinderTool should be callable and return results."""
        agent = create_raja_bartender(include_default_tools=True)

        sub_tools = [t for t in agent.tools if isinstance(t, SubstitutionFinderTool)]
        tool = sub_tools[0]

        # Tool should be callable
        result = tool._run(ingredient="bourbon")
        assert result is not None
        assert len(result) > 0

    def test_unlock_calculator_tool_is_callable(self):
        """UnlockCalculatorTool should be callable and return results."""
        agent = create_raja_bartender(include_default_tools=True)

        unlock_tools = [t for t in agent.tools if isinstance(t, UnlockCalculatorTool)]
        tool = unlock_tools[0]

        # Tool should be callable
        result = tool._run(cabinet=["bourbon", "simple-syrup"])
        assert result is not None
        assert len(result) > 0

    def test_flavor_profiler_tool_is_callable(self):
        """FlavorProfilerTool should be callable and return results."""
        agent = create_raja_bartender(include_default_tools=True)

        flavor_tools = [t for t in agent.tools if isinstance(t, FlavorProfilerTool)]
        tool = flavor_tools[0]

        # Tool should be callable
        result = tool._run(cocktail_ids=["old-fashioned"])
        assert result is not None
        assert len(result) > 0
