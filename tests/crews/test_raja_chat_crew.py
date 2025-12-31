"""Unit tests for the Raja Chat Crew.

Tests verify that the Raja Chat Crew is properly configured and that
session management, helper functions, and output parsing work correctly.
These tests do not require an LLM connection as they mock crew execution.
"""

import os
import uuid
from unittest.mock import MagicMock, patch

# Set mock API keys before importing CrewAI to bypass validation
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from crewai import Crew

from src.app.crews.raja_chat_crew import (
    _get_drink_by_id,
    _get_suggested_action,
    _parse_raja_output,
    create_raja_chat_crew,
    delete_session,
    get_or_create_session,
    get_session,
)
from src.app.models.chat import (
    ChatSession,
    MessageIntent,
    MessageRole,
    RajaChatOutput,
)


class TestGetOrCreateSession:
    """Tests for session management functions."""

    def setup_method(self):
        """Clear session store before each test."""
        from src.app.crews import raja_chat_crew

        raja_chat_crew._chat_sessions.clear()

    def test_creates_new_session_when_no_id_provided(self):
        """Should create a new session with defaults when session_id is None."""
        session = get_or_create_session(session_id=None)

        assert session is not None
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.cabinet == []
        assert session.skill_level == "intermediate"
        assert session.drink_type_preference == "cocktail"

    def test_creates_new_session_with_provided_context(self):
        """Should create session with provided cabinet, skill level, and drink type."""
        cabinet = ["bourbon", "sweet-vermouth", "angostura-bitters"]
        session = get_or_create_session(
            session_id=None,
            cabinet=cabinet,
            skill_level="beginner",
            drink_type="mocktail",
        )

        assert session.cabinet == cabinet
        assert session.skill_level == "beginner"
        assert session.drink_type_preference == "mocktail"

    def test_adds_greeting_message_to_new_session(self):
        """New session should have Raja's greeting as first message."""
        session = get_or_create_session(session_id=None)

        assert len(session.history.messages) == 1
        greeting = session.history.messages[0]
        assert greeting.role == MessageRole.RAJA
        assert "yaar" in greeting.content.lower()
        assert "AI" in greeting.content

    def test_returns_existing_session_when_found(self):
        """Should return existing session when valid session_id provided."""
        # Create initial session
        session1 = get_or_create_session(session_id=None, cabinet=["gin"])

        # Retrieve by ID
        session2 = get_or_create_session(session_id=session1.session_id)

        assert session2.session_id == session1.session_id
        assert session2.cabinet == ["gin"]

    def test_updates_last_active_on_existing_session(self):
        """Should update last_active when retrieving existing session."""
        session = get_or_create_session(session_id=None)
        original_time = session.last_active

        # Wait a tiny bit and retrieve again
        import time

        time.sleep(0.01)
        retrieved = get_or_create_session(session_id=session.session_id)

        assert retrieved.last_active >= original_time

    def test_updates_context_on_existing_session(self):
        """Should update cabinet, skill_level, drink_type when provided."""
        session = get_or_create_session(
            session_id=None, cabinet=["vodka"], skill_level="beginner"
        )

        # Update with new values
        updated = get_or_create_session(
            session_id=session.session_id,
            cabinet=["gin", "tonic"],
            skill_level="advanced",
            drink_type="both",
        )

        assert updated.cabinet == ["gin", "tonic"]
        assert updated.skill_level == "advanced"
        assert updated.drink_type_preference == "both"

    def test_creates_new_session_for_unknown_id(self):
        """Should create new session when session_id doesn't exist."""
        session = get_or_create_session(session_id="nonexistent-id-12345")

        # Session should be new (new ID, not the one provided)
        assert session.session_id != "nonexistent-id-12345"


class TestGetSession:
    """Tests for get_session function."""

    def setup_method(self):
        """Clear session store before each test."""
        from src.app.crews import raja_chat_crew

        raja_chat_crew._chat_sessions.clear()

    def test_returns_session_when_exists(self):
        """Should return session when it exists."""
        created = get_or_create_session(session_id=None, cabinet=["rum"])
        retrieved = get_session(created.session_id)

        assert retrieved is not None
        assert retrieved.session_id == created.session_id
        assert retrieved.cabinet == ["rum"]

    def test_returns_none_when_not_found(self):
        """Should return None when session doesn't exist."""
        result = get_session("nonexistent-session-id")
        assert result is None


class TestDeleteSession:
    """Tests for delete_session function."""

    def setup_method(self):
        """Clear session store before each test."""
        from src.app.crews import raja_chat_crew

        raja_chat_crew._chat_sessions.clear()

    def test_deletes_existing_session(self):
        """Should delete session and return True when it exists."""
        session = get_or_create_session(session_id=None)

        result = delete_session(session.session_id)

        assert result is True
        assert get_session(session.session_id) is None

    def test_returns_false_for_nonexistent_session(self):
        """Should return False when session doesn't exist."""
        result = delete_session("nonexistent-session-id")
        assert result is False


