# Cocktail Cache - Architecture Document

> **Design Principles**: KISS (Keep It Simple) + YAGNI (You Aren't Gonna Need It)
>
> Every component must justify its existence. If in doubt, leave it out.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Agentic Architecture](#agentic-architecture)
3. [Data Flow](#data-flow)
4. [BDD Specifications](#bdd-specifications)
5. [Blueprint](#blueprint)
6. [Key Decisions](#key-decisions)

---

## Implementation Status

> **Current Phase**: Week 1 Complete → Week 2 CrewAI Core (Next)

### Completed Components

| Component | Status | Details |
|-----------|--------|---------|
| Data Layer | ✅ Complete | 50 cocktails, 24 mocktails, 134 ingredients |
| Pydantic Models | ✅ Complete | `Drink`, `Ingredient`, `UnlockScores` validated |
| Project Structure | ✅ Complete | FastAPI skeleton, tests, scripts configured |
| Validation Scripts | ✅ Complete | `validate_data.py`, `compute_unlock_scores.py` |
| Pre-commit Hooks | ✅ Complete | ruff, mypy, trailing whitespace checks |

### Data Files Summary

| File | Records | Validation |
|------|---------|------------|
| `cocktails.json` | 50 drinks | Pydantic validated |
| `mocktails.json` | 24 drinks | Pydantic validated |
| `ingredients.json` | 134 ingredients | 6 categories |
| `substitutions.json` | 118 rules | 7 substitution maps |
| `unlock_scores.json` | 110 entries | Pre-computed ROI |

### Actual Project Structure (Phase 1)

```
cocktail-cache/
├── src/
│   └── app/
│       ├── main.py              # FastAPI entry point (skeleton)
│       ├── config.py            # Environment configuration
│       ├── models/              # ✅ Pydantic models
│       │   ├── __init__.py
│       │   ├── drinks.py        # Drink, IngredientAmount, FlavorProfile
│       │   ├── ingredients.py   # Ingredient, IngredientsDatabase, SubstitutionsDatabase
│       │   └── unlock_scores.py # UnlockedDrink, UnlockScores
│       ├── services/            # ✅ Data loading
│       │   ├── __init__.py
│       │   └── data_loader.py   # Cached JSON loading with validation
│       ├── agents/              # 🔲 Week 2
│       ├── crews/               # 🔲 Week 2
│       ├── tools/               # 🔲 Week 2
│       ├── flows/               # 🔲 Week 3
│       ├── routers/             # 🔲 Week 4
│       ├── templates/           # 🔲 Week 5
│       └── static/              # 🔲 Week 5
├── data/                        # ✅ Complete
│   ├── cocktails.json           # 50 cocktail recipes
│   ├── mocktails.json           # 24 non-alcoholic recipes
│   ├── ingredients.json         # 134 categorized ingredients
│   ├── substitutions.json       # 118 ingredient swap rules
│   └── unlock_scores.json       # Pre-computed bottle ROI (110 entries)
├── scripts/                     # ✅ Complete
│   ├── compute_unlock_scores.py # Generate bottle recommendations
│   └── validate_data.py         # Pydantic data validation
├── tests/                       # 🔲 Week 2+
├── tasks.md                     # Development task tracker
├── pyproject.toml              # Project configuration
├── Makefile                    # Development commands
└── render.yaml                 # Render deployment config
```

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COCKTAIL CACHE                                  │
│                                                                         │
│  "Your cabinet. Your mood. Your perfect drink."                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT                                    │
│                                                                         │
│   Cabinet: [bourbon, gin, lemons, honey, angostura...]                  │
│   Mood: "Unwinding after a long week"                                   │
│   Constraints: [not too sweet]                                          │
│   Preferred Spirit: bourbon (optional)                                  │
│   Drink Type: cocktail | mocktail | both                                │
│   Skill Level: beginner | intermediate | adventurous                    │
│   Recent History: [last 3-10 made drinks to exclude]                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │     PRE-COMPUTED DATA     │   │      RUNTIME AI           │
    │     (No LLM needed)       │   │      (CrewAI)             │
    ├───────────────────────────┤   ├───────────────────────────┤
    │ • Cocktail recipes        │   │ • Mood interpretation     │
    │ • Flavor profiles         │   │ • Personalized copy       │
    │ • Ingredient categories   │   │ • Technique tips          │
    │ • Substitution mappings   │   │ • Contextual advice       │
    │ • Unlock scores           │   │                           │
    └───────────────────────────┘   └───────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT                                       │
│                                                                         │
│   Recommendation: Gold Rush (or Mocktail if selected)                   │
│   Recipe: [ingredients, method, skill-adapted tips]                     │
│   Flavor Profile: {sweet: 40, sour: 50, bitter: 10}                     │
│   Next Bottle: Campari (unlocks 4 new drinks)                           │
│   Difficulty Badge: Easy | Medium | Advanced                            │
│   Mocktail Badge: Spirit-free indicator (if applicable)                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Insight

**Most of the work is NOT AI.** Recipe matching, flavor profiles, and unlock scores are deterministic. AI adds value for:
- Interpreting fuzzy mood descriptions
- Writing personalized, contextual copy
- Adapting technique tips to explicit skill level
- Selecting from cocktails OR mocktails based on drink type preference

This insight drives the entire architecture.

---

## Agentic Architecture

### Crew Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COCKTAIL FLOW                                    │
│                     (Orchestrates everything)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────────┐
│       CREW 1: ANALYSIS        │   │        CREW 2: RECIPE             │
│   "What CAN and SHOULD        │   │   "How to make it, what          │
│    they make?"                │   │    to buy next"                   │
├───────────────────────────────┤   ├───────────────────────────────────┤
│                               │   │                                   │
│  ┌─────────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │    CABINET ANALYST      │  │   │  │      RECIPE WRITER          │  │
│  │                         │  │   │  │                             │  │
│  │  Input: Raw ingredients │  │   │  │  Input: Selected cocktail   │  │
│  │  Tool: RecipeDB         │  │   │  │  Tool: RecipeDB             │  │
│  │  Output: Candidates     │  │   │  │  Output: Full recipe +      │  │
│  │          with scores    │  │   │  │          technique tips     │  │
│  └───────────┬─────────────┘  │   │  └───────────┬─────────────────┘  │
│              │                │   │              │                    │
│              ▼                │   │              ▼                    │
│  ┌─────────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │     MOOD MATCHER        │  │   │  │     BOTTLE ADVISOR          │  │
│  │                         │  │   │  │                             │  │
│  │  Input: Mood + canddts  │  │   │  │  Input: Cabinet             │  │
│  │  Tool: FlavorProfiler   │  │   │  │  Tool: UnlockCalculator     │  │
│  │  Output: Ranked list    │  │   │  │  Output: Next bottle +      │  │
│  │          with "why"     │  │   │  │          ROI justification  │  │
│  └─────────────────────────┘  │   │  └─────────────────────────────┘  │
│                               │   │                                   │
└───────────────────────────────┘   └───────────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FINAL RESPONSE    │
                         └─────────────────────┘
```

### Agent Specifications

#### Agent 1: Cabinet Analyst

```yaml
role: "Cabinet Analyst"
goal: "Identify all drinks makeable with available ingredients"
backstory: |
  You're the inventory specialist. You know every classic cocktail's
  and mocktail's ingredient list by heart. Your job is simple: look at
  what they have, find what they can make. No creativity needed—just accuracy.

tools:
  - RecipeDB.query_by_ingredients()

input:
  cabinet: list[str]      # ["bourbon", "lemons", "honey"]
  drink_type: str         # "cocktail" | "mocktail" | "both"
  skill_level: str        # "beginner" | "intermediate" | "adventurous"
  exclude_recent: list[str]  # Recipe IDs to exclude (from history)

output:
  candidates:
    - cocktail_id: str
      name: str
      match_score: float  # 1.0 = all ingredients, 0.8 = missing 1
      missing: list[str]
      substitutable: bool
      difficulty: str     # "easy" | "medium" | "advanced"
      is_mocktail: bool
```

#### Agent 2: Mood Matcher

```yaml
role: "Mood Matcher"
goal: "Rank drinks by how well they fit the user's mood, constraints, and skill level"
backstory: |
  You read between the lines. "Unwinding" means something different than
  "celebrating." You understand that "not too sweet" is a hard constraint,
  but "something impressive" is a soft preference. You also respect skill
  levels—beginners get simpler recipes first. You explain WHY a drink
  fits—that's what builds trust.

tools:
  - FlavorProfiler.get_profile()

input:
  mood: str
  constraints: list[str]
  candidates: list[CocktailMatch]
  skill_level: str        # Factor into ranking

output:
  ranked:
    - cocktail_id: str
      rank: int
      why: str  # "This delivers bourbon warmth without being heavy..."
      flavor_profile: FlavorProfile
      skill_appropriate: bool  # Matches user's comfort level
```

#### Agent 3: Recipe Writer

```yaml
role: "Recipe Writer"
goal: "Generate clear, skill-appropriate recipes with technique tips"
backstory: |
  You've taught thousands of home bartenders at every skill level. You know
  where beginners mess up: undershaking, using bottled citrus, not chilling
  glasses. For adventurous users, you can explain egg white handling or
  infusion techniques. Your recipes are scannable (bold actions, indented
  details) and your tips match the user's comfort level. You never
  condescend—you empower.

tools:
  - RecipeDB.get_recipe()
  - SubstitutionFinder.find_subs()

input:
  cocktail_id: str
  user_cabinet: list[str]
  skill_level: str        # Adjusts tip detail and complexity

output:
  recipe: Recipe  # Full Pydantic model (see models/)
  # Includes: skill_adapted_tips, mocktail_badge (if applicable)
```

#### Agent 4: Bottle Advisor

```yaml
role: "Bottle Advisor"
goal: "Recommend the highest-ROI next bottle purchase"
backstory: |
  You think in terms of "unlock potential." One bottle that enables 4 new
  cocktails beats three bottles that each enable one. You consider what
  they already have, what they seem to like, and what lasts on the shelf.
  You always explain your reasoning—it's not just a recommendation, it's
  education.

tools:
  - UnlockCalculator.get_scores()

input:
  cabinet: list[str]
  preferred_profiles: list[str]  # inferred from mood/selection

output:
  recommendation:
    bottle: str
    price_range: str
    why: str
    unlocks: list[UnlockedCocktail]
  runner_up:
    bottle: str
    why: str
```

### Tool Specifications

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            TOOLS                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   RecipeDB      │  │ FlavorProfiler  │  │SubstitutionFind │         │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤         │
│  │                 │  │                 │  │                 │         │
│  │ query_by_       │  │ get_profile()   │  │ find_subs()     │         │
│  │   ingredients() │  │                 │  │                 │         │
│  │                 │  │ Returns:        │  │ Returns:        │         │
│  │ get_recipe()    │  │ {sweet, sour,   │  │ [{sub, quality, │         │
│  │                 │  │  bitter, spirit}│  │   ratio_adj}]   │         │
│  │ Data: JSON file │  │                 │  │                 │         │
│  │ No AI needed    │  │ Data: JSON file │  │ Data: JSON file │         │
│  │                 │  │ No AI needed    │  │ No AI needed    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
│  ┌─────────────────┐                                                    │
│  │UnlockCalculator │  KEY INSIGHT: All tools are deterministic.        │
│  ├─────────────────┤  They query pre-computed data.                    │
│  │                 │  AI is only for interpretation and copy.          │
│  │ get_scores()    │                                                    │
│  │                 │                                                    │
│  │ Returns:        │                                                    │
│  │ {bottle: score} │                                                    │
│  │                 │                                                    │
│  │ Pre-computed    │                                                    │
│  │ at build time   │                                                    │
│  └─────────────────┘                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Request Lifecycle

```
                              REQUEST
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 1. PARSE INPUT                                                       │
│    • Validate cabinet ingredients against known list                 │
│    • Normalize names ("Maker's Mark" → "bourbon")                    │
│    • Store in flow state                                             │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. PRE-FILTER (No AI)                                                │
│    • Query RecipeDB for all cocktails matching cabinet               │
│    • This is a simple set intersection, not AI                       │
│    • Returns 5-50 candidates depending on cabinet size               │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. ANALYSIS CREW (2 LLM calls)                                       │
│    • Cabinet Analyst: Scores candidates by match quality             │
│    • Mood Matcher: Ranks by mood fit, applies constraints            │
│    • Output: Top 3 candidates with reasoning                         │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. RECIPE CREW (2 LLM calls)                                         │
│    • Recipe Writer: Full recipe with tips for #1 candidate           │
│    • Bottle Advisor: Next bottle recommendation                      │
│    • Output: Complete response payload                               │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                          │
│    • Assemble JSON response                                          │
│    • Store state for "show me something else"                        │
│    • Return to client                                                │
└──────────────────────────────────────────────────────────────────────┘


TOTAL LLM CALLS: 4
TARGET LATENCY: <8 seconds
```

### State Management

```python
class CocktailFlowState(BaseModel):
    """State for request lifecycle with skill and history awareness."""

    # Session
    session_id: str

    # Input (from user)
    cabinet: list[str]
    mood: str
    constraints: list[str] = []
    preferred_spirit: str | None = None
    drink_type: str = "cocktail"  # "cocktail" | "mocktail" | "both"
    skill_level: str = "intermediate"  # "beginner" | "intermediate" | "adventurous"

    # History (loaded from local storage)
    recent_history: list[str] = []  # Recipe IDs to exclude

    # Analysis output
    candidates: list[CocktailMatch] = []
    selected: str | None = None

    # Recipe output
    recipe: Recipe | None = None
    next_bottle: BottleRecommendation | None = None

    # Session memory
    rejected: list[str] = []  # For "show me something else"
```

**Note**: History, skill level, and drink type are stored in browser local storage and passed with each request.

---

## BDD Specifications

### Feature: Cocktail Recommendation

```gherkin
Feature: Drink Recommendation
  As a home drink enthusiast
  I want to get cocktail or mocktail recommendations based on my cabinet and mood
  So that I can make something great with what I already have

  Background:
    Given the recipe database is loaded
    And unlock scores are pre-computed

  # ─────────────────────────────────────────────────────────────────────
  # HAPPY PATH SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Minimal cabinet gets a valid recommendation
    Given my cabinet contains:
      | ingredient |
      | bourbon    |
      | lemons     |
      | honey      |
    And my mood is "unwinding after a long week"
    When I request a recommendation
    Then I receive a cocktail recommendation
    And the recipe uses only ingredients from my cabinet
    And the response includes technique tips
    And I receive a "next bottle" recommendation

  Scenario: Well-stocked cabinet gets premium recommendation
    Given my cabinet contains 15 or more ingredients
    And my mood is "impressing someone special"
    When I request a recommendation
    Then I receive a cocktail that uses premium ingredients
    And the "why this drink" explanation references impressiveness

  Scenario: Constraints are respected
    Given my cabinet contains:
      | ingredient    |
      | gin           |
      | sweet vermouth|
      | campari       |
      | lemons        |
      | simple syrup  |
    And my constraint is "not too sweet"
    When I request a recommendation
    Then all recommended cocktails have sweet_score < 50
    And the Negroni is ranked higher than sweet cocktails

  # ─────────────────────────────────────────────────────────────────────
  # EDGE CASE SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Single-spirit cabinet gets helpful response
    Given my cabinet contains only:
      | ingredient |
      | vodka      |
    When I request a recommendation
    Then I receive a recommendation for what's possible
    And the "next bottle" recommendation is strongly emphasized
    And the tone is helpful, not judgmental

  Scenario: Empty cabinet gets guidance
    Given my cabinet is empty
    When I request a recommendation
    Then I receive a "getting started" guide
    And I receive a suggested "starter cabinet"
    And the tone is encouraging

  Scenario: "Show me something else" excludes previous
    Given I received a recommendation for "Gold Rush"
    When I click "show me something else"
    Then I receive a different recommendation
    And "Gold Rush" is not in the alternatives

  # ─────────────────────────────────────────────────────────────────────
  # NEXT BOTTLE SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Next bottle maximizes unlock potential
    Given my cabinet contains:
      | ingredient     |
      | gin            |
      | sweet vermouth |
      | lemons         |
      | simple syrup   |
    When I request a recommendation
    Then the "next bottle" recommendation is "Campari"
    And the justification explains it unlocks Negroni and Boulevardier
    And the runner-up is also provided

  # ─────────────────────────────────────────────────────────────────────
  # MOCKTAIL SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Mocktail mode returns only non-alcoholic drinks
    Given my cabinet contains:
      | ingredient     |
      | lemons         |
      | honey          |
      | ginger         |
      | soda water     |
    And my drink type is "mocktail"
    When I request a recommendation
    Then I receive only non-alcoholic recommendations
    And each recipe displays a "spirit-free" badge
    And no spirits appear in any ingredient list

  Scenario: Both mode returns mixed recommendations
    Given my cabinet contains spirits and mixers
    And my drink type is "both"
    When I request a recommendation
    Then I receive a mix of cocktails and mocktails
    And each drink is clearly labeled by type

  # ─────────────────────────────────────────────────────────────────────
  # SKILL LEVEL SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Beginner skill level filters complex recipes
    Given my cabinet contains 10 ingredients
    And my skill level is "beginner"
    When I request a recommendation
    Then recommended drinks have difficulty "easy" or "medium"
    And technique tips use beginner-friendly language
    And no recipes require egg whites or infusions

  Scenario: Adventurous skill level includes complex recipes
    Given my cabinet contains 10 ingredients
    And my skill level is "adventurous"
    When I request a recommendation
    Then all difficulty levels are available
    And technique tips include advanced techniques
    And complex recipes like flips and fizzes may appear

  Scenario: Skill level affects tip verbosity
    Given I select the "Whiskey Sour" cocktail
    When I view the recipe as a "beginner"
    Then shaking technique has detailed explanation
    And timing is explicitly stated
    When I view the same recipe as "adventurous"
    Then shaking technique is concise
    And optional variations are suggested

  # ─────────────────────────────────────────────────────────────────────
  # RECIPE HISTORY SCENARIOS
  # ─────────────────────────────────────────────────────────────────────

  Scenario: Recent drinks are excluded from recommendations
    Given I made "Gold Rush" 2 days ago
    And I made "Whiskey Sour" yesterday
    And my cabinet can make both drinks
    When I request a recommendation
    Then neither "Gold Rush" nor "Whiskey Sour" is recommended
    And the recommendation is something different

  Scenario: "I made this" tracks recipe to history
    Given I am viewing the "Negroni" recipe
    When I click "I made this"
    Then "Negroni" is added to my recipe history
    And the timestamp is recorded
    And my history shows "Negroni" as recently made

  Scenario: History displays recently made drinks
    Given I have made 5 drinks in the past month
    When I view my recipe history
    Then I see "Recently Made" list
    And drinks are ordered by most recent first
    And each entry shows drink name and date

  Scenario: "Make Again" quick action works
    Given "Margarita" is in my recipe history
    When I click "Make Again" on Margarita
    Then I see the full Margarita recipe
    And my cabinet compatibility is shown
```

### Feature: Recipe Display

```gherkin
Feature: Recipe Display
  As a party host
  I want clear, instructive recipes
  So that I don't mess up in front of guests

  Scenario: Recipe includes all required sections
    Given I have selected the "Gold Rush" cocktail
    When I view the recipe
    Then I see the cocktail name and tagline
    And I see the full ingredient list with amounts
    And I see step-by-step method
    And I see technique tips for each step
    And I see timing and difficulty
    And I see garnish instructions

  Scenario: Recipe includes prep steps when needed
    Given I have selected a cocktail requiring honey syrup
    When I view the recipe
    Then I see a "prep" section for honey syrup
    And the prep section includes storage instructions

  Scenario: Recipe suggests substitutions
    Given I am missing "lime juice" for a cocktail
    When I view the recipe
    Then I see a substitution suggestion
    And the substitution includes quality rating
    And the substitution includes ratio adjustment if needed
```

### Feature: Local Storage Persistence

```gherkin
Feature: Local Storage Persistence
  As a return user
  I want my preferences and history saved
  So that I get a personalized experience every time

  Scenario: Cabinet is saved automatically
    Given I am a first-time user
    When I enter my cabinet ingredients
    And I receive a recommendation
    Then my cabinet is saved to local storage

  Scenario: Cabinet is restored on return
    Given I previously saved a cabinet with 10 ingredients
    When I return to the app
    Then my cabinet is pre-populated
    And I can immediately request a recommendation

  Scenario: Skill level persists across sessions
    Given I set my skill level to "beginner"
    When I close and reopen the app
    Then my skill level is still "beginner"
    And recommendations are filtered appropriately

  Scenario: Drink type preference persists
    Given I set drink type to "mocktail"
    When I close and reopen the app
    Then drink type is still "mocktail"
    And I receive mocktail recommendations

  Scenario: Recipe history persists across sessions
    Given I marked "Negroni" as made last week
    When I close and reopen the app
    Then "Negroni" still appears in my history
    And it's excluded from new recommendations

  Scenario: Clear all data works
    Given I have cabinet, history, and preferences saved
    When I click "Clear All Data"
    Then all local storage is cleared
    And I see the first-time user experience
```

---

## Blueprint

### Directory Structure

```
cocktail-cache/
│
├── app/                          # Application code
│   │
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Environment configuration
│   │
│   ├── agents/                   # CrewAI agent definitions
│   │   ├── __init__.py
│   │   ├── cabinet_analyst.py    # Analyzes cabinet → candidates
│   │   ├── mood_matcher.py       # Ranks by mood fit
│   │   ├── recipe_writer.py      # Generates full recipes
│   │   └── bottle_advisor.py     # Recommends next purchase
│   │
│   ├── crews/                    # Crew compositions
│   │   ├── __init__.py
│   │   ├── analysis_crew.py      # Cabinet + Mood agents
│   │   └── recipe_crew.py        # Recipe + Bottle agents
│   │
│   ├── tools/                    # CrewAI tools
│   │   ├── __init__.py
│   │   ├── recipe_db.py          # Query cocktail database
│   │   ├── flavor_profiler.py    # Get flavor profiles
│   │   ├── substitution_finder.py# Find ingredient swaps
│   │   └── unlock_calculator.py  # Calculate unlock scores
│   │
│   ├── flows/                    # CrewAI flows
│   │   ├── __init__.py
│   │   └── cocktail_flow.py      # Main orchestration
│   │
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── cabinet.py            # Cabinet, Ingredient
│   │   ├── cocktail.py           # Cocktail, CocktailMatch
│   │   ├── recipe.py             # Recipe, Step, Tip
│   │   └── recommendation.py     # Recommendation, NextBottle
│   │
│   ├── routers/                  # FastAPI routes
│   │   ├── __init__.py
│   │   └── api.py                # /recommend, /another, /recipe
│   │
│   ├── templates/                # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   └── components/
│   │       ├── cabinet_grid.html
│   │       ├── recipe_card.html
│   │       ├── flavor_chart.html
│   │       ├── skill_selector.html   # Skill level toggle
│   │       ├── drink_type_toggle.html # Cocktail/Mocktail selector
│   │       └── history_list.html     # Recently made drinks
│   │
│   └── static/
│       ├── styles.css
│       └── htmx.min.js
│
├── data/                         # Static data files
│   ├── cocktails.json            # 50 classic cocktail recipes
│   ├── mocktails.json            # 20+ non-alcoholic recipes
│   ├── ingredients.json          # Categorized ingredient list
│   ├── substitutions.json        # Ingredient swap mappings
│   └── unlock_scores.json        # Pre-computed at build
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── features/                 # BDD feature files
│   │   ├── recommendation.feature
│   │   ├── recipe.feature
│   │   ├── cabinet.feature
│   │   ├── mocktails.feature     # Non-alcoholic recommendations
│   │   ├── skill_level.feature   # Skill-based filtering
│   │   └── history.feature       # Recipe history tracking
│   ├── steps/                    # BDD step definitions
│   │   └── ...
│   ├── agents/                   # Agent unit tests
│   │   └── ...
│   ├── tools/                    # Tool unit tests
│   │   └── ...
│   └── integration/              # End-to-end tests
│       └── ...
│
├── scripts/                      # Build/utility scripts
│   ├── compute_unlock_scores.py  # Pre-compute unlock data
│   └── validate_data.py          # Validate JSON files
│
├── product.md                    # Product requirements
├── architecture.md               # This document
├── Dockerfile
├── fly.toml
├── requirements.txt
├── pyproject.toml
└── .env.example
```

### File Purposes

| File/Directory | Purpose | KISS Rationale |
|----------------|---------|----------------|
| `agents/` | One file per agent | Single responsibility |
| `crews/` | One file per crew | Explicit composition |
| `tools/` | One file per tool | Easy to test |
| `flows/` | One flow file | We only have one flow |
| `models/` | Pydantic models | Type safety, validation |
| `data/` | JSON files (cocktails + mocktails) | No database needed |
| `tests/features/` | BDD feature files | Executable specs |
| `templates/components/` | UI partials (skill, history, drink type) | Progressive enhancement |

---

## Key Decisions

### What We Build

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Database | JSON files | 100 recipes don't need SQLite |
| Caching | In-memory dict | Redis is overkill for MVP |
| Auth | None | Local storage is enough |
| Crew execution | Sequential | Prove need for parallel first |
| Frontend | HTMX | No build step, no JS framework |
| State | Flow state only | No persistent user state |
| Hosting | Fly.io | Good free tier, simple deploy |

### What We DON'T Build (YAGNI)

| Feature | Why Not |
|---------|---------|
| User accounts | Adds auth complexity, local storage is enough |
| Recipe ratings | Requires accounts |
| Favorites | History serves similar purpose |
| Shopping list export | Nice-to-have, not core |
| Social sharing cards | Defer until we have users |
| Measurement toggle (oz/ml) | Single unit is fine for MVP |
| Price lookup | Prices change, hard to maintain |
| Barcode scanning | Mobile complexity |

### Anti-Patterns to Avoid

```
❌ DON'T: Add "just in case" features
✅ DO: Add features when users ask for them

❌ DON'T: Abstract until you have 3+ similar things
✅ DO: Copy-paste is fine for 2 things

❌ DON'T: Add agents for single responsibilities
✅ DO: One agent can have multiple outputs

❌ DON'T: Add tools for things the LLM can do directly
✅ DO: Tools are for external data access

❌ DON'T: Add caching until you measure latency
✅ DO: Measure first, optimize second

❌ DON'T: Add error recovery until you see errors
✅ DO: Let it fail, then handle
```

---

## Appendix: CrewAI Patterns Used

| Pattern | Where | Learning Objective |
|---------|-------|-------------------|
| Agent with persona | All agents | Voice/personality design |
| Tool with schema | All tools | Type-safe tool inputs |
| Sequential crew | Both crews | Agent handoff |
| Flow state | CocktailFlow | Cross-crew state |
| Structured output | All outputs | Pydantic integration |
| Error delegation | Flow | Graceful degradation |

---

*Document Version: 1.0*
*Last Updated: 2025-12-27*
*Principles: KISS + YAGNI*
