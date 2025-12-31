"""Tests for the parsing utility module.

Tests for:
- parse_json_from_llm_output: Extract and parse JSON from LLM raw output
"""

import logging

import pytest
from pydantic import BaseModel, Field

from src.app.utils.parsing import parse_json_from_llm_output

# =============================================================================
# Test Models
# =============================================================================


class SimpleModel(BaseModel):
    """Simple Pydantic model for testing."""

    name: str
    value: int


class ComplexModel(BaseModel):
    """Complex Pydantic model with optional fields for testing."""

    id: str
    title: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class NestedModel(BaseModel):
    """Model with nested structure for testing."""

    outer_name: str
    inner: SimpleModel


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def test_logger() -> logging.Logger:
    """Provide a logger for testing."""
    return logging.getLogger("test_parsing")


# =============================================================================
# Tests: Successful Parsing
# =============================================================================


class TestSuccessfulParsing:
    """Tests for successful JSON parsing scenarios."""

    def test_parse_simple_json(self, test_logger: logging.Logger):
        """Parse a simple JSON object from clean output."""
        raw_output = '{"name": "test", "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "test"
        assert result.value == 42

    def test_parse_json_with_surrounding_text(self, test_logger: logging.Logger):
        """Parse JSON embedded in surrounding text."""
        raw_output = """
        Here is my response:
        {"name": "embedded", "value": 123}
        I hope this helps!
        """

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "embedded"
        assert result.value == 123

    def test_parse_json_with_markdown_code_block(self, test_logger: logging.Logger):
        """Parse JSON from markdown code block."""
        raw_output = """
        Here's the JSON:
        ```json
        {"name": "markdown", "value": 456}
        ```
        """

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "markdown"
        assert result.value == 456

    def test_parse_complex_model(self, test_logger: logging.Logger):
        """Parse JSON into a complex model with optional fields."""
        raw_output = """
        {
            "id": "abc-123",
            "title": "Test Title",
            "description": "A test description",
            "tags": ["tag1", "tag2", "tag3"],
            "metadata": {"key1": "value1", "key2": "value2"}
        }
        """

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.id == "abc-123"
        assert result.title == "Test Title"
        assert result.description == "A test description"
        assert result.tags == ["tag1", "tag2", "tag3"]
        assert result.metadata == {"key1": "value1", "key2": "value2"}

    def test_parse_complex_model_with_defaults(self, test_logger: logging.Logger):
        """Parse JSON into complex model using default values."""
        raw_output = '{"id": "def-456", "title": "Minimal"}'

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.id == "def-456"
        assert result.title == "Minimal"
        assert result.description is None
        assert result.tags == []
        assert result.metadata == {}

    def test_parse_nested_model(self, test_logger: logging.Logger):
        """Parse JSON with nested structure."""
        raw_output = """
        {
            "outer_name": "outer",
            "inner": {"name": "inner", "value": 789}
        }
        """

        result = parse_json_from_llm_output(
            raw_output, NestedModel, test_logger, "test output"
        )

        assert result is not None
        assert result.outer_name == "outer"
        assert result.inner.name == "inner"
        assert result.inner.value == 789

    def test_parse_json_with_newlines_in_values(self, test_logger: logging.Logger):
        """Parse JSON with newlines inside string values."""
        raw_output = '{"name": "multi\\nline", "value": 100}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "multi\nline"
        assert result.value == 100

    def test_parse_json_with_unicode(self, test_logger: logging.Logger):
        """Parse JSON with unicode characters.

        Unicode escape sequences are properly decoded by JSON parser.
        """
        raw_output = '{"name": "caf\\u00e9", "value": 200}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        # Unicode \u00e9 is e-acute, so the result is "cafe" with accent
        assert result.name == "café"  # e with acute accent
        assert result.value == 200


# =============================================================================
# Tests: Failed Parsing
# =============================================================================


class TestFailedParsing:
    """Tests for failed JSON parsing scenarios."""

    def test_no_json_in_output(self, test_logger: logging.Logger):
        """Return None when no JSON is found in output."""
        raw_output = "This is just plain text with no JSON at all."

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_empty_output(self, test_logger: logging.Logger):
        """Return None for empty output string."""
        raw_output = ""

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_only_whitespace(self, test_logger: logging.Logger):
        """Return None for whitespace-only output."""
        raw_output = "   \n\t\n   "

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_partial_json_opening_brace_only(self, test_logger: logging.Logger):
        """Return None for incomplete JSON with only opening brace."""
        raw_output = "Here is the data: {"

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None


# =============================================================================
# Tests: Malformed JSON
# =============================================================================


class TestMalformedJson:
    """Tests for malformed JSON scenarios."""

    def test_invalid_json_syntax(self, test_logger: logging.Logger):
        """Return None for invalid JSON syntax."""
        raw_output = '{"name": "test", value: 42}'  # Missing quotes around value key

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_trailing_comma(self, test_logger: logging.Logger):
        """Return None for JSON with trailing comma."""
        raw_output = '{"name": "test", "value": 42,}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_single_quotes(self, test_logger: logging.Logger):
        """Return None for JSON with single quotes (invalid JSON)."""
        raw_output = "{'name': 'test', 'value': 42}"

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_unquoted_string_value(self, test_logger: logging.Logger):
        """Return None for JSON with unquoted string value."""
        raw_output = '{"name": test, "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_unclosed_string(self, test_logger: logging.Logger):
        """Return None for JSON with unclosed string."""
        raw_output = '{"name": "test, "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None


