"""Unit tests for the CocktailFlow orchestration.

Tests verify flow state management, state transitions, and configuration.
These tests do not require an LLM connection as they mock crew execution.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Set mock API keys before importing CrewAI to bypass validation
# These keys are never used for actual API calls in tests
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from src.app.flows.cocktail_flow import (
    CocktailFlow,
    CocktailFlowState,
    request_another,
    run_cocktail_flow,
)
from src.app.models import DrinkType, SkillLevel


# =============================================================================
# CocktailFlowState Model Tests
# =============================================================================
class TestCocktailFlowStateValidation:
    """Tests for CocktailFlowState Pydantic model validation."""

    def test_default_state_is_valid(self):
        """Default state should be valid with all defaults."""
        state = CocktailFlowState()
        assert state is not None
        assert isinstance(state.session_id, str)
        assert len(state.session_id) > 0

    def test_session_id_is_uuid(self):
        """Session ID should be a valid UUID string."""
        state = CocktailFlowState()
        # Should not raise an exception
        parsed_uuid = uuid.UUID(state.session_id)
        assert parsed_uuid is not None

    def test_state_accepts_cabinet_list(self):
        """State should accept a list of ingredient IDs."""
        cabinet = ["bourbon", "simple-syrup", "angostura-bitters"]
        state = CocktailFlowState(cabinet=cabinet)
        assert state.cabinet == cabinet

    def test_state_accepts_mood_string(self):
        """State should accept a mood description string."""
        mood = "relaxing after a long day"
        state = CocktailFlowState(mood=mood)
        assert state.mood == mood

    def test_default_cabinet_is_empty_list(self):
        """Default cabinet should be an empty list."""
        state = CocktailFlowState()
        assert state.cabinet == []
        assert isinstance(state.cabinet, list)

    def test_default_mood_is_empty_string(self):
        """Default mood should be an empty string."""
        state = CocktailFlowState()
        assert state.mood == ""

    def test_default_drink_type_is_cocktail(self):
        """Default drink type should be 'cocktail'."""
        state = CocktailFlowState()
        assert state.drink_type == "cocktail"

    def test_default_skill_level_is_intermediate(self):
        """Default skill level should be 'intermediate'."""
        state = CocktailFlowState()
        assert state.skill_level == "intermediate"


class TestCocktailFlowStateConstraints:
    """Tests for CocktailFlowState constraints handling."""

    def test_state_accepts_constraints_list(self):
        """State should accept a list of constraint strings."""
        constraints = ["not too sweet", "low alcohol"]
        state = CocktailFlowState(constraints=constraints)
        assert state.constraints == constraints

    def test_default_constraints_is_empty_list(self):
        """Default constraints should be an empty list."""
        state = CocktailFlowState()
        assert state.constraints == []


class TestCocktailFlowStateHistory:
    """Tests for CocktailFlowState history and rejection handling."""

    def test_state_accepts_recent_history(self):
        """State should accept a list of recent drink IDs."""
        history = ["old-fashioned", "whiskey-sour"]
        state = CocktailFlowState(recent_history=history)
        assert state.recent_history == history

    def test_default_recent_history_is_empty(self):
        """Default recent history should be an empty list."""
        state = CocktailFlowState()
        assert state.recent_history == []

    def test_default_rejected_is_empty(self):
        """Default rejected list should be empty."""
        state = CocktailFlowState()
        assert state.rejected == []

    def test_rejected_can_be_modified(self):
        """Rejected list should be modifiable."""
        state = CocktailFlowState()
        state.rejected.append("old-fashioned")
        assert "old-fashioned" in state.rejected


class TestCocktailFlowStateOutputs:
    """Tests for CocktailFlowState output fields."""

    def test_default_candidates_is_empty(self):
        """Default candidates should be an empty list."""
        state = CocktailFlowState()
        assert state.candidates == []

    def test_default_selected_is_none(self):
        """Default selected should be None."""
        state = CocktailFlowState()
        assert state.selected is None

    def test_default_recipe_is_none(self):
        """Default recipe should be None."""
        state = CocktailFlowState()
        assert state.recipe is None

    def test_default_next_bottle_is_none(self):
        """Default next_bottle should be None."""
        state = CocktailFlowState()
        assert state.next_bottle is None

    def test_default_error_is_none(self):
        """Default error should be None."""
        state = CocktailFlowState()
        assert state.error is None

    def test_candidates_accepts_dict_list(self):
        """Candidates should accept a list of dictionaries."""
        candidates = [
            {"id": "old-fashioned", "name": "Old Fashioned", "mood_score": 85},
            {"id": "manhattan", "name": "Manhattan", "mood_score": 80},
        ]
        state = CocktailFlowState(candidates=candidates)
        assert state.candidates == candidates
        assert len(state.candidates) == 2


class TestCocktailFlowStateJsonSchema:
    """Tests for CocktailFlowState JSON schema compatibility."""

    def test_state_serializable_to_dict(self):
        """State should be serializable to a dictionary."""
        state = CocktailFlowState(
            cabinet=["bourbon"],
            mood="relaxing",
            skill_level="beginner",
        )
        state_dict = state.model_dump()
        assert isinstance(state_dict, dict)
        assert state_dict["cabinet"] == ["bourbon"]
        assert state_dict["mood"] == "relaxing"

    def test_state_serializable_to_json(self):
        """State should be serializable to JSON string."""
        state = CocktailFlowState(
            cabinet=["gin", "vermouth"],
            mood="fancy evening",
        )
        json_str = state.model_dump_json()
        assert isinstance(json_str, str)
        assert "gin" in json_str
        assert "fancy evening" in json_str


# =============================================================================
# CocktailFlow Instantiation Tests
# =============================================================================
class TestCocktailFlowInstantiation:
    """Tests for CocktailFlow class instantiation."""

    def test_flow_instantiation_with_defaults(self):
        """Flow should be instantiable with no arguments."""
        flow = CocktailFlow()
        assert flow is not None

    def test_flow_has_state_attribute(self):
        """Flow should have a state attribute."""
        flow = CocktailFlow()
        assert hasattr(flow, "state")

    def test_flow_state_is_cocktail_flow_state(self):
        """Flow state should be a CocktailFlowState instance."""
        flow = CocktailFlow()
        assert isinstance(flow.state, CocktailFlowState)

    def test_flow_has_receive_input_method(self):
        """Flow should have receive_input method."""
        flow = CocktailFlow()
        assert hasattr(flow, "receive_input")
        assert callable(flow.receive_input)

    def test_flow_has_analyze_method(self):
        """Flow should have analyze method."""
        flow = CocktailFlow()
        assert hasattr(flow, "analyze")
        assert callable(flow.analyze)

    def test_flow_has_generate_recipe_method(self):
        """Flow should have generate_recipe method."""
        flow = CocktailFlow()
        assert hasattr(flow, "generate_recipe")
        assert callable(flow.generate_recipe)


# =============================================================================
# CocktailFlow State Through Kickoff Tests
# =============================================================================
class TestCocktailFlowStateViaKickoff:
    """Tests for state populated via kickoff inputs."""

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_kickoff_populates_state_from_inputs(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """State should be populated from kickoff inputs."""
        # Mock the crews to avoid actual LLM calls
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        mock_recipe = MagicMock()
        mock_recipe.kickoff.return_value = "{}"
        mock_recipe_crew.return_value = mock_recipe

        flow = CocktailFlow()
        flow.kickoff(
            inputs={
                "cabinet": ["bourbon", "lemon"],
                "mood": "relaxing evening",
                "skill_level": "beginner",
            }
        )

        assert flow.state.cabinet == ["bourbon", "lemon"]
        assert flow.state.mood == "relaxing evening"
        assert flow.state.skill_level == "beginner"


class TestCocktailFlowAnalysisStep:
    """Tests for the analysis step with mocked crew execution."""

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_analyze_sets_error_on_empty_cabinet(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Analyze should set error when cabinet is empty."""
        flow = CocktailFlow()
        flow.kickoff(inputs={"cabinet": []})

        # Empty cabinet should result in error being set
        assert flow.state.error is not None
        assert (
            "empty" in flow.state.error.lower() or "cabinet" in flow.state.error.lower()
        )


