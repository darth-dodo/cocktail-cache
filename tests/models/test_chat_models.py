"""Unit tests for the chat Pydantic models.

Tests verify that all chat models for the Raja conversational interface
are properly configured with correct fields, validation, and behavior.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.app.models.chat import (
    ChatHistory,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSession,
    DrinkReference,
    MessageIntent,
    MessageRole,
    RajaChatOutput,
)


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_user_role_value(self):
        """USER role should have value 'user'."""
        assert MessageRole.USER.value == "user"

    def test_raja_role_value(self):
        """RAJA role should have value 'raja'."""
        assert MessageRole.RAJA.value == "raja"

    def test_system_role_value(self):
        """SYSTEM role should have value 'system'."""
        assert MessageRole.SYSTEM.value == "system"

    def test_role_is_string_enum(self):
        """MessageRole should be a string enum."""
        assert isinstance(MessageRole.USER, str)
        assert MessageRole.USER == "user"


class TestMessageIntent:
    """Tests for MessageIntent enum."""

    def test_all_intents_exist(self):
        """All expected intents should be defined."""
        expected = [
            "greeting",
            "recommendation_request",
            "recipe_question",
            "technique_question",
            "ingredient_question",
            "general_chat",
            "cabinet_update",
            "feedback",
            "goodbye",
        ]
        for intent in expected:
            assert hasattr(MessageIntent, intent.upper())

    def test_intent_is_string_enum(self):
        """MessageIntent should be a string enum."""
        assert isinstance(MessageIntent.GREETING, str)
        assert MessageIntent.GREETING == "greeting"


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_creates_message_with_required_fields(self):
        """Should create message with id, role, and content."""
        msg = ChatMessage(
            id="test-id",
            role=MessageRole.USER,
            content="Hello Raja!",
        )

        assert msg.id == "test-id"
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello Raja!"

    def test_timestamp_defaults_to_now(self):
        """Timestamp should default to current UTC time."""
        before = datetime.utcnow()
        msg = ChatMessage(
            id="test",
            role=MessageRole.USER,
            content="Test",
        )
        after = datetime.utcnow()

        assert before <= msg.timestamp <= after

    def test_intent_defaults_to_none(self):
        """Intent should default to None."""
        msg = ChatMessage(
            id="test",
            role=MessageRole.USER,
            content="Test",
        )

        assert msg.intent is None

    def test_accepts_intent(self):
        """Should accept intent value."""
        msg = ChatMessage(
            id="test",
            role=MessageRole.USER,
            content="What can I make?",
            intent=MessageIntent.RECOMMENDATION_REQUEST,
        )

        assert msg.intent == MessageIntent.RECOMMENDATION_REQUEST

    def test_metadata_defaults_to_empty_dict(self):
        """Metadata should default to empty dict."""
        msg = ChatMessage(
            id="test",
            role=MessageRole.USER,
            content="Test",
        )

        assert msg.metadata == {}

    def test_accepts_metadata(self):
        """Should accept metadata dict."""
        msg = ChatMessage(
            id="test",
            role=MessageRole.RAJA,
            content="Try the Manhattan!",
            metadata={"drinks_mentioned": ["manhattan"]},
        )

        assert msg.metadata == {"drinks_mentioned": ["manhattan"]}


class TestChatHistory:
    """Tests for ChatHistory model."""

    def test_creates_with_empty_messages(self):
        """Should create with empty message list by default."""
        history = ChatHistory()
        assert history.messages == []

    def test_default_max_messages(self):
        """Should have default max_messages of 50."""
        history = ChatHistory()
        assert history.max_messages == 50

    def test_add_message_appends_to_history(self):
        """add_message should append message to list."""
        history = ChatHistory()
        msg = ChatMessage(
            id="test",
            role=MessageRole.USER,
            content="Hello",
        )

        history.add_message(msg)

        assert len(history.messages) == 1
        assert history.messages[0].content == "Hello"

    def test_add_message_trims_when_over_limit(self):
        """add_message should trim old messages when over limit."""
        history = ChatHistory(max_messages=3)

        for i in range(5):
            msg = ChatMessage(
                id=f"msg-{i}",
                role=MessageRole.USER,
                content=f"Message {i}",
            )
            history.add_message(msg)

        assert len(history.messages) <= 3

    def test_add_message_preserves_system_messages(self):
        """add_message should preserve system messages when trimming."""
        history = ChatHistory(max_messages=3)

        system_msg = ChatMessage(
            id="system",
            role=MessageRole.SYSTEM,
            content="System message",
        )
        history.add_message(system_msg)

        # Add more messages than limit
        for i in range(5):
            msg = ChatMessage(
                id=f"user-{i}",
                role=MessageRole.USER,
                content=f"User message {i}",
            )
            history.add_message(msg)

        # System message should still be present
        system_msgs = [m for m in history.messages if m.role == MessageRole.SYSTEM]
        assert len(system_msgs) == 1

    def test_get_context_window_returns_last_n(self):
        """get_context_window should return last N messages."""
        history = ChatHistory()

        for i in range(10):
            msg = ChatMessage(
                id=f"msg-{i}",
                role=MessageRole.USER,
                content=f"Message {i}",
            )
            history.add_message(msg)

        context = history.get_context_window(last_n=3)

        assert len(context) == 3
        assert context[-1].content == "Message 9"

    def test_format_for_prompt_returns_string(self):
        """format_for_prompt should return formatted string."""
        history = ChatHistory()

        history.add_message(ChatMessage(id="1", role=MessageRole.USER, content="Hello"))
        history.add_message(
            ChatMessage(id="2", role=MessageRole.RAJA, content="Hi there!")
        )

        result = history.format_for_prompt(last_n=10)

        assert isinstance(result, str)
        assert "Customer:" in result
        assert "Raja:" in result

    def test_format_for_prompt_empty_history(self):
        """format_for_prompt should handle empty history."""
        history = ChatHistory()

        result = history.format_for_prompt()

        assert "No previous conversation" in result


class TestChatSession:
    """Tests for ChatSession model."""

    def test_creates_session_with_required_fields(self):
        """Should create session with session_id."""
        session = ChatSession(session_id="test-session-123")

        assert session.session_id == "test-session-123"

    def test_created_at_defaults_to_now(self):
        """created_at should default to current time."""
        before = datetime.utcnow()
        session = ChatSession(session_id="test")
        after = datetime.utcnow()

        assert before <= session.created_at <= after

    def test_last_active_defaults_to_now(self):
        """last_active should default to current time."""
        before = datetime.utcnow()
        session = ChatSession(session_id="test")
        after = datetime.utcnow()

        assert before <= session.last_active <= after

    def test_history_defaults_to_empty(self):
        """history should default to empty ChatHistory."""
        session = ChatSession(session_id="test")

        assert isinstance(session.history, ChatHistory)
        assert len(session.history.messages) == 0

    def test_cabinet_defaults_to_empty_list(self):
        """cabinet should default to empty list."""
        session = ChatSession(session_id="test")
        assert session.cabinet == []

    def test_skill_level_defaults_to_intermediate(self):
        """skill_level should default to 'intermediate'."""
        session = ChatSession(session_id="test")
        assert session.skill_level == "intermediate"

    def test_drink_type_preference_defaults_to_cocktail(self):
        """drink_type_preference should default to 'cocktail'."""
        session = ChatSession(session_id="test")
        assert session.drink_type_preference == "cocktail"

    def test_current_mood_defaults_to_none(self):
        """current_mood should default to None."""
        session = ChatSession(session_id="test")
        assert session.current_mood is None

    def test_mentioned_drinks_defaults_to_empty(self):
        """mentioned_drinks should default to empty list."""
        session = ChatSession(session_id="test")
        assert session.mentioned_drinks == []

    def test_mentioned_ingredients_defaults_to_empty(self):
        """mentioned_ingredients should default to empty list."""
        session = ChatSession(session_id="test")
        assert session.mentioned_ingredients == []


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_requires_message(self):
        """Should require message field."""
        with pytest.raises(ValidationError):
            ChatRequest()

    def test_creates_with_message(self):
        """Should create with just message."""
        request = ChatRequest(message="Hello Raja!")

        assert request.message == "Hello Raja!"
        assert request.session_id is None

    def test_message_min_length(self):
        """Message should have minimum length of 1."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_max_length(self):
        """Message should have maximum length of 2000."""
        long_message = "x" * 2001
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message)

    def test_accepts_session_id(self):
        """Should accept session_id."""
        request = ChatRequest(
            session_id="session-123",
            message="Continue our chat",
        )

        assert request.session_id == "session-123"

    def test_accepts_cabinet(self):
        """Should accept cabinet list."""
        request = ChatRequest(
            message="What can I make?",
            cabinet=["bourbon", "vermouth"],
        )

        assert request.cabinet == ["bourbon", "vermouth"]

    def test_accepts_skill_level(self):
        """Should accept skill_level."""
        request = ChatRequest(
            message="I'm new",
            skill_level="beginner",
        )

        assert request.skill_level == "beginner"

    def test_accepts_drink_type(self):
        """Should accept drink_type."""
        request = ChatRequest(
            message="No alcohol please",
            drink_type="mocktail",
        )

        assert request.drink_type == "mocktail"


