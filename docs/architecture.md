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

> **Current Phase**: Week 4 API & UI Complete

### Completed Components

| Component | Status | Details |
|-----------|--------|---------|
| Data Layer | ✅ Complete | 50 cocktails, 24 mocktails, 134 ingredients |
| Pydantic Models | ✅ Complete | Structured crew I/O (AnalysisOutput, RecipeOutput, BottleAdvisorOutput) |
| Project Structure | ✅ Complete | FastAPI with routers, templates, static assets |
| Validation Scripts | ✅ Complete | `validate_data.py`, `compute_unlock_scores.py` |
| Pre-commit Hooks | ✅ Complete | ruff, mypy, trailing whitespace checks |
| CrewAI Agents | ✅ Complete | 5 agents including unified Drink Recommender (fast mode) |
| CrewAI Tools | ✅ Complete | 4 deterministic tools for data operations |
| CrewAI Crews | ✅ Complete | Analysis Crew (fast/full modes) + Recipe Crew (optional bottle advice) |
| CrewAI Flow | ✅ Complete | CocktailFlow with state management and rejection workflow |
| API Routes | ✅ Complete | FastAPI endpoints for recommendations |
| Chat UI | ✅ Complete | Conversational interface with Raja the AI Mixologist |
| Deployment | ✅ Complete | Render.com with GitHub Actions CI/CD |
| Unit Tests | ✅ Complete | 339 tests passing with 87% coverage |

### Data Files Summary

| File | Records | Validation |
|------|---------|------------|
| `cocktails.json` | 50 drinks | Pydantic validated |
| `mocktails.json` | 24 drinks | Pydantic validated |
| `ingredients.json` | 134 ingredients | 6 categories |
| `substitutions.json` | 118 rules | 7 substitution maps |
| `unlock_scores.json` | 110 entries | Pre-computed ROI |

### Actual Project Structure (Phase 2)

```
cocktail-cache/
├── src/
│   └── app/
│       ├── main.py              # FastAPI entry point (skeleton)
│       ├── config.py            # Environment configuration
│       ├── models/              # ✅ Complete (Phase 1 + 2)
│       │   ├── __init__.py      # Exports all models
│       │   ├── drinks.py        # Drink, IngredientAmount, FlavorProfile
│       │   ├── ingredients.py   # Ingredient, IngredientsDatabase, SubstitutionsDatabase
│       │   ├── unlock_scores.py # UnlockedDrink, UnlockScores
│       │   ├── cabinet.py       # Cabinet model
│       │   ├── cocktail.py      # CocktailMatch model
│       │   ├── recipe.py        # Recipe, RecipeStep, TechniqueTip
│       │   ├── recommendation.py # Recommendation, BottleRec
│       │   ├── user_prefs.py    # SkillLevel, DrinkType, UserPreferences
│       │   └── history.py       # HistoryEntry, RecipeHistory
│       ├── services/            # ✅ Data loading
│       │   ├── __init__.py
│       │   └── data_loader.py   # Cached JSON loading with validation
│       ├── agents/              # ✅ Complete (Claude Haiku)
│       │   ├── __init__.py      # Factory exports + LLM config
│       │   ├── llm_config.py    # Centralized LLM configuration
│       │   ├── cabinet_analyst.py
│       │   ├── mood_matcher.py
│       │   ├── recipe_writer.py
│       │   └── bottle_advisor.py
│       ├── tools/               # ✅ Complete
│       │   ├── __init__.py      # Tool exports
│       │   ├── recipe_db.py     # RecipeDBTool
│       │   ├── flavor_profiler.py # FlavorProfilerTool
│       │   ├── substitution_finder.py # SubstitutionFinderTool
│       │   └── unlock_calculator.py # UnlockCalculatorTool
│       ├── crews/               # ✅ Complete
│       │   ├── __init__.py      # Crew exports
│       │   ├── analysis_crew.py # Cabinet Analyst → Mood Matcher
│       │   └── recipe_crew.py   # Recipe Writer → Bottle Advisor
│       ├── flows/               # ✅ Complete
│       │   ├── __init__.py      # Flow exports
│       │   └── cocktail_flow.py # Main orchestration with state
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
├── tests/                       # ✅ Complete (339 tests)
│   ├── agents/test_agents.py    # Agent factory tests
│   ├── models/                  # Model validation tests
│   ├── tools/test_tools.py      # Tool unit tests
│   ├── crews/                   # Crew configuration tests
│   │   ├── test_analysis_crew.py
│   │   └── test_recipe_crew.py
│   └── flows/                   # Flow orchestration tests
│       └── test_cocktail_flow.py
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

The system supports two modes for the Analysis Crew:

**Fast Mode (Default)** - Single LLM call, ~50% faster:
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
│   CREW 1: ANALYSIS (FAST)     │   │        CREW 2: RECIPE             │
│   "Find and rank drinks"      │   │   "How to make it, what          │
│                               │   │    to buy next"                   │
├───────────────────────────────┤   ├───────────────────────────────────┤
│                               │   │                                   │
│  ┌─────────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │   DRINK RECOMMENDER     │  │   │  │      RECIPE WRITER          │  │
│  │   (Unified Agent)       │  │   │  │                             │  │
│  │                         │  │   │  │  Input: Selected cocktail   │  │
│  │  Input: Cabinet + Mood  │  │   │  │  Tools: RecipeDB,           │  │
│  │  Tools: RecipeDB,       │  │   │  │         SubstitutionFinder  │  │
│  │         FlavorProfiler  │  │   │  │  Output: RecipeOutput       │  │
│  │  Output: AnalysisOutput │  │   │  └───────────┬─────────────────┘  │
│  │  (1 LLM call)           │  │   │              │ (optional)         │
│  └─────────────────────────┘  │   │              ▼                    │
│                               │   │  ┌─────────────────────────────┐  │
│                               │   │  │     BOTTLE ADVISOR          │  │
│                               │   │  │                             │  │
│                               │   │  │  Input: Cabinet             │  │
│                               │   │  │  Tool: UnlockCalculator     │  │
│                               │   │  │  Output: BottleAdvisorOutput│  │
│                               │   │  └─────────────────────────────┘  │
└───────────────────────────────┘   └───────────────────────────────────┘
```