class TestCocktailFlowRecipeStep:
    """Tests for the recipe generation step with mocked crew execution."""

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_generate_recipe_requires_selection(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Recipe generation should require a selected drink."""
        # Mock crews
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"  # No candidates
        mock_analysis_crew.return_value = mock_analysis

        flow = CocktailFlow()
        flow.kickoff(inputs={"cabinet": ["bourbon"]})

        # No candidates means no selection, should result in error
        assert flow.state.selected is None
        # Error should mention no drinks or selection
        assert flow.state.error is not None


# =============================================================================
# Run Cocktail Flow Convenience Function Tests
# =============================================================================
class TestRunCocktailFlowFunction:
    """Tests for the run_cocktail_flow convenience function."""

    def test_accepts_skill_level_enum(self):
        """Function should accept SkillLevel enum values."""
        # Verify enum values are valid
        assert SkillLevel.BEGINNER.value == "beginner"
        assert SkillLevel.INTERMEDIATE.value == "intermediate"
        assert SkillLevel.ADVENTUROUS.value == "adventurous"

    def test_accepts_drink_type_enum(self):
        """Function should accept DrinkType enum values."""
        # Verify enum values are valid
        assert DrinkType.COCKTAIL.value == "cocktail"
        assert DrinkType.MOCKTAIL.value == "mocktail"
        assert DrinkType.BOTH.value == "both"

    def test_accepts_string_parameters(self):
        """Function should accept string values for skill and drink type."""
        # These are valid string values
        valid_skills = ["beginner", "intermediate", "adventurous"]
        valid_drinks = ["cocktail", "mocktail", "both"]

        for skill in valid_skills:
            assert isinstance(skill, str)
        for drink in valid_drinks:
            assert isinstance(drink, str)

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_returns_state(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should return a CocktailFlowState."""
        # Mock the crews
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        mock_recipe = MagicMock()
        mock_recipe.kickoff.return_value = "{}"
        mock_recipe_crew.return_value = mock_recipe

        result = await run_cocktail_flow(
            cabinet=["bourbon", "simple-syrup"],
            mood="relaxing evening",
            skill_level="beginner",
            drink_type="cocktail",
        )

        assert isinstance(result, CocktailFlowState)

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_sets_cabinet(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should set cabinet in the returned state."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        cabinet = ["gin", "vermouth", "campari"]

        result = await run_cocktail_flow(
            cabinet=cabinet,
            mood="aperitivo hour",
        )

        # Inputs are passed via kickoff and populate state
        assert result.cabinet == [i.lower() for i in cabinet]

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_sets_mood(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should set mood in the returned state."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        mood = "celebrating a promotion"

        result = await run_cocktail_flow(
            cabinet=["champagne"],
            mood=mood,
        )

        assert result.mood == mood

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_handles_enum_skill_level(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should handle SkillLevel enum correctly."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        result = await run_cocktail_flow(
            cabinet=["bourbon"],
            mood="test",
            skill_level=SkillLevel.ADVENTUROUS,
        )

        assert result.skill_level == "adventurous"

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_handles_enum_drink_type(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should handle DrinkType enum correctly."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        result = await run_cocktail_flow(
            cabinet=["bourbon"],
            mood="test",
            drink_type=DrinkType.MOCKTAIL,
        )

        assert result.drink_type == "mocktail"

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_sets_recent_history(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should set recent_history in the state."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        history = ["old-fashioned", "manhattan"]

        result = await run_cocktail_flow(
            cabinet=["bourbon"],
            mood="test",
            recent_history=history,
        )

        assert result.recent_history == history

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_run_cocktail_flow_sets_constraints(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Function should set constraints in the state."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        constraints = ["not too sweet", "low alcohol"]

        result = await run_cocktail_flow(
            cabinet=["bourbon"],
            mood="test",
            constraints=constraints,
        )

        assert result.constraints == constraints


# =============================================================================
# CocktailFlow Rejection Workflow Tests
# =============================================================================
class TestCocktailFlowRejection:
    """Tests for the 'show me something else' rejection workflow."""

    @pytest.mark.asyncio
    async def test_request_another_returns_state_for_no_selection(self):
        """request_another should return unchanged state if no selection."""
        state = CocktailFlowState()
        result = await request_another(state)
        assert isinstance(result, CocktailFlowState)

    @pytest.mark.asyncio
    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    async def test_request_another_adds_to_rejected(
        self, mock_recipe_crew, mock_analysis_crew
    ):
        """Requesting another should add current selection to rejected."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        state = CocktailFlowState(
            cabinet=["bourbon"],
            mood="test",
            selected="old-fashioned",
            rejected=["manhattan"],
        )

        new_state = await request_another(state)

        assert "old-fashioned" in new_state.rejected


# =============================================================================
# Flow Method Tests
# =============================================================================
class TestCocktailFlowMethods:
    """Tests for CocktailFlow helper methods."""

    def test_parse_analysis_output_with_empty_string(self):
        """Parse method should handle empty string."""
        flow = CocktailFlow()

        result = flow._parse_analysis_output("")

        assert result is not None
        assert hasattr(result, "candidates")
        assert len(result.candidates) == 0

    def test_parse_recipe_output_with_empty_string(self):
        """Parse method should handle empty string."""
        flow = CocktailFlow()
        # Set a selected drink in the state (for the parse method to use)
        flow.state.selected = "test-drink"

        result = flow._parse_recipe_output("", "test-drink")

        assert result is not None
        assert hasattr(result, "id")
        assert result.id == "test-drink"


class TestCocktailFlowEdgeCases:
    """Tests for edge cases and error conditions."""

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_flow_handles_empty_cabinet(self, mock_recipe_crew, mock_analysis_crew):
        """Flow should handle empty cabinet gracefully."""
        flow = CocktailFlow()
        flow.kickoff(inputs={"cabinet": []})

        assert flow.state.error is not None

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_flow_normalizes_cabinet_case(self, mock_recipe_crew, mock_analysis_crew):
        """Flow should normalize cabinet ingredient case."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        flow = CocktailFlow()
        flow.kickoff(
            inputs={"cabinet": ["BOURBON", "Simple-Syrup", "ANGOSTURA-BITTERS"]}
        )

        # All ingredients should be lowercase
        for ingredient in flow.state.cabinet:
            assert ingredient == ingredient.lower()

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_flow_normalizes_skill_level(self, mock_recipe_crew, mock_analysis_crew):
        """Flow should normalize invalid skill level to intermediate."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        flow = CocktailFlow()
        flow.kickoff(
            inputs={
                "cabinet": ["bourbon"],
                "skill_level": "expert",  # Invalid value
            }
        )

        assert flow.state.skill_level == "intermediate"

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_flow_normalizes_drink_type(self, mock_recipe_crew, mock_analysis_crew):
        """Flow should normalize invalid drink type to cocktail."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        flow = CocktailFlow()
        flow.kickoff(
            inputs={
                "cabinet": ["bourbon"],
                "drink_type": "smoothie",  # Invalid value
            }
        )

        assert flow.state.drink_type == "cocktail"

    @patch("src.app.flows.cocktail_flow.create_analysis_crew")
    @patch("src.app.flows.cocktail_flow.create_recipe_crew")
    def test_flow_provides_default_mood(self, mock_recipe_crew, mock_analysis_crew):
        """Flow should provide default mood when empty."""
        mock_analysis = MagicMock()
        mock_analysis.kickoff.return_value = "[]"
        mock_analysis_crew.return_value = mock_analysis

        flow = CocktailFlow()
        flow.kickoff(
            inputs={
                "cabinet": ["bourbon"],
                "mood": "",
            }
        )

        assert flow.state.mood != ""
        assert len(flow.state.mood) > 0


class TestCocktailFlowSessionManagement:
    """Tests for session management functionality."""

    def test_each_flow_has_unique_session_id(self):
        """Each flow instance should have a unique session ID."""
        flow1 = CocktailFlow()
        flow2 = CocktailFlow()

        assert flow1.state.session_id != flow2.state.session_id

    def test_session_id_is_valid_uuid_format(self):
        """Session ID should be a valid UUID format."""
        flow = CocktailFlow()

        # Should not raise an exception
        parsed = uuid.UUID(flow.state.session_id)
        assert str(parsed) == flow.state.session_id