class TestDrinkReference:
    """Tests for DrinkReference model."""

    def test_requires_id_and_name(self):
        """Should require id and name."""
        with pytest.raises(ValidationError):
            DrinkReference()

    def test_creates_with_id_and_name(self):
        """Should create with id and name."""
        ref = DrinkReference(id="manhattan", name="Manhattan")

        assert ref.id == "manhattan"
        assert ref.name == "Manhattan"

    def test_mentioned_reason_defaults_to_empty(self):
        """mentioned_reason should default to empty string."""
        ref = DrinkReference(id="test", name="Test")
        assert ref.mentioned_reason == ""


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_requires_core_fields(self):
        """Should require session_id, message_id, and content."""
        with pytest.raises(ValidationError):
            ChatResponse()

    def test_creates_with_required_fields(self):
        """Should create with required fields."""
        response = ChatResponse(
            session_id="session-123",
            message_id="msg-456",
            content="Arrey yaar, try the Manhattan!",
        )

        assert response.session_id == "session-123"
        assert response.message_id == "msg-456"
        assert response.content == "Arrey yaar, try the Manhattan!"

    def test_timestamp_defaults_to_now(self):
        """timestamp should default to current time."""
        response = ChatResponse(
            session_id="s",
            message_id="m",
            content="test",
        )

        assert response.timestamp is not None

    def test_drinks_mentioned_defaults_to_empty(self):
        """drinks_mentioned should default to empty list."""
        response = ChatResponse(
            session_id="s",
            message_id="m",
            content="test",
        )

        assert response.drinks_mentioned == []

    def test_ingredients_mentioned_defaults_to_empty(self):
        """ingredients_mentioned should default to empty list."""
        response = ChatResponse(
            session_id="s",
            message_id="m",
            content="test",
        )

        assert response.ingredients_mentioned == []

    def test_suggested_action_defaults_to_none(self):
        """suggested_action should default to None."""
        response = ChatResponse(
            session_id="s",
            message_id="m",
            content="test",
        )

        assert response.suggested_action is None

    def test_recommendation_offered_defaults_to_false(self):
        """recommendation_offered should default to False."""
        response = ChatResponse(
            session_id="s",
            message_id="m",
            content="test",
        )

        assert response.recommendation_offered is False