class TestGetDrinkById:
    """Tests for _get_drink_by_id helper function."""

    @patch("src.app.crews.raja_chat_crew.load_all_drinks")
    def test_returns_drink_when_found(self, mock_load):
        """Should return drink dict when ID matches."""
        mock_drink = MagicMock()
        mock_drink.id = "manhattan"
        mock_drink.name = "Manhattan"
        mock_drink.tagline = "Classic"
        mock_load.return_value = [mock_drink]

        result = _get_drink_by_id("manhattan")

        assert result is not None
        assert result["id"] == "manhattan"
        assert result["name"] == "Manhattan"

    @patch("src.app.crews.raja_chat_crew.load_all_drinks")
    def test_returns_none_when_not_found(self, mock_load):
        """Should return None when drink ID doesn't exist."""
        mock_drink = MagicMock()
        mock_drink.id = "other-drink"
        mock_load.return_value = [mock_drink]

        result = _get_drink_by_id("nonexistent-id")

        assert result is None


class TestCreateRajaChatCrew:
    """Tests for create_raja_chat_crew factory function."""

    def test_returns_crew_instance(self):
        """Should return a CrewAI Crew instance."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=["bourbon"],
            skill_level="intermediate",
        )

        crew = create_raja_chat_crew(session, "Hello!")

        assert isinstance(crew, Crew)

    def test_crew_has_single_agent(self):
        """Raja Chat Crew should have exactly 1 agent."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "Hi there")

        assert len(crew.agents) == 1

    def test_agent_is_raja_bartender(self):
        """The agent should be Raja Bartender."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "What should I drink?")
        agent = crew.agents[0]

        assert "Raja" in agent.role

    def test_crew_has_single_task(self):
        """Crew should have exactly 1 task."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "Recommend something")

        assert len(crew.tasks) == 1

    def test_task_description_includes_user_message(self):
        """Task description should include the user's message."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )
        user_message = "I want something refreshing"

        crew = create_raja_chat_crew(session, user_message)
        task = crew.tasks[0]

        assert user_message in task.description

    def test_task_description_includes_cabinet_info(self):
        """Task description should include cabinet information."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=["gin", "tonic", "lime"],
        )

        crew = create_raja_chat_crew(session, "What can I make?")
        task = crew.tasks[0]

        assert "gin" in task.description.lower() or "3 bottles" in task.description

    def test_task_description_includes_skill_level(self):
        """Task description should include user's skill level."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
            skill_level="beginner",
        )

        crew = create_raja_chat_crew(session, "Help me")
        task = crew.tasks[0]

        assert "beginner" in task.description.lower()

    def test_task_has_expected_output(self):
        """Task should have expected output defined."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "Hello")
        task = crew.tasks[0]

        assert task.expected_output is not None
        assert "JSON" in task.expected_output

    def test_agent_has_cocktail_tools(self):
        """Raja agent should have cocktail tools for dynamic data access."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "Hi")
        agent = crew.agents[0]

        # Raja has default tools (4) plus RecipeDBTool added by crew (1 duplicate)
        # Tools: recipe_database, substitution_finder, unlock_calculator, flavor_profiler
        assert len(agent.tools) >= 4
        tool_names = [t.name for t in agent.tools]
        assert "recipe_database" in tool_names
        assert "substitution_finder" in tool_names

    def test_crew_verbose_is_false(self):
        """Crew should have verbose=False."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            cabinet=[],
        )

        crew = create_raja_chat_crew(session, "Hello")

        assert crew.verbose is False


class TestParseRajaOutput:
    """Tests for _parse_raja_output function."""

    def test_parses_pydantic_output(self):
        """Should use pydantic output when available."""
        expected = RajaChatOutput(
            response="Arrey yaar, great choice!",
            detected_intent=MessageIntent.RECOMMENDATION_REQUEST,
        )
        mock_result = MagicMock()
        mock_result.pydantic = expected

        result = _parse_raja_output(mock_result)

        assert result.response == "Arrey yaar, great choice!"
        assert result.detected_intent == MessageIntent.RECOMMENDATION_REQUEST

    def test_parses_json_from_raw_output(self):
        """Should parse JSON from raw output when pydantic not available."""
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.raw = """
        Here is my response:
        {
            "response": "Bilkul, try the Manhattan!",
            "detected_intent": "recommendation_request",
            "recommendation_made": true
        }
        """

        result = _parse_raja_output(mock_result)

        assert result.response == "Bilkul, try the Manhattan!"
        assert result.detected_intent == MessageIntent.RECOMMENDATION_REQUEST
        assert result.recommendation_made is True

    def test_fallback_on_invalid_json(self):
        """Should return fallback response when JSON parsing fails."""
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.raw = "This is not valid JSON at all"

        result = _parse_raja_output(mock_result)

        assert result.response == "This is not valid JSON at all"
        assert result.detected_intent == MessageIntent.GENERAL_CHAT

    def test_fallback_on_empty_output(self):
        """Should return fallback response when output is empty."""
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.raw = ""

        result = _parse_raja_output(mock_result)

        assert "something went wrong" in result.response.lower()