**Full Mode** - Two LLM calls, more detailed analysis:
```
┌───────────────────────────────┐
│   CREW 1: ANALYSIS (FULL)     │
├───────────────────────────────┤
│  ┌─────────────────────────┐  │
│  │    CABINET ANALYST      │  │
│  │  Tool: RecipeDB         │  │
│  │  Output: Candidates     │  │
│  └───────────┬─────────────┘  │
│              ▼                │
│  ┌─────────────────────────┐  │
│  │     MOOD MATCHER        │  │
│  │  Tool: FlavorProfiler   │  │
│  │  Output: AnalysisOutput │  │
│  └─────────────────────────┘  │
└───────────────────────────────┘
```

### Agent Specifications

> **LLM Configuration**: All agents use Claude Haiku (`anthropic/claude-3-5-haiku-20241022`) by default.
> Custom LLM configurations can be passed to each factory function.

#### Agent 0: Drink Recommender (Fast Mode)

```python
# src/app/agents/drink_recommender.py
from crewai import LLM, Agent
from src.app.agents.llm_config import get_default_llm

def create_drink_recommender(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Drink Recommender",
        goal="Find and rank the best drinks based on available ingredients and mood",
        backstory="""You are Raja, an expert AI mixologist who combines deep
        knowledge of cocktail recipes with an intuitive understanding of mood
        and occasion. You analyze bar cabinets instantly, identify all makeable
        drinks, and rank them by how well they match the user's current mood.
        You always respect drink type preferences and skill level constraints.""",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

**Recommended Tools**: `RecipeDBTool`, `FlavorProfilerTool`
**Used In**: Fast mode Analysis Crew (single-agent, single LLM call)

#### Agent 1: Cabinet Analyst

```python
# src/app/agents/cabinet_analyst.py
from crewai import LLM, Agent
from src.app.agents.llm_config import get_default_llm

