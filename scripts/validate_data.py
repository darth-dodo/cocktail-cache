#!/usr/bin/env python3
"""Validate all data files using Pydantic models.

This script validates all JSON data files against their Pydantic schemas
and reports any validation errors. It uses the centralized data loader
service for consistent validation.

Usage:
    uv run python scripts/validate_data.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from src.app.services.data_loader import (
    clear_cache,
    load_cocktails,
    load_ingredients,
    load_mocktails,
    load_substitutions,
    load_unlock_scores,
)


def validate_all() -> bool:
    """Validate all data files.

    Returns:
        True if all validations pass, False otherwise
    """
    # Clear any cached data to force fresh validation
    clear_cache()

    all_valid = True
    errors: list[str] = []

    print("=" * 60)
    print("Cocktail Cache Data Validation")
    print("=" * 60)

    # Validate cocktails
    print("\n📋 Validating cocktails.json...")
    try:
        cocktails = load_cocktails()
        print(f"  ✅ {len(cocktails)} cocktails validated")

        # Check for mocktails incorrectly in cocktails file
        mocktails_in_cocktails = [c for c in cocktails if c.is_mocktail]
        if mocktails_in_cocktails:
            print(
                f"  ⚠️  Found {len(mocktails_in_cocktails)} mocktails in cocktails.json"
            )
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.error_count()} errors")
        errors.append(f"cocktails.json: {e}")
        all_valid = False
    except FileNotFoundError:
        print("  ❌ File not found")
        errors.append("cocktails.json: File not found")
        all_valid = False

    # Validate mocktails
    print("\n🍹 Validating mocktails.json...")
    try:
        mocktails = load_mocktails()
        print(f"  ✅ {len(mocktails)} mocktails validated")

        # Check all are marked as mocktails
        not_mocktails = [m for m in mocktails if not m.is_mocktail]
        if not_mocktails:
            print(f"  ⚠️  {len(not_mocktails)} drinks missing is_mocktail=true")
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.error_count()} errors")
        errors.append(f"mocktails.json: {e}")
        all_valid = False
    except FileNotFoundError:
        print("  ❌ File not found")
        errors.append("mocktails.json: File not found")
        all_valid = False

    # Validate ingredients
    print("\n🧪 Validating ingredients.json...")
    try:
        ingredients = load_ingredients()
        total = len(ingredients.all_ingredients())
        print(f"  ✅ {total} ingredients validated across categories:")
        print(f"      - spirits: {len(ingredients.spirits)}")
        print(f"      - modifiers: {len(ingredients.modifiers)}")
        print(f"      - bitters_syrups: {len(ingredients.bitters_syrups)}")
        print(f"      - fresh: {len(ingredients.fresh)}")
        print(f"      - mixers: {len(ingredients.mixers)}")
        print(f"      - non_alcoholic: {len(ingredients.non_alcoholic)}")
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.error_count()} errors")
        errors.append(f"ingredients.json: {e}")
        all_valid = False
    except FileNotFoundError:
        print("  ❌ File not found")
        errors.append("ingredients.json: File not found")
        all_valid = False

    # Validate substitutions
    print("\n🔄 Validating substitutions.json...")
    try:
        substitutions = load_substitutions()
        total = (
            len(substitutions.spirits)
            + len(substitutions.modifiers)
            + len(substitutions.bitters_syrups)
            + len(substitutions.fresh)
            + len(substitutions.mixers)
            + len(substitutions.non_alcoholic_to_alcoholic)
            + len(substitutions.alcoholic_to_non_alcoholic)
        )
        print(f"  ✅ {total} substitution rules validated")
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.error_count()} errors")
        errors.append(f"substitutions.json: {e}")
        all_valid = False
    except FileNotFoundError:
        print("  ❌ File not found")
        errors.append("substitutions.json: File not found")
        all_valid = False

    # Validate unlock scores
    print("\n🔓 Validating unlock_scores.json...")
    try:
        unlock_scores = load_unlock_scores()
        total_entries = sum(len(drinks) for drinks in unlock_scores.values())
        print(
            f"  ✅ {len(unlock_scores)} ingredients with {total_entries} unlock entries"
        )

        # Show top 5 most versatile
        top_5 = sorted(unlock_scores.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        print("  Top 5 versatile ingredients:")
        for ing, drinks in top_5:
            print(f"      - {ing}: {len(drinks)} drinks")
    except ValidationError as e:
        print(f"  ❌ Validation failed: {e.error_count()} errors")
        errors.append(f"unlock_scores.json: {e}")
        all_valid = False
    except FileNotFoundError:
        print("  ❌ File not found")
        errors.append("unlock_scores.json: File not found")
        all_valid = False

    # Summary
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All data files validated successfully!")
    else:
        print("❌ Validation failed with errors:")
        for error in errors:
            print(f"  - {error}")
    print("=" * 60)

    return all_valid


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