class TestGetSuggestedAction:
    """Tests for _get_suggested_action function."""

    def test_returns_view_recipe_for_recommendation(self):
        """Should return 'view_recipe' when recommendation made."""
        output = RajaChatOutput(
            response="Try the Manhattan!",
            recommendation_made=True,
            recommended_drink_id="manhattan",
        )

        result = _get_suggested_action(output)

        assert result == "view_recipe"

    def test_returns_update_cabinet_for_cabinet_intent(self):
        """Should return 'update_cabinet' for cabinet update intent."""
        output = RajaChatOutput(
            response="Add some gin to your cabinet!",
            detected_intent=MessageIntent.CABINET_UPDATE,
        )

        result = _get_suggested_action(output)

        assert result == "update_cabinet"

    def test_returns_show_recommendations_for_recommendation_request(self):
        """Should return 'show_recommendations' for recommendation requests."""
        output = RajaChatOutput(
            response="Let me think what you can make...",
            detected_intent=MessageIntent.RECOMMENDATION_REQUEST,
            recommendation_made=False,
        )

        result = _get_suggested_action(output)

        assert result == "show_recommendations"

    def test_returns_none_for_general_chat(self):
        """Should return None for general chat without recommendations."""
        output = RajaChatOutput(
            response="Nice to chat with you!",
            detected_intent=MessageIntent.GENERAL_CHAT,
        )

        result = _get_suggested_action(output)

        assert result is None


class TestDrinkIdValidation:
    """Tests for drink ID validation in crew creation and run_raja_chat.

    Note: The actual validation of recommended_drink_id happens in run_raja_chat(),
    not in _parse_raja_output(). The _parse_raja_output function only parses the LLM
    output, while run_raja_chat validates the drink ID after parsing.
    """

    def test_parse_output_returns_drink_id_as_is(self):
        """_parse_raja_output should return drink ID without validation (validation happens later)."""
        mock_result = MagicMock()
        mock_result.pydantic = RajaChatOutput(
            response="Try the Fancy Drink!",
            detected_intent=MessageIntent.RECOMMENDATION_REQUEST,
            recommendation_made=True,
            recommended_drink_id="any-drink-id",  # This should pass through
        )

        result = _parse_raja_output(mock_result)

        # _parse_raja_output just parses - validation happens in run_raja_chat
        assert result.recommended_drink_id == "any-drink-id"

    def test_parse_output_handles_none_drink_id(self):
        """Should handle None recommended_drink_id gracefully."""
        mock_result = MagicMock()
        mock_result.pydantic = RajaChatOutput(
            response="Nice chatting!",
            detected_intent=MessageIntent.GENERAL_CHAT,
            recommendation_made=False,
            recommended_drink_id=None,  # No recommendation
        )

        result = _parse_raja_output(mock_result)

        # Should remain None
        assert result.recommended_drink_id is None


class TestTaskDescriptionContent:
    """Tests for content of task descriptions."""

    def test_description_includes_snappy_instruction(self):
        """Task description should instruct snappy 2-3 sentence responses."""
        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hello")
        description = crew.tasks[0].description.lower()

        assert "snappy" in description or "2-3 sentences" in description

    def test_description_includes_respectful_hindi_instruction(self):
        """Task description should instruct use of respectful Hindi."""
        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hello")
        description = crew.tasks[0].description.lower()

        assert "yaar" in description or "hindi" in description

    def test_description_includes_second_hand_stories_instruction(self):
        """Task description should instruct second-hand stories only."""
        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hello")
        description = crew.tasks[0].description.lower()

        assert "second-hand" in description or "legend" in description


class TestCrewConfiguration:
    """Tests for crew configuration options."""

    def test_crew_uses_sequential_process(self):
        """Crew should use sequential process."""
        from crewai import Process

        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hi")

        assert crew.process == Process.sequential

    def test_agent_verbose_is_false(self):
        """Agent should have verbose=False."""
        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hi")

        assert crew.agents[0].verbose is False

    def test_agent_allow_delegation_is_false(self):
        """Agent should have allow_delegation=False."""
        session = ChatSession(session_id=str(uuid.uuid4()), cabinet=[])
        crew = create_raja_chat_crew(session, "Hi")

        assert crew.agents[0].allow_delegation is False
