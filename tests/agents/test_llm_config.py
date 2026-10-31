"""Tests for the LLM profile configuration in llm.yaml."""

from src.app.agents.config import get_llm_profile, load_llm_config


class TestLLMProfileModel:
    """The model ID is defined once and shared by every profile."""

    def test_all_profiles_share_default_model(self):
        """Every profile should resolve to the default profile's model."""
        default_model = get_llm_profile("default").model
        profiles = load_llm_config()

        assert profiles, "llm.yaml should define at least one profile"
        for name, profile in profiles.items():
            assert profile.model == default_model, name

    def test_default_model_is_not_a_retired_claude_3_id(self):
        """Claude 3.x model IDs are retired and must not be configured."""
        model = get_llm_profile("default").model

        assert model.startswith("anthropic/")
        assert "claude-3" not in model
