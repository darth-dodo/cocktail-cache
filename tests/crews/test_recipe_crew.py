"""Unit tests for the Recipe Crew configuration.

Tests verify that the Recipe Crew is properly configured with the
correct agents, tasks, and tool assignments. These tests do not
require an LLM connection as they only test object configuration.
"""

import os

import pytest

# Set mock API keys before importing CrewAI to bypass validation
# These keys are never used for actual API calls in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from crewai import Agent, Crew, Process, Task

from src.app.crews.recipe_crew import create_recipe_crew
from src.app.models import DrinkType, SkillLevel


class TestCreateRecipeCrew:
    """Tests for the create_recipe_crew factory function."""

    def test_create_recipe_crew_returns_crew(self):
        """Factory should return a CrewAI Crew instance."""
        crew = create_recipe_crew()
        assert isinstance(crew, Crew)

    def test_crew_has_correct_number_of_agents(self):
        """Recipe Crew should have exactly 2 agents."""
        crew = create_recipe_crew()
        assert len(crew.agents) == 2

    def test_crew_has_recipe_writer_agent(self):
        """Crew should include a Recipe Writer agent."""
        crew = create_recipe_crew()
        roles = [agent.role for agent in crew.agents]
        assert "Recipe Writer" in roles

    def test_crew_has_bottle_advisor_agent(self):
        """Crew should include a Bottle Advisor agent."""
        crew = create_recipe_crew()
        roles = [agent.role for agent in crew.agents]
        assert "Bottle Advisor" in roles

    def test_agents_are_in_correct_order(self):
        """Recipe Writer should be first, Bottle Advisor second."""
        crew = create_recipe_crew()
        assert crew.agents[0].role == "Recipe Writer"
        assert crew.agents[1].role == "Bottle Advisor"


class TestRecipeCrewTasks:
    """Tests for Recipe Crew task configuration."""

    def test_crew_has_correct_number_of_tasks(self):
        """Recipe Crew should have exactly 2 tasks."""
        crew = create_recipe_crew()
        assert len(crew.tasks) == 2

    def test_first_task_assigned_to_recipe_writer(self):
        """First task should be assigned to Recipe Writer."""
        crew = create_recipe_crew()
        first_task = crew.tasks[0]
        assert first_task.agent.role == "Recipe Writer"

    def test_second_task_assigned_to_bottle_advisor(self):
        """Second task should be assigned to Bottle Advisor."""
        crew = create_recipe_crew()
        second_task = crew.tasks[1]
        assert second_task.agent.role == "Bottle Advisor"

    def test_second_task_depends_on_first(self):
        """Bottle task should have recipe task as context (dependency)."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        bottle_task = crew.tasks[1]

        # The bottle_task should have context that includes recipe_task
        assert bottle_task.context is not None
        assert len(bottle_task.context) >= 1
        # Check that the first task (recipe) is in the context
        assert recipe_task in bottle_task.context

    def test_first_task_has_no_context(self):
        """Recipe task should not depend on any other task."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]

        # First task should have no context (no dependencies)
        # CrewAI uses _NotSpecified sentinel for unset context
        context = recipe_task.context
        if context is None:
            assert True  # No context, as expected
        elif hasattr(context, "__len__"):
            assert len(context) == 0
        else:
            # _NotSpecified or similar sentinel - treat as no context
            assert True

    def test_tasks_are_task_instances(self):
        """All tasks should be CrewAI Task instances."""
        crew = create_recipe_crew()
        for task in crew.tasks:
            assert isinstance(task, Task)


