"""Unit tests for the Analysis Crew configuration.

Tests verify that the Analysis Crew is properly configured with the
correct agents, tasks, and tool assignments. These tests do not
require an LLM connection as they only test object configuration.

Note: The analysis crew supports two modes:
- Fast mode (default): Single unified agent for ~50% faster response
- Full mode: Two sequential agents for more detailed analysis

Most tests use full mode (fast_mode=False) to test the two-agent configuration.
"""

import os

import pytest

# Set mock API keys before importing CrewAI to bypass validation
# These keys are never used for actual API calls in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from crewai import Agent, Crew, Task

from src.app.crews.analysis_crew import create_analysis_crew


class TestCreateAnalysisCrew:
    """Tests for the create_analysis_crew factory function."""

    def test_create_analysis_crew_returns_crew(self):
        """Factory should return a CrewAI Crew instance."""
        crew = create_analysis_crew(fast_mode=False)
        assert isinstance(crew, Crew)

    def test_crew_has_correct_number_of_agents(self):
        """Analysis Crew (full mode) should have exactly 2 agents."""
        crew = create_analysis_crew(fast_mode=False)
        assert len(crew.agents) == 2

    def test_crew_has_cabinet_analyst_agent(self):
        """Crew (full mode) should include a Cabinet Analyst agent."""
        crew = create_analysis_crew(fast_mode=False)
        roles = [agent.role for agent in crew.agents]
        assert "Cabinet Analyst" in roles

    def test_crew_has_mood_matcher_agent(self):
        """Crew (full mode) should include a Mood Matcher agent."""
        crew = create_analysis_crew(fast_mode=False)
        roles = [agent.role for agent in crew.agents]
        assert "Mood Matcher" in roles

    def test_agents_are_in_correct_order(self):
        """Cabinet Analyst should be first, Mood Matcher second."""
        crew = create_analysis_crew(fast_mode=False)
        assert crew.agents[0].role == "Cabinet Analyst"
        assert crew.agents[1].role == "Mood Matcher"


class TestAnalysisCrewFastMode:
    """Tests for the fast mode (single agent) crew configuration."""

    def test_fast_mode_is_default(self):
        """Fast mode should be the default behavior."""
        crew = create_analysis_crew()
        # Fast mode uses a single unified agent
        assert len(crew.agents) == 1

    def test_fast_mode_has_single_agent(self):
        """Fast mode crew should have exactly 1 agent."""
        crew = create_analysis_crew(fast_mode=True)
        assert len(crew.agents) == 1

    def test_fast_mode_agent_is_drink_recommender(self):
        """Fast mode should use the Drink Recommender agent."""
        crew = create_analysis_crew(fast_mode=True)
        assert crew.agents[0].role == "Drink Recommender"

    def test_fast_mode_has_single_task(self):
        """Fast mode crew should have exactly 1 task."""
        crew = create_analysis_crew(fast_mode=True)
        assert len(crew.tasks) == 1

    def test_fast_mode_agent_has_no_tools(self):
        """Fast mode agent should have no tools (data is pre-injected into prompts)."""
        crew = create_analysis_crew(fast_mode=True)
        agent = crew.agents[0]
        assert len(agent.tools) == 0


class TestAnalysisCrewTasks:
    """Tests for Analysis Crew task configuration (full mode)."""

    def test_crew_has_correct_number_of_tasks(self):
        """Analysis Crew (full mode) should have exactly 2 tasks."""
        crew = create_analysis_crew(fast_mode=False)
        assert len(crew.tasks) == 2

    def test_first_task_assigned_to_cabinet_analyst(self):
        """First task should be assigned to Cabinet Analyst."""
        crew = create_analysis_crew(fast_mode=False)
        first_task = crew.tasks[0]
        assert first_task.agent.role == "Cabinet Analyst"

    def test_second_task_assigned_to_mood_matcher(self):
        """Second task should be assigned to Mood Matcher."""
        crew = create_analysis_crew(fast_mode=False)
        second_task = crew.tasks[1]
        assert second_task.agent.role == "Mood Matcher"

    def test_second_task_depends_on_first(self):
        """Match task should have analyze task as context (dependency)."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]
        match_task = crew.tasks[1]

        # The match_task should have context that includes analyze_task
        assert match_task.context is not None
        assert len(match_task.context) >= 1
        # Check that the first task (analyze) is in the context
        assert analyze_task in match_task.context

    def test_first_task_has_no_context(self):
        """Analyze task should not depend on any other task."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]

        # First task should have no context (no dependencies)
        # CrewAI uses _NotSpecified sentinel for unset context
        context = analyze_task.context
        if context is None:
            assert True  # No context, as expected
        elif hasattr(context, "__len__"):
            assert len(context) == 0
        else:
            # _NotSpecified or similar sentinel - treat as no context
            assert True

    def test_tasks_are_task_instances(self):
        """All tasks should be CrewAI Task instances."""
        crew = create_analysis_crew(fast_mode=False)
        for task in crew.tasks:
            assert isinstance(task, Task)


