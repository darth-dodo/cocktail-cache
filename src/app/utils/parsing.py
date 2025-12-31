"""Common parsing utilities for LLM output extraction."""

import json
import logging
import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def parse_json_from_llm_output(
    raw_output: str,
    model_class: type[T],
    logger: logging.Logger,
    context: str = "output",
) -> T | None:
    """
    Extract and parse JSON from LLM raw output into a Pydantic model.

    Args:
        raw_output: Raw string output from LLM that may contain JSON
        model_class: Pydantic model class to parse into
        logger: Logger instance for error reporting
        context: Description of what's being parsed (for error messages)

    Returns:
        Parsed Pydantic model instance, or None if parsing fails
    """
    try:
        json_match = re.search(r"\{[\s\S]*\}", raw_output)
        if json_match:
            data = json.loads(json_match.group())
            return model_class(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse {context}: {e}")

    return None