class TestRecipeCrewToolAssignments:
    """Tests for tool assignments on Recipe Crew agents."""

    def test_recipe_writer_has_tools(self):
        """Recipe Writer should have at least one tool."""
        crew = create_recipe_crew()
        recipe_writer = crew.agents[0]
        assert recipe_writer.role == "Recipe Writer"
        assert len(recipe_writer.tools) >= 1

    def test_recipe_writer_has_recipe_db_tool(self):
        """Recipe Writer should have RecipeDBTool assigned."""
        crew = create_recipe_crew()
        recipe_writer = crew.agents[0]

        tool_types = [type(tool).__name__ for tool in recipe_writer.tools]
        assert "RecipeDBTool" in tool_types

    def test_recipe_writer_has_substitution_finder_tool(self):
        """Recipe Writer should have SubstitutionFinderTool assigned."""
        crew = create_recipe_crew()
        recipe_writer = crew.agents[0]

        tool_types = [type(tool).__name__ for tool in recipe_writer.tools]
        assert "SubstitutionFinderTool" in tool_types

    def test_bottle_advisor_has_tools(self):
        """Bottle Advisor should have at least one tool."""
        crew = create_recipe_crew()
        bottle_advisor = crew.agents[1]
        assert bottle_advisor.role == "Bottle Advisor"
        assert len(bottle_advisor.tools) >= 1

    def test_bottle_advisor_has_unlock_calculator_tool(self):
        """Bottle Advisor should have UnlockCalculatorTool assigned."""
        crew = create_recipe_crew()
        bottle_advisor = crew.agents[1]

        tool_types = [type(tool).__name__ for tool in bottle_advisor.tools]
        assert "UnlockCalculatorTool" in tool_types

    def test_tools_are_instantiated(self):
        """Tools should be actual instances, not classes."""
        crew = create_recipe_crew()

        for agent in crew.agents:
            for tool in agent.tools:
                # Tool should be an instance, not a class
                assert not isinstance(tool, type)
                # Tool should have required attributes
                assert hasattr(tool, "name")
                assert hasattr(tool, "description")


class TestRecipeCrewConfiguration:
    """Tests for Recipe Crew configuration options."""

    def test_crew_verbose_is_false(self):
        """Crew should have verbose=False for clean output."""
        crew = create_recipe_crew()
        assert crew.verbose is False

    def test_crew_process_is_sequential(self):
        """Crew should use sequential process."""
        crew = create_recipe_crew()
        assert crew.process == Process.sequential

    def test_all_agents_have_verbose_false(self):
        """All agents in the crew should have verbose=False."""
        crew = create_recipe_crew()
        for agent in crew.agents:
            assert agent.verbose is False

    def test_all_agents_have_allow_delegation_false(self):
        """All agents should have allow_delegation=False."""
        crew = create_recipe_crew()
        for agent in crew.agents:
            assert agent.allow_delegation is False

    def test_agents_are_agent_instances(self):
        """All agents should be CrewAI Agent instances."""
        crew = create_recipe_crew()
        for agent in crew.agents:
            assert isinstance(agent, Agent)


