"""Data loading service with Pydantic validation.

This service provides type-safe access to the JSON data files,
validating all data through Pydantic models on load.
"""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from src.app.models.drinks import Drink
from src.app.models.ingredients import IngredientsDatabase, SubstitutionsDatabase
from src.app.models.unlock_scores import UnlockedDrink


def get_data_dir() -> Path:
    """Get the data directory path."""
    # Navigate from src/app/services to project root/data
    return Path(__file__).parent.parent.parent.parent / "data"


@lru_cache(maxsize=1)
def load_cocktails() -> list[Drink]:
    """Load and validate cocktails from JSON.

    Returns:
        List of validated Drink models

    Raises:
        ValidationError: If JSON data doesn't match schema
        FileNotFoundError: If cocktails.json doesn't exist
    """
    data_path = get_data_dir() / "cocktails.json"
    with open(data_path) as f:
        raw_data = json.load(f)

    # Validate each cocktail through Pydantic
    adapter = TypeAdapter(list[Drink])
    return adapter.validate_python(raw_data)


@lru_cache(maxsize=1)
def load_mocktails() -> list[Drink]:
    """Load and validate mocktails from JSON.

    Returns:
        List of validated Drink models (all with is_mocktail=True)

    Raises:
        ValidationError: If JSON data doesn't match schema
        FileNotFoundError: If mocktails.json doesn't exist
    """
    data_path = get_data_dir() / "mocktails.json"
    with open(data_path) as f:
        raw_data = json.load(f)

    adapter = TypeAdapter(list[Drink])
    return adapter.validate_python(raw_data)


@lru_cache(maxsize=1)
def load_all_drinks() -> list[Drink]:
    """Load all drinks (cocktails + mocktails).

    Returns:
        Combined list of all validated Drink models
    """
    return load_cocktails() + load_mocktails()


@lru_cache(maxsize=1)
def load_ingredients() -> IngredientsDatabase:
    """Load and validate ingredients database.

    Returns:
        Validated IngredientsDatabase model

    Raises:
        ValidationError: If JSON data doesn't match schema
    """
    data_path = get_data_dir() / "ingredients.json"
    with open(data_path) as f:
        raw_data = json.load(f)

    return IngredientsDatabase.model_validate(raw_data)


@lru_cache(maxsize=1)
def load_substitutions() -> SubstitutionsDatabase:
    """Load and validate substitutions database.

    Returns:
        Validated SubstitutionsDatabase model

    Raises:
        ValidationError: If JSON data doesn't match schema
    """
    data_path = get_data_dir() / "substitutions.json"
    with open(data_path) as f:
        raw_data = json.load(f)

    return SubstitutionsDatabase.model_validate(raw_data)


@lru_cache(maxsize=1)
def load_unlock_scores() -> dict[str, list[UnlockedDrink]]:
    """Load and validate unlock scores.

    Returns:
        Dictionary mapping ingredient IDs to lists of unlocked drinks

    Raises:
        ValidationError: If JSON data doesn't match schema
    """
    data_path = get_data_dir() / "unlock_scores.json"
    with open(data_path) as f:
        raw_data = json.load(f)

    # Validate each entry
    adapter = TypeAdapter(dict[str, list[UnlockedDrink]])
    return adapter.validate_python(raw_data)


def clear_cache() -> None:
    """Clear all cached data (useful for testing or reloading)."""
    load_cocktails.cache_clear()
    load_mocktails.cache_clear()
    load_all_drinks.cache_clear()
    load_ingredients.cache_clear()
    load_substitutions.cache_clear()
    load_unlock_scores.cache_clear()


def save_drinks(drinks: list[Drink], filepath: Path) -> None:
    """Save drinks to JSON file with validation.

    Args:
        drinks: List of Drink models to save
        filepath: Path to save the JSON file

    Raises:
        ValidationError: If any drink doesn't match schema
    """
    # Re-validate before saving
    adapter = TypeAdapter(list[Drink])
    validated = adapter.validate_python([d.model_dump() for d in drinks])

    with open(filepath, "w") as f:
        json.dump([d.model_dump() for d in validated], f, indent=2)


def save_ingredients(ingredients: IngredientsDatabase, filepath: Path) -> None:
    """Save ingredients database to JSON file.

    Args:
        ingredients: IngredientsDatabase model to save
        filepath: Path to save the JSON file
    """
    with open(filepath, "w") as f:
        json.dump(ingredients.model_dump(), f, indent=2)


def save_substitutions(substitutions: SubstitutionsDatabase, filepath: Path) -> None:
    """Save substitutions database to JSON file.

    Args:
        substitutions: SubstitutionsDatabase model to save
        filepath: Path to save the JSON file
    """
    with open(filepath, "w") as f:
        json.dump(substitutions.model_dump(), f, indent=2)


def save_unlock_scores(scores: dict[str, list[UnlockedDrink]], filepath: Path) -> None:
    """Save unlock scores to JSON file.

    Args:
        scores: Dictionary of ingredient ID to unlocked drinks
        filepath: Path to save the JSON file
    """
    # Convert UnlockedDrink models to dicts
    output = {ing: [d.model_dump() for d in drinks] for ing, drinks in scores.items()}
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
