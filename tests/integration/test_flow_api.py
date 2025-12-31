"""Integration tests for the unified /flow API endpoint.

Tests verify the complete request/response cycle for the flow endpoint
including START, ANOTHER, and MADE actions. These tests mock the underlying
flow functions to avoid AI API calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set mock API keys before importing modules that require them
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used-for-actual-calls")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-for-actual-calls")

from src.app.flows.cocktail_flow import CocktailFlowState
from src.app.main import app
from src.app.models import (
    DrinkType,
    FlavorProfile,
    RecipeOutput,
    SkillLevel,
)
from src.app.models.recipe import RecipeIngredient, RecipeStep

# Import from the new flow router location
from src.app.routers.flow import _sessions

# =============================================================================
# Helper Functions
# =============================================================================


def create_simple_recipe(
    recipe_id: str, name: str, tagline: str = "A classic cocktail"
) -> RecipeOutput:
    """Create a simple RecipeOutput for testing purposes."""
    return RecipeOutput(
        id=recipe_id,
        name=name,
        tagline=tagline,
        why="Perfect for testing",
        flavor_profile=FlavorProfile(sweet=30, sour=20, bitter=20, spirit=70),
        ingredients=[RecipeIngredient(amount="2", unit="oz", item="Spirit")],
        method=[RecipeStep(action="Mix", detail="and serve")],
        glassware="Rocks glass",
        garnish="None",
        timing="2 minutes",
        difficulty="easy",
    )


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def api_client() -> TestClient:
    """Provide FastAPI test client for API tests."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session storage before and after each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def mock_flow_state() -> CocktailFlowState:
    """Provide a mock CocktailFlowState for testing.

    This state represents a successful flow execution with:
    - A valid session ID
    - Cabinet with common ingredients
    - Two candidate drinks with mood scores
    - A selected drink (whiskey-sour)
    - A complete recipe using proper Pydantic model
    - A bottle recommendation
    """
    recipe = RecipeOutput(
        id="whiskey-sour",
        name="Whiskey Sour",
        tagline="A classic citrus cocktail with perfect balance",
        why="The bright citrus perfectly matches your relaxing mood",
        flavor_profile=FlavorProfile(sweet=40, sour=50, bitter=10, spirit=60),
        ingredients=[
            RecipeIngredient(amount="2", unit="oz", item="Bourbon"),
            RecipeIngredient(amount="0.75", unit="oz", item="Fresh lemon juice"),
            RecipeIngredient(amount="0.5", unit="oz", item="Simple syrup"),
        ],
        method=[
            RecipeStep(action="Combine", detail="all ingredients in a shaker"),
            RecipeStep(action="Shake", detail="with ice vigorously"),
            RecipeStep(action="Strain", detail="into a rocks glass over ice"),
        ],
        glassware="Rocks glass",
        garnish="Lemon wheel and cherry",
        timing="3 minutes",
        difficulty="easy",
    )
    return CocktailFlowState(
        session_id="test-session-123",
        cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
        mood="relaxing after work",
        skill_level=SkillLevel.INTERMEDIATE.value,
        drink_type=DrinkType.COCKTAIL.value,
        recent_history=[],
        constraints=[],
        candidates=[
            {"id": "whiskey-sour", "name": "Whiskey Sour", "mood_score": 90},
            {"id": "old-fashioned", "name": "Old Fashioned", "mood_score": 85},
        ],
        selected="whiskey-sour",
        recipe=recipe,
        next_bottle={
            "ingredient": "sweet-vermouth",
            "unlocks": 4,
            "drinks": ["Manhattan", "Boulevardier", "Rob Roy", "Negroni"],
        },
        error=None,
    )


@pytest.fixture
def mock_another_state() -> CocktailFlowState:
    """Provide a mock state for the ANOTHER action response."""
    recipe = RecipeOutput(
        id="old-fashioned",
        name="Old Fashioned",
        tagline="The classic that started it all",
        why="A timeless choice for relaxation",
        flavor_profile=FlavorProfile(sweet=30, sour=10, bitter=30, spirit=80),
        ingredients=[
            RecipeIngredient(amount="2", unit="oz", item="Bourbon"),
            RecipeIngredient(amount="0.25", unit="oz", item="Simple syrup"),
            RecipeIngredient(amount="2", unit="dashes", item="Angostura bitters"),
        ],
        method=[
            RecipeStep(action="Add", detail="all ingredients to a mixing glass"),
            RecipeStep(action="Stir", detail="with ice for 30 seconds"),
            RecipeStep(
                action="Strain", detail="into a rocks glass over a large ice cube"
            ),
        ],
        glassware="Rocks glass",
        garnish="Orange peel",
        timing="3 minutes",
        difficulty="easy",
    )
    return CocktailFlowState(
        session_id="test-session-123",
        cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
        mood="relaxing after work",
        skill_level=SkillLevel.INTERMEDIATE.value,
        drink_type=DrinkType.COCKTAIL.value,
        recent_history=[],
        constraints=[],
        rejected=["whiskey-sour"],
        candidates=[
            {"id": "old-fashioned", "name": "Old Fashioned", "mood_score": 85},
            {"id": "gold-rush", "name": "Gold Rush", "mood_score": 80},
        ],
        selected="old-fashioned",
        recipe=recipe,
        next_bottle={
            "ingredient": "angostura-bitters",
            "unlocks": 6,
        },
        error=None,
    )