class TestRajaChatOutput:
    """Tests for RajaChatOutput model (agent task output)."""

    def test_requires_response(self):
        """Should require response field."""
        with pytest.raises(ValidationError):
            RajaChatOutput()

    def test_creates_with_response(self):
        """Should create with just response."""
        output = RajaChatOutput(response="Bilkul, great choice yaar!")

        assert output.response == "Bilkul, great choice yaar!"

    def test_detected_intent_defaults_to_general_chat(self):
        """detected_intent should default to GENERAL_CHAT."""
        output = RajaChatOutput(response="Test")

        assert output.detected_intent == MessageIntent.GENERAL_CHAT

    def test_detected_mood_defaults_to_none(self):
        """detected_mood should default to None."""
        output = RajaChatOutput(response="Test")

        assert output.detected_mood is None

    def test_drinks_mentioned_defaults_to_empty(self):
        """drinks_mentioned should default to empty list."""
        output = RajaChatOutput(response="Test")

        assert output.drinks_mentioned == []

    def test_ingredients_mentioned_defaults_to_empty(self):
        """ingredients_mentioned should default to empty list."""
        output = RajaChatOutput(response="Test")

        assert output.ingredients_mentioned == []

    def test_recommendation_made_defaults_to_false(self):
        """recommendation_made should default to False."""
        output = RajaChatOutput(response="Test")

        assert output.recommendation_made is False

    def test_recommended_drink_id_defaults_to_none(self):
        """recommended_drink_id should default to None."""
        output = RajaChatOutput(response="Test")

        assert output.recommended_drink_id is None

    def test_suggested_follow_up_defaults_to_none(self):
        """suggested_follow_up should default to None."""
        output = RajaChatOutput(response="Test")

        assert output.suggested_follow_up is None

    def test_accepts_all_fields(self):
        """Should accept all fields."""
        output = RajaChatOutput(
            response="Try the Manhattan!",
            detected_intent=MessageIntent.RECOMMENDATION_REQUEST,
            detected_mood="relaxed",
            drinks_mentioned=["manhattan"],
            ingredients_mentioned=["bourbon", "vermouth"],
            recommendation_made=True,
            recommended_drink_id="manhattan",
            suggested_follow_up="Want to know the history?",
        )

        assert output.response == "Try the Manhattan!"
        assert output.detected_intent == MessageIntent.RECOMMENDATION_REQUEST
        assert output.detected_mood == "relaxed"
        assert output.drinks_mentioned == ["manhattan"]
        assert output.ingredients_mentioned == ["bourbon", "vermouth"]
        assert output.recommendation_made is True
        assert output.recommended_drink_id == "manhattan"
        assert output.suggested_follow_up == "Want to know the history?"