def create_cabinet_analyst(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Cabinet Analyst",
        goal="Identify all drinks makeable with available ingredients",
        backstory="""You are an expert mixologist who has memorized every classic
        cocktail and mocktail recipe. When shown a home bar cabinet, you instantly
        recognize which drinks can be made. You consider close substitutions and
        always respect the user's drink type preference (cocktail, mocktail, or both).
        You never suggest drinks that require unavailable ingredients.""",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

**Recommended Tools**: `RecipeDBTool`

#### Agent 2: Mood Matcher

```python
# src/app/agents/mood_matcher.py
def create_mood_matcher(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Mood Matcher",
        goal="Rank drinks by mood fit and occasion",
        backstory="""You understand the deep emotional connection between drinks
        and moods. A Manhattan suits quiet contemplation; a Margarita fits
        celebration. You consider time of day, season, and the user's stated
        mood when ranking candidates. You match drink complexity to skill level
        and prioritize drinks the user hasn't made recently.""",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

**Recommended Tools**: `FlavorProfilerTool`

#### Agent 3: Recipe Writer

```python
# src/app/agents/recipe_writer.py
def create_recipe_writer(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Recipe Writer",
        goal="Generate clear, skill-appropriate recipes with technique tips",
        backstory="""You have taught thousands of home bartenders at every skill
        level. For beginners, you provide detailed technique explanations, safety
        tips, and precise measurements. For intermediate users, you give standard
        instructions with occasional tips. For adventurous bartenders, you're
        concise and suggest creative variations or experiments.""",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

**Recommended Tools**: `RecipeDBTool`, `SubstitutionFinderTool`

#### Agent 4: Bottle Advisor

```python
# src/app/agents/bottle_advisor.py
def create_bottle_advisor(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Bottle Advisor",
        goal="Recommend the next bottle purchase for maximum value",
        backstory="""You analyze bar inventories and recommend strategic purchases.
        You know exactly which bottles unlock the most new drink possibilities.
        You consider budget-friendly options and suggest bottles that unlock the
        most NEW drinks the user cannot currently make. You always respect the
        user's drink type preference.""",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

**Recommended Tools**: `UnlockCalculatorTool`

### LLM Configuration

```python
# src/app/agents/llm_config.py
from crewai import LLM

DEFAULT_MODEL = "anthropic/claude-3-5-haiku-20241022"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

def get_default_llm() -> LLM:
    """Get the default LLM configuration (Claude Haiku)."""
    return LLM(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
    )

def get_llm(
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> LLM:
    """Get a customized LLM configuration."""
    return LLM(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        temperature=temperature or DEFAULT_TEMPERATURE,
    )
```

**Environment Requirements**:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
APP_ENV=development        # Options: development, staging, production, test
CREWAI_TRACING=false       # Enable flow tracing for debugging/observability
```

**CrewAI Tracing**:

When `CREWAI_TRACING=true`, the application enables flow tracing which sends execution traces to CrewAI's observability platform. This is useful for:
- Debugging complex flow issues
- Monitoring LLM call latency and token usage
- Analyzing agent behavior in production

Note: Tracing is disabled by default to avoid sending data to external services.

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

### Configuration Options

The system supports several configuration parameters for performance tuning:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fast_mode` | `True` | Uses unified Drink Recommender (1 LLM call) instead of Cabinet Analyst + Mood Matcher (2 calls) |
| `include_bottle_advice` | `True` | When False, skips the bottle advisor step to save 1 LLM call |
| `PARALLEL_CREWS` | `True` | Environment variable. When enabled, runs Recipe Writer and Bottle Advisor concurrently |

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
│ 3. ANALYSIS CREW                                                     │
│    • Fast mode (default): 1 LLM call via Drink Recommender           │
│    • Full mode (fast_mode=False): 2 LLM calls (Cabinet Analyst →     │
│      Mood Matcher)                                                   │
│    • Output: AnalysisOutput with ranked candidates                   │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. RECIPE CREW                                                       │
│    • Recipe Writer: Full recipe with tips (RecipeOutput)             │
│    • Bottle Advisor (optional, include_bottle_advice=True):          │
│      Next bottle recommendation (BottleAdvisorOutput)                │
│    • Output: RecipeCrewOutput (combined structured output)           │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                          │
│    • Assemble JSON response                                          │
│    • Store state for "show me something else"                        │
│    • Return to client                                                │
└──────────────────────────────────────────────────────────────────────┘


TOTAL LLM CALLS: 2-4 (depending on configuration)
  - Fast mode + no bottle advice: 2 calls (~3-4 seconds)
  - Fast mode + bottle advice (sequential): 3 calls (~5-6 seconds)
  - Fast mode + bottle advice (parallel): 3 calls (~3-4 seconds) [40% faster]
  - Full mode + bottle advice: 4 calls (~6-8 seconds)
TARGET LATENCY: <8 seconds (fast mode with parallel: <4 seconds)
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
| Parallel crew execution | Recipe Crew | Concurrent tasks with `asyncio.gather()` |
| Flow state | CocktailFlow | Cross-crew state |
| Structured output | All outputs | Pydantic integration |
| Error delegation | Flow | Graceful degradation |

---

## Appendix: Parallel Crew Execution

When `PARALLEL_CREWS=true` (the default), the Recipe Writer and Bottle Advisor tasks execute concurrently instead of sequentially. This optimization reduces latency by approximately 40% for requests that include bottle advice.

### Parallel Execution Flow

```
analyze (1.5-4s)
    │
    ├──────────────────┬───────────────────┐
    │                  │                   │
    ▼                  ▼                   │
Recipe Writer    Bottle Advisor           │  ← PARALLEL (asyncio.gather)
(1.5-2s)         (1.5-2s)                 │
    │                  │                   │
    └──────────────────┴───────────────────┘
                       │
                       ▼
                 merge_results
```

### Why This Works

The Bottle Advisor does not depend on Recipe Writer output. It only requires:
- `cabinet` - Available from flow input
- `drink_type` - Available from flow input
- `UnlockCalculatorTool` - Deterministic data lookup

### Configuration

```bash
# Enable parallel execution (default)
export PARALLEL_CREWS=true

# Disable parallel execution (rollback)
export PARALLEL_CREWS=false
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Recipe fails, Bottle succeeds | Return error, discard bottle result |
| Recipe succeeds, Bottle fails | Return recipe with empty bottle advice |
| Both fail | Return first error |
| Timeout (30s) | Return timeout error |

---

*Document Version: 1.3*
*Last Updated: 2025-12-27*
*Principles: KISS + YAGNI*
*Changes: Added PARALLEL_CREWS config, parallel execution architecture, updated latency estimates*