class TestAnalysisCrewToolFreeArchitecture:
    """Tests verifying tool-free architecture (data is pre-injected into prompts)."""

    def test_cabinet_analyst_has_no_tools(self):
        """Cabinet Analyst should have no tools (data is pre-injected)."""
        crew = create_analysis_crew(fast_mode=False)
        cabinet_analyst = crew.agents[0]
        assert cabinet_analyst.role == "Cabinet Analyst"
        assert len(cabinet_analyst.tools) == 0

    def test_mood_matcher_has_no_tools(self):
        """Mood Matcher should have no tools (data is pre-injected)."""
        crew = create_analysis_crew(fast_mode=False)
        mood_matcher = crew.agents[1]
        assert mood_matcher.role == "Mood Matcher"
        assert len(mood_matcher.tools) == 0

    def test_all_agents_are_tool_free(self):
        """All agents should have no tools in tool-free architecture."""
        crew = create_analysis_crew(fast_mode=False)
        for agent in crew.agents:
            assert len(agent.tools) == 0, f"Agent '{agent.role}' should have no tools"


class TestAnalysisCrewConfiguration:
    """Tests for Analysis Crew configuration options."""

    def test_crew_verbose_is_false(self):
        """Crew should have verbose=False for clean output."""
        crew = create_analysis_crew(fast_mode=False)
        assert crew.verbose is False

    def test_all_agents_have_verbose_false(self):
        """All agents in the crew should have verbose=False."""
        crew = create_analysis_crew(fast_mode=False)
        for agent in crew.agents:
            assert agent.verbose is False

    def test_all_agents_have_allow_delegation_false(self):
        """All agents should have allow_delegation=False."""
        crew = create_analysis_crew(fast_mode=False)
        for agent in crew.agents:
            assert agent.allow_delegation is False

    def test_agents_are_agent_instances(self):
        """All agents should be CrewAI Agent instances."""
        crew = create_analysis_crew(fast_mode=False)
        for agent in crew.agents:
            assert isinstance(agent, Agent)


class TestAnalysisCrewTaskDescriptions:
    """Tests for task description content (full mode)."""

    def test_analyze_task_mentions_cabinet(self):
        """Analyze task description should mention cabinet."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]
        description_lower = analyze_task.description.lower()
        assert "cabinet" in description_lower

    def test_analyze_task_mentions_drinks(self):
        """Analyze task description should mention drinks."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]
        description_lower = analyze_task.description.lower()
        assert "drink" in description_lower

    def test_match_task_mentions_mood(self):
        """Match task description should mention mood."""
        crew = create_analysis_crew(fast_mode=False)
        match_task = crew.tasks[1]
        description_lower = match_task.description.lower()
        assert "mood" in description_lower

    def test_match_task_mentions_skill_level(self):
        """Match task description should mention skill level."""
        crew = create_analysis_crew(fast_mode=False)
        match_task = crew.tasks[1]
        description_lower = match_task.description.lower()
        assert "skill" in description_lower

    def test_match_task_mentions_ranking(self):
        """Match task description should mention ranking."""
        crew = create_analysis_crew(fast_mode=False)
        match_task = crew.tasks[1]
        description_lower = match_task.description.lower()
        assert "rank" in description_lower


class TestAnalysisCrewExpectedOutputs:
    """Tests for task expected output specifications (full mode)."""

    def test_analyze_task_has_expected_output(self):
        """Analyze task should have an expected output defined."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]
        assert analyze_task.expected_output is not None
        assert len(analyze_task.expected_output) > 0

    def test_match_task_has_expected_output(self):
        """Match task should have an expected output defined."""
        crew = create_analysis_crew(fast_mode=False)
        match_task = crew.tasks[1]
        assert match_task.expected_output is not None
        assert len(match_task.expected_output) > 0

    def test_analyze_expected_output_mentions_json(self):
        """Analyze task expected output should mention JSON format."""
        crew = create_analysis_crew(fast_mode=False)
        analyze_task = crew.tasks[0]
        output_lower = analyze_task.expected_output.lower()
        assert "json" in output_lower

    def test_match_expected_output_mentions_ranked(self):
        """Match task expected output should mention ranked/ordered results."""
        crew = create_analysis_crew(fast_mode=False)
        match_task = crew.tasks[1]
        output_lower = match_task.expected_output.lower()
        assert "rank" in output_lower or "order" in output_lower


class TestAnalysisCrewConsistency:
    """Cross-component consistency tests for Analysis Crew."""

    @pytest.fixture
    def crew(self):
        """Provide a crew instance for tests."""
        return create_analysis_crew(fast_mode=False)

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
        crew1 = create_analysis_crew(fast_mode=False)
        crew2 = create_analysis_crew(fast_mode=False)

        assert len(crew1.agents) == len(crew2.agents)
        assert len(crew1.tasks) == len(crew2.tasks)

        for i, (agent1, agent2) in enumerate(
            zip(crew1.agents, crew2.agents, strict=True)
        ):
            assert agent1.role == agent2.role, f"Agent {i} roles don't match"
            assert len(agent1.tools) == len(agent2.tools)
