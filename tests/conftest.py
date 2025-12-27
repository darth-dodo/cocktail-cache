"""Pytest configuration and shared fixtures for Cocktail Cache tests."""

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import app


@pytest.fixture
def test_settings() -> Settings:
    """Provide test-specific settings."""
    return Settings(
        APP_ENV="development",
        DEBUG=True,
        ANTHROPIC_API_KEY="test-api-key",
    )


@pytest.fixture
def client() -> TestClient:
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_anthropic_response() -> dict:
    """Provide a mock Anthropic API response for testing."""
    return {
        "content": [
            {
                "type": "text",
                "text": "Here is a cocktail recommendation...",
            }
        ],
        "model": "claude-3-sonnet-20240229",
        "stop_reason": "end_turn",
    }


@pytest.fixture
def sample_cocktail_data() -> dict:
    """Provide sample cocktail data for testing."""
    return {
        "name": "Old Fashioned",
        "ingredients": [
            {"name": "Bourbon", "amount": "2 oz"},
            {"name": "Sugar", "amount": "1 cube"},
            {"name": "Angostura Bitters", "amount": "2 dashes"},
            {"name": "Orange peel", "amount": "1 twist"},
        ],
        "instructions": [
            "Muddle sugar cube with bitters and a splash of water",
            "Add bourbon and ice",
            "Stir until well-chilled",
            "Garnish with orange peel",
        ],
        "glass": "Old Fashioned glass",
        "category": "Classic",
    }


@pytest.fixture
def sample_user_preferences() -> dict:
    """Provide sample user preferences for testing."""
    return {
        "spirit_preferences": ["bourbon", "rye"],
        "flavor_profile": ["sweet", "aromatic"],
        "avoided_ingredients": ["vodka"],
        "experience_level": "intermediate",
    }