# =============================================================================
# Tests: Model Validation Failures
# =============================================================================


class TestModelValidationFailures:
    """Tests for Pydantic model validation failures."""

    def test_missing_required_field(self, test_logger: logging.Logger):
        """Return None when required field is missing."""
        raw_output = '{"name": "test"}'  # Missing "value" field

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_wrong_type_for_field(self, test_logger: logging.Logger):
        """Return None when field has wrong type."""
        raw_output = '{"name": "test", "value": "not-an-int"}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_extra_fields_allowed(self, test_logger: logging.Logger):
        """Extra fields are ignored (Pydantic default behavior)."""
        raw_output = '{"name": "test", "value": 42, "extra": "ignored"}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "test"
        assert result.value == 42
        # Extra field not accessible on model
        assert not hasattr(result, "extra")

    def test_null_for_required_field(self, test_logger: logging.Logger):
        """Return None when required field is null."""
        raw_output = '{"name": null, "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is None

    def test_null_for_optional_field(self, test_logger: logging.Logger):
        """Accept null for optional field."""
        raw_output = '{"id": "xyz", "title": "Test", "description": null}'

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.id == "xyz"
        assert result.title == "Test"
        assert result.description is None


# =============================================================================
# Tests: Different Pydantic Models
# =============================================================================


class TestDifferentPydanticModels:
    """Tests verifying parsing works with various Pydantic model structures."""

    def test_model_with_field_validators(self, test_logger: logging.Logger):
        """Parse model that uses Field for validation."""
        raw_output = """
        {
            "id": "test-id",
            "title": "Test Title",
            "tags": ["a", "b"]
        }
        """

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.id == "test-id"
        assert result.tags == ["a", "b"]

    def test_model_with_empty_lists(self, test_logger: logging.Logger):
        """Parse model with explicitly empty lists."""
        raw_output = '{"id": "empty", "title": "Empty", "tags": []}'

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.tags == []

    def test_model_with_empty_dict(self, test_logger: logging.Logger):
        """Parse model with explicitly empty dict."""
        raw_output = '{"id": "empty", "title": "Empty", "metadata": {}}'

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.metadata == {}


# =============================================================================
# Tests: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in JSON parsing."""

    def test_multiple_json_objects_greedy_match_fails(
        self, test_logger: logging.Logger
    ):
        """When multiple JSON objects exist on separate lines, greedy regex fails.

        The regex `{[\\s\\S]*}` is greedy and matches from first { to last },
        which creates invalid JSON when multiple objects are on different lines.
        """
        raw_output = """
        First object: {"name": "first", "value": 1}
        Second object: {"name": "second", "value": 2}
        """

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        # Greedy regex matches from first { to last }, creating invalid JSON
        # that includes text between the objects, so parsing fails
        assert result is None

    def test_single_json_object_parses_correctly(self, test_logger: logging.Logger):
        """Single JSON object with surrounding text parses correctly."""
        raw_output = """
        Here is the result:
        {"name": "single", "value": 42}
        That's all!
        """

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "single"
        assert result.value == 42

    def test_json_with_special_characters_in_strings(self, test_logger: logging.Logger):
        """Parse JSON with escaped special characters."""
        raw_output = r'{"name": "test\"with\"quotes", "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == 'test"with"quotes'
        assert result.value == 42

    def test_json_with_backslash(self, test_logger: logging.Logger):
        """Parse JSON with backslash in values."""
        raw_output = r'{"name": "path\\to\\file", "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "test output"
        )

        assert result is not None
        assert result.name == "path\\to\\file"
        assert result.value == 42

    def test_json_with_numeric_string(self, test_logger: logging.Logger):
        """Parse JSON where string field looks like number."""
        raw_output = '{"id": "12345", "title": "Numeric ID"}'

        result = parse_json_from_llm_output(
            raw_output, ComplexModel, test_logger, "test output"
        )

        assert result is not None
        assert result.id == "12345"
        assert isinstance(result.id, str)

    def test_context_parameter_in_error_logging(self, test_logger: logging.Logger):
        """Verify context parameter is used (for error messages)."""
        # This test verifies the function accepts the context parameter
        # The actual logging is tested implicitly through error scenarios
        raw_output = '{"name": "test", "value": 42}'

        result = parse_json_from_llm_output(
            raw_output, SimpleModel, test_logger, "custom context description"
        )

        assert result is not None
        assert result.name == "test"

    def test_deeply_nested_json(self, test_logger: logging.Logger):
        """Parse deeply nested JSON structure."""
        raw_output = """
        {
            "outer_name": "level1",
            "inner": {
                "name": "level2",
                "value": 999
            }
        }
        """

        result = parse_json_from_llm_output(
            raw_output, NestedModel, test_logger, "nested output"
        )

        assert result is not None
        assert result.outer_name == "level1"
        assert result.inner.name == "level2"
        assert result.inner.value == 999
