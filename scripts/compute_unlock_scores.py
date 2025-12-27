#!/usr/bin/env python3
"""Pre-compute which bottles unlock which cocktails AND mocktails.

This script analyzes all drink recipes and builds a reverse index
showing which ingredients unlock which drinks. This enables the
"next bottle" recommendation feature.

Usage:
    uv run python scripts/compute_unlock_scores.py
"""

import json
from collections import defaultdict
from pathlib import Path


def load_json(filepath: Path) -> list[dict]:
    """Load JSON file and return contents."""
    with open(filepath) as f:
        return json.load(f)


def extract_ingredient_ids(drink: dict) -> set[str]:
    """Extract all ingredient item IDs from a drink recipe."""
    return {ing["item"] for ing in drink.get("ingredients", [])}


def compute_unlock_scores(
    cocktails: list[dict],
    mocktails: list[dict],
) -> dict[str, list[dict]]:
    """
    Compute which drinks each ingredient unlocks.

    For each ingredient, returns a list of drinks that use it,
    along with what other ingredients are needed.
    """
    all_drinks = cocktails + mocktails
    bottle_unlocks: dict[str, list[dict]] = defaultdict(list)

    for drink in all_drinks:
        ingredients = extract_ingredient_ids(drink)

        for ing in ingredients:
            bottle_unlocks[ing].append(
                {
                    "id": drink["id"],
                    "name": drink["name"],
                    "is_mocktail": drink.get("is_mocktail", False),
                    "difficulty": drink.get("difficulty", "medium"),
                    "other": sorted(ingredients - {ing}),
                }
            )

    # Sort each ingredient's unlocks by drink name
    for ing in bottle_unlocks:
        bottle_unlocks[ing].sort(key=lambda x: x["name"])

    return dict(bottle_unlocks)


def compute_stats(unlock_scores: dict[str, list[dict]]) -> dict:
    """Compute statistics about the unlock scores."""
    total_ingredients = len(unlock_scores)
    total_unlocks = sum(len(v) for v in unlock_scores.values())

    # Top 10 most versatile ingredients
    top_ingredients = sorted(
        unlock_scores.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    )[:10]

    return {
        "total_ingredients": total_ingredients,
        "total_unlocks": total_unlocks,
        "avg_unlocks_per_ingredient": round(total_unlocks / total_ingredients, 2)
        if total_ingredients > 0
        else 0,
        "top_10_versatile": [
            {"ingredient": ing, "unlocks_count": len(drinks)}
            for ing, drinks in top_ingredients
        ],
    }


def main() -> None:
    """Main entry point."""
    data_dir = Path("data")

    # Load drink databases
    cocktails_path = data_dir / "cocktails.json"
    mocktails_path = data_dir / "mocktails.json"

    if not cocktails_path.exists():
        print(f"Error: {cocktails_path} not found")
        return

    if not mocktails_path.exists():
        print(f"Error: {mocktails_path} not found")
        return

    cocktails = load_json(cocktails_path)
    mocktails = load_json(mocktails_path)

    print(f"Loaded {len(cocktails)} cocktails and {len(mocktails)} mocktails")

    # Compute unlock scores
    unlock_scores = compute_unlock_scores(cocktails, mocktails)

    # Save to file
    output_path = data_dir / "unlock_scores.json"
    with open(output_path, "w") as f:
        json.dump(unlock_scores, f, indent=2)

    print(f"Saved unlock scores to {output_path}")

    # Print stats
    stats = compute_stats(unlock_scores)
    print("\nStatistics:")
    print(f"  Total ingredients: {stats['total_ingredients']}")
    print(f"  Total unlock entries: {stats['total_unlocks']}")
    print(f"  Avg unlocks per ingredient: {stats['avg_unlocks_per_ingredient']}")
    print("\nTop 10 most versatile ingredients:")
    for item in stats["top_10_versatile"]:
        print(f"  {item['ingredient']}: {item['unlocks_count']} drinks")


if __name__ == "__main__":
    main()