@pytest.fixture
def mock_error_state() -> CocktailFlowState:
    """Provide a mock state representing a flow error."""
    return CocktailFlowState(
        session_id="test-session-error",
        cabinet=["water"],
        mood="testing",
        error="No drinks can be made with your current cabinet.",
    )


# =============================================================================
# START Action Tests
# =============================================================================


class TestStartFlowAction:
    """Tests for the START action of the /flow endpoint."""

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_success(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with valid cabinet creates session and returns recipe data."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons", "honey", "simple-syrup"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["session_id"] == "test-session-123"
        assert data["error"] is None

        # Verify recipe data
        assert data["recipe"] is not None
        assert data["recipe"]["id"] == "whiskey-sour"
        assert data["recipe"]["name"] == "Whiskey Sour"
        assert data["recipe"]["tagline"] is not None

        # Verify next bottle recommendation
        assert data["next_bottle"] is not None
        assert data["next_bottle"]["ingredient"] == "sweet-vermouth"
        assert data["next_bottle"]["unlocks"] == 4

        # Verify alternatives (candidates minus selected)
        assert data["alternatives"] is not None
        assert len(data["alternatives"]) == 1
        assert data["alternatives"][0]["id"] == "old-fashioned"

        # Verify flow was called with correct params
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["cabinet"] == [
            "bourbon",
            "lemons",
            "honey",
            "simple-syrup",
        ]

    def test_start_flow_empty_cabinet(self, api_client: TestClient):
        """START with empty cabinet returns 400 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": [],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "cabinet" in data["detail"].lower()
        assert "empty" in data["detail"].lower()

    def test_start_flow_missing_cabinet(self, api_client: TestClient):
        """START without cabinet field returns 400 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "cabinet" in data["detail"].lower()

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_with_mood(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with mood parameter passes it to the flow."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
                "mood": "celebrating a promotion",
            },
        )

        assert response.status_code == 200

        # Verify mood was passed to flow
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["mood"] == "celebrating a promotion"

    @pytest.mark.parametrize(
        "skill_level,expected_value",
        [
            ("beginner", SkillLevel.BEGINNER),
            ("intermediate", SkillLevel.INTERMEDIATE),
            ("adventurous", SkillLevel.ADVENTUROUS),
        ],
    )
    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_with_skill_level(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
        skill_level: str,
        expected_value: SkillLevel,
    ):
        """START with skill_level parameter handles all valid values."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
                "skill_level": skill_level,
            },
        )

        assert response.status_code == 200

        # Verify skill_level was passed correctly
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["skill_level"] == expected_value

    @pytest.mark.parametrize(
        "drink_type,expected_value",
        [
            ("cocktail", DrinkType.COCKTAIL),
            ("mocktail", DrinkType.MOCKTAIL),
            ("both", DrinkType.BOTH),
        ],
    )
    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_with_drink_type(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
        drink_type: str,
        expected_value: DrinkType,
    ):
        """START with drink_type parameter handles cocktail/mocktail/both."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
                "drink_type": drink_type,
            },
        )

        assert response.status_code == 200

        # Verify drink_type was passed correctly
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["drink_type"] == expected_value

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_with_recent_history(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with recent_history excludes previously made drinks."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
                "recent_history": ["old-fashioned", "manhattan"],
            },
        )

        assert response.status_code == 200

        # Verify recent_history was passed
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["recent_history"] == ["old-fashioned", "manhattan"]

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_with_constraints(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with constraints passes them to the flow."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
                "constraints": ["not too sweet", "low alcohol"],
            },
        )

        assert response.status_code == 200

        # Verify constraints were passed
        mock_run_flow.assert_called_once()
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["constraints"] == ["not too sweet", "low alcohol"]

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_error_state(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_error_state: CocktailFlowState,
    ):
        """START that results in error returns error in response."""
        mock_run_flow.return_value = mock_error_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["water"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify error is returned
        assert data["success"] is False
        assert data["error"] is not None
        assert "cabinet" in data["error"].lower()
        assert data["recipe"] is None

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_flow_stores_session(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START stores session state for future ANOTHER/MADE calls."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]

        # Verify session was stored
        assert session_id in _sessions
        assert _sessions[session_id].selected == "whiskey-sour"


# =============================================================================
# ANOTHER Action Tests
# =============================================================================


class TestAnotherFlowAction:
    """Tests for the ANOTHER action of the /flow endpoint."""

    @patch("src.app.routers.flow.request_another")
    def test_another_success(
        self,
        mock_request_another: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
        mock_another_state: CocktailFlowState,
    ):
        """ANOTHER with valid session_id returns new recommendation."""
        # First, store a session
        _sessions["test-session-123"] = mock_flow_state
        mock_request_another.return_value = mock_another_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": "test-session-123",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify new recommendation
        assert data["success"] is True
        assert data["recipe"]["id"] == "old-fashioned"
        assert data["recipe"]["name"] == "Old Fashioned"
        assert data["message"] == "Here's another recommendation"

        # Verify request_another was called with current state
        mock_request_another.assert_called_once_with(mock_flow_state)

    def test_another_missing_session_id(self, api_client: TestClient):
        """ANOTHER without session_id returns 400 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "session_id" in data["detail"].lower()

    def test_another_invalid_session_id(self, api_client: TestClient):
        """ANOTHER with non-existent session_id returns 404 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": "non-existent-session-xyz",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "session" in data["detail"].lower()
        assert "not found" in data["detail"].lower()

    @patch("src.app.routers.flow.request_another")
    def test_another_updates_session_state(
        self,
        mock_request_another: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
        mock_another_state: CocktailFlowState,
    ):
        """ANOTHER updates the stored session state."""
        _sessions["test-session-123"] = mock_flow_state
        mock_request_another.return_value = mock_another_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": "test-session-123",
            },
        )

        assert response.status_code == 200

        # Verify session state was updated
        updated_session = _sessions["test-session-123"]
        assert updated_session.selected == "old-fashioned"
        assert "whiskey-sour" in updated_session.rejected