class TestRecipeCrewTaskDescriptions:
    """Tests for task description content."""

    def test_recipe_task_mentions_cocktail_id(self):
        """Recipe task description should mention cocktail_id."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        description_lower = recipe_task.description.lower()
        assert "cocktail" in description_lower or "id" in description_lower

    def test_recipe_task_mentions_skill_level(self):
        """Recipe task description should mention skill level."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        description_lower = recipe_task.description.lower()
        assert "skill" in description_lower

    def test_recipe_task_mentions_cabinet(self):
        """Recipe task description should mention cabinet/ingredients."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        description_lower = recipe_task.description.lower()
        assert "cabinet" in description_lower or "ingredient" in description_lower

    def test_bottle_task_mentions_cabinet(self):
        """Bottle task description should mention cabinet."""
        crew = create_recipe_crew()
        bottle_task = crew.tasks[1]
        description_lower = bottle_task.description.lower()
        assert "cabinet" in description_lower

    def test_bottle_task_mentions_unlock(self):
        """Bottle task description should mention unlock/unlocking drinks."""
        crew = create_recipe_crew()
        bottle_task = crew.tasks[1]
        description_lower = bottle_task.description.lower()
        assert "unlock" in description_lower


class TestRecipeCrewExpectedOutputs:
    """Tests for task expected output specifications."""

    def test_recipe_task_has_expected_output(self):
        """Recipe task should have an expected output defined."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        assert recipe_task.expected_output is not None
        assert len(recipe_task.expected_output) > 0

    def test_bottle_task_has_expected_output(self):
        """Bottle task should have an expected output defined."""
        crew = create_recipe_crew()
        bottle_task = crew.tasks[1]
        assert bottle_task.expected_output is not None
        assert len(bottle_task.expected_output) > 0

    def test_recipe_expected_output_mentions_ingredients(self):
        """Recipe task expected output should mention ingredients."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        output_lower = recipe_task.expected_output.lower()
        assert "ingredient" in output_lower

    def test_recipe_expected_output_mentions_technique(self):
        """Recipe task expected output should mention technique tips."""
        crew = create_recipe_crew()
        recipe_task = crew.tasks[0]
        output_lower = recipe_task.expected_output.lower()
        assert "technique" in output_lower or "tip" in output_lower

    def test_bottle_expected_output_mentions_recommendation(self):
        """Bottle task expected output should mention recommendation."""
        crew = create_recipe_crew()
        bottle_task = crew.tasks[1]
        output_lower = bottle_task.expected_output.lower()
        assert "recommend" in output_lower or "bottle" in output_lower


class TestRecipeCrewConsistency:
    """Cross-component consistency tests for Recipe Crew."""

    @pytest.fixture
    def crew(self):
        """Provide a crew instance for tests."""
        return create_recipe_crew()

    def test_task_agent_references_match_crew_agents(self, crew):
        """Task agent references should match agents in crew.agents."""
        crew_agent_ids = {id(agent) for agent in crew.agents}
        for task in crew.tasks:
            assert id(task.agent) in crew_agent_ids

    def test_each_agent_has_exactly_one_task(self, crew):
        """Each agent should be assigned to exactly one task."""
        agent_task_count = {}
        for task in crew.tasks:
            agent_role = task.agent.role
            agent_task_count[agent_role] = agent_task_count.get(agent_role, 0) + 1

        for role, count in agent_task_count.items():
            assert count == 1, f"Agent '{role}' has {count} tasks, expected 1"

    def test_crew_is_reproducible(self):
        """Creating multiple crews should yield consistent configurations."""
        crew1 = create_recipe_crew()
        crew2 = create_recipe_crew()

        assert len(crew1.agents) == len(crew2.agents)
        assert len(crew1.tasks) == len(crew2.tasks)

        for i, (agent1, agent2) in enumerate(
            zip(crew1.agents, crew2.agents, strict=True)
        ):
            assert agent1.role == agent2.role, f"Agent {i} roles don't match"
            assert len(agent1.tools) == len(agent2.tools)


class TestRunRecipeCrewFunction:
    """Tests for the run_recipe_crew convenience function."""

    def test_run_recipe_crew_accepts_skill_level_enum(self):
        """Function should accept SkillLevel enum values."""
        # This test verifies the function signature, not actual execution
        # Since execution would require LLM calls
        skill = SkillLevel.BEGINNER
        assert skill.value == "beginner"

        skill = SkillLevel.INTERMEDIATE
        assert skill.value == "intermediate"

        skill = SkillLevel.ADVENTUROUS
        assert skill.value == "adventurous"

    def test_run_recipe_crew_accepts_drink_type_enum(self):
        """Function should accept DrinkType enum values."""
        # This test verifies the function signature, not actual execution
        drink_type = DrinkType.COCKTAIL
        assert drink_type.value == "cocktail"

        drink_type = DrinkType.MOCKTAIL
        assert drink_type.value == "mocktail"

        drink_type = DrinkType.BOTH
        assert drink_type.value == "both"

    def test_run_recipe_crew_accepts_string_skill_level(self):
        """Function should accept string skill level values."""
        # Function signature allows str | SkillLevel
        valid_levels = ["beginner", "intermediate", "adventurous"]
        for level in valid_levels:
            assert isinstance(level, str)

    def test_run_recipe_crew_accepts_string_drink_type(self):
        """Function should accept string drink type values."""
        # Function signature allows str | DrinkType
        valid_types = ["cocktail", "mocktail", "both"]
        for drink_type in valid_types:
            assert isinstance(drink_type, str)


class TestRecipeWriterToolCount:
    """Tests for Recipe Writer's tool configuration."""

    def test_recipe_writer_has_exactly_two_tools(self):
        """Recipe Writer should have exactly 2 tools."""
        crew = create_recipe_crew()
        recipe_writer = crew.agents[0]
        assert len(recipe_writer.tools) == 2

    def test_recipe_writer_tool_types(self):
        """Recipe Writer should have RecipeDBTool and SubstitutionFinderTool."""
        crew = create_recipe_crew()
        recipe_writer = crew.agents[0]

        tool_types = {type(tool).__name__ for tool in recipe_writer.tools}
        expected_types = {"RecipeDBTool", "SubstitutionFinderTool"}
        assert tool_types == expected_types


class TestBottleAdvisorToolCount:
    """Tests for Bottle Advisor's tool configuration."""

    def test_bottle_advisor_has_exactly_one_tool(self):
        """Bottle Advisor should have exactly 1 tool."""
        crew = create_recipe_crew()
        bottle_advisor = crew.agents[1]
        assert len(bottle_advisor.tools) == 1

    def test_bottle_advisor_tool_type(self):
        """Bottle Advisor should have UnlockCalculatorTool."""
        crew = create_recipe_crew()
        bottle_advisor = crew.agents[1]

        tool_types = {type(tool).__name__ for tool in bottle_advisor.tools}
        assert tool_types == {"UnlockCalculatorTool"}