# =============================================================================
# MADE Action Tests
# =============================================================================


class TestMadeFlowAction:
    """Tests for the MADE action of the /flow endpoint."""

    def test_made_success(
        self, api_client: TestClient, mock_flow_state: CocktailFlowState
    ):
        """MADE records drink in history and returns success."""
        _sessions["test-session-123"] = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "test-session-123",
                "drink_id": "whiskey-sour",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify success response
        assert data["success"] is True
        assert "whiskey-sour" in data["message"]
        assert "excluded" in data["message"].lower()

        # Verify drink was added to history
        assert "whiskey-sour" in _sessions["test-session-123"].recent_history

    def test_made_missing_session_id(self, api_client: TestClient):
        """MADE without session_id returns 400 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "drink_id": "whiskey-sour",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "session_id" in data["detail"].lower()

    def test_made_missing_drink_id(
        self, api_client: TestClient, mock_flow_state: CocktailFlowState
    ):
        """MADE without drink_id returns 400 error."""
        _sessions["test-session-123"] = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "test-session-123",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "drink_id" in data["detail"].lower()

    def test_made_invalid_session_id(self, api_client: TestClient):
        """MADE with non-existent session_id returns 404 error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "non-existent-session-xyz",
                "drink_id": "whiskey-sour",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "session" in data["detail"].lower()
        assert "not found" in data["detail"].lower()

    def test_made_prevents_duplicate_history(
        self, api_client: TestClient, mock_flow_state: CocktailFlowState
    ):
        """MADE does not add duplicate entries to history."""
        mock_flow_state.recent_history = ["whiskey-sour"]
        _sessions["test-session-123"] = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "test-session-123",
                "drink_id": "whiskey-sour",
            },
        )

        assert response.status_code == 200

        # Verify no duplicate was added
        history = _sessions["test-session-123"].recent_history
        assert history.count("whiskey-sour") == 1

    def test_made_adds_new_drink_to_history(
        self, api_client: TestClient, mock_flow_state: CocktailFlowState
    ):
        """MADE adds a new drink to existing history."""
        mock_flow_state.recent_history = ["old-fashioned"]
        _sessions["test-session-123"] = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "test-session-123",
                "drink_id": "whiskey-sour",
            },
        )

        assert response.status_code == 200

        # Verify both drinks are in history
        history = _sessions["test-session-123"].recent_history
        assert "old-fashioned" in history
        assert "whiskey-sour" in history
        assert len(history) == 2


# =============================================================================
# Complete Flow Integration Tests
# =============================================================================


class TestCompleteFlowIntegration:
    """Tests for complete START -> ANOTHER -> MADE flow sequences."""

    @patch("src.app.routers.flow.request_another")
    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_complete_flow_sequence(
        self,
        mock_run_flow: MagicMock,
        mock_request_another: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
        mock_another_state: CocktailFlowState,
    ):
        """Complete flow: START -> ANOTHER -> MADE sequence works correctly."""
        mock_run_flow.return_value = mock_flow_state
        mock_request_another.return_value = mock_another_state

        # Step 1: START
        start_response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons", "honey"],
                "mood": "relaxing",
            },
        )

        assert start_response.status_code == 200
        start_data = start_response.json()
        session_id = start_data["session_id"]

        assert start_data["success"] is True
        assert start_data["recipe"]["id"] == "whiskey-sour"

        # Step 2: ANOTHER (user wants a different drink)
        another_response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": session_id,
            },
        )

        assert another_response.status_code == 200
        another_data = another_response.json()

        assert another_data["success"] is True
        assert another_data["recipe"]["id"] == "old-fashioned"

        # Step 3: MADE (user made the second recommendation)
        made_response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": session_id,
                "drink_id": "old-fashioned",
            },
        )

        assert made_response.status_code == 200
        made_data = made_response.json()

        assert made_data["success"] is True
        assert "old-fashioned" in made_data["message"]

        # Verify final session state
        final_state = _sessions[session_id]
        assert "old-fashioned" in final_state.recent_history

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_then_made_without_another(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """User can mark first recommendation as made without requesting another."""
        mock_run_flow.return_value = mock_flow_state

        # Step 1: START
        start_response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
            },
        )

        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Step 2: MADE (user likes and makes the first recommendation)
        made_response = api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": session_id,
                "drink_id": "whiskey-sour",
            },
        )

        assert made_response.status_code == 200
        assert made_response.json()["success"] is True

    @patch("src.app.routers.flow.request_another")
    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_multiple_another_requests(
        self,
        mock_run_flow: MagicMock,
        mock_request_another: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """User can request multiple alternatives before making a decision."""
        mock_run_flow.return_value = mock_flow_state

        # Create different states for each ANOTHER call
        second_recommendation = CocktailFlowState(
            session_id="test-session-123",
            cabinet=["bourbon", "lemons"],
            selected="old-fashioned",
            recipe=create_simple_recipe("old-fashioned", "Old Fashioned"),
            rejected=["whiskey-sour"],
        )
        third_recommendation = CocktailFlowState(
            session_id="test-session-123",
            cabinet=["bourbon", "lemons"],
            selected="gold-rush",
            recipe=create_simple_recipe("gold-rush", "Gold Rush"),
            rejected=["whiskey-sour", "old-fashioned"],
        )

        mock_request_another.side_effect = [second_recommendation, third_recommendation]

        # START
        start_response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "lemons"],
            },
        )
        session_id = start_response.json()["session_id"]

        # First ANOTHER
        another1_response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": session_id,
            },
        )
        assert another1_response.status_code == 200
        assert another1_response.json()["recipe"]["id"] == "old-fashioned"

        # Second ANOTHER
        another2_response = api_client.post(
            "/api/flow",
            json={
                "action": "ANOTHER",
                "session_id": session_id,
            },
        )
        assert another2_response.status_code == 200
        assert another2_response.json()["recipe"]["id"] == "gold-rush"


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestFlowEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_action_returns_validation_error(self, api_client: TestClient):
        """Invalid action value returns validation error."""
        response = api_client.post(
            "/api/flow",
            json={
                "action": "INVALID_ACTION",
                "cabinet": ["bourbon"],
            },
        )

        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_with_all_optional_params(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with all optional parameters works correctly."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "vermouth", "bitters"],
                "mood": "sophisticated evening",
                "skill_level": "adventurous",
                "drink_type": "both",
                "recent_history": ["martini", "manhattan"],
                "constraints": ["not too sweet", "stirred not shaken"],
            },
        )

        assert response.status_code == 200

        # Verify all params were passed
        call_args = mock_run_flow.call_args
        assert call_args.kwargs["cabinet"] == ["bourbon", "vermouth", "bitters"]
        assert call_args.kwargs["mood"] == "sophisticated evening"
        assert call_args.kwargs["skill_level"] == SkillLevel.ADVENTUROUS
        assert call_args.kwargs["drink_type"] == DrinkType.BOTH
        assert call_args.kwargs["recent_history"] == ["martini", "manhattan"]
        assert call_args.kwargs["constraints"] == [
            "not too sweet",
            "stirred not shaken",
        ]

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_start_with_single_ingredient_cabinet(
        self,
        mock_run_flow: MagicMock,
        api_client: TestClient,
        mock_flow_state: CocktailFlowState,
    ):
        """START with single ingredient cabinet is accepted."""
        mock_run_flow.return_value = mock_flow_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon"],
            },
        )

        assert response.status_code == 200
        mock_run_flow.assert_called_once()

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_recipe_structured_output(
        self, mock_run_flow: MagicMock, api_client: TestClient
    ):
        """Recipe with structured RecipeOutput is properly converted."""
        recipe = create_simple_recipe(
            "custom-drink", "Custom Drink", "A simple test drink"
        )
        raw_state = CocktailFlowState(
            session_id="test-structured-recipe",
            cabinet=["bourbon"],
            selected="custom-drink",
            recipe=recipe,
        )
        mock_run_flow.return_value = raw_state

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recipe"]["id"] == "custom-drink"
        assert data["recipe"]["name"] == "Custom Drink"
        assert data["recipe"]["tagline"] == "A simple test drink"

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_response_without_next_bottle(
        self, mock_run_flow: MagicMock, api_client: TestClient
    ):
        """Response without next_bottle recommendation is valid."""
        state_no_bottle = CocktailFlowState(
            session_id="test-no-bottle",
            cabinet=["bourbon", "vermouth", "bitters", "sugar"],
            selected="manhattan",
            recipe=create_simple_recipe("manhattan", "Manhattan"),
            next_bottle=None,  # No recommendation needed
        )
        mock_run_flow.return_value = state_no_bottle

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon", "vermouth", "bitters", "sugar"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["next_bottle"] is None

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_response_without_alternatives(
        self, mock_run_flow: MagicMock, api_client: TestClient
    ):
        """Response with only one candidate has no alternatives."""
        state_single = CocktailFlowState(
            session_id="test-single",
            cabinet=["bourbon"],
            selected="bourbon-neat",
            recipe=create_simple_recipe("bourbon-neat", "Bourbon Neat"),
            candidates=[{"id": "bourbon-neat", "name": "Bourbon Neat"}],
        )
        mock_run_flow.return_value = state_single

        response = api_client.post(
            "/api/flow",
            json={
                "action": "START",
                "cabinet": ["bourbon"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Empty list after removing selected
        assert data["alternatives"] is None or len(data["alternatives"]) == 0


# =============================================================================
# Session Management Tests
# =============================================================================


class TestSessionManagement:
    """Tests for session storage and lifecycle."""

    @patch("src.app.routers.flow.run_cocktail_flow")
    def test_multiple_sessions_are_independent(
        self, mock_run_flow: MagicMock, api_client: TestClient
    ):
        """Multiple concurrent sessions are stored independently."""
        # Create two different states
        state1 = CocktailFlowState(
            session_id="session-1",
            cabinet=["bourbon"],
            selected="old-fashioned",
        )
        state2 = CocktailFlowState(
            session_id="session-2",
            cabinet=["gin"],
            selected="martini",
        )

        mock_run_flow.side_effect = [state1, state2]

        # Start first session
        response1 = api_client.post(
            "/api/flow",
            json={"action": "START", "cabinet": ["bourbon"]},
        )
        session1_id = response1.json()["session_id"]

        # Start second session
        response2 = api_client.post(
            "/api/flow",
            json={"action": "START", "cabinet": ["gin"]},
        )
        session2_id = response2.json()["session_id"]

        # Verify both sessions exist and are independent
        assert session1_id in _sessions
        assert session2_id in _sessions
        assert _sessions[session1_id].selected == "old-fashioned"
        assert _sessions[session2_id].selected == "martini"

    def test_made_on_one_session_does_not_affect_another(self, api_client: TestClient):
        """MADE action on one session does not affect other sessions."""
        # Create two sessions directly
        state1 = CocktailFlowState(
            session_id="session-1",
            cabinet=["bourbon"],
            recent_history=[],
        )
        state2 = CocktailFlowState(
            session_id="session-2",
            cabinet=["gin"],
            recent_history=[],
        )
        _sessions["session-1"] = state1
        _sessions["session-2"] = state2

        # Mark drink as made in session 1
        api_client.post(
            "/api/flow",
            json={
                "action": "MADE",
                "session_id": "session-1",
                "drink_id": "old-fashioned",
            },
        )

        # Verify only session 1 was affected
        assert "old-fashioned" in _sessions["session-1"].recent_history
        assert "old-fashioned" not in _sessions["session-2"].recent_history
