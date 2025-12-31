# Multi-Agent AI Service Blueprint

> **For Developers & AI Agents** — A practical guide to building production-ready multi-agent systems.
>
> Based on patterns from [Cocktail Cache](https://cocktail-cache.onrender.com) — 761 tests, 78% coverage, CrewAI + FastAPI + Claude.

---

## Quick Context (for AI Agents)

```yaml
# Machine-parseable metadata for AI coding assistants
project_type: multi-agent-ai-service
name: cocktail-cache
description: AI-powered drink advisor with conversational agent (Raja)

stack:
  runtime: python 3.12
  api: fastapi
  ai_framework: crewai >= 0.86.0
  llm_provider: anthropic claude
  frontend: htmx + jinja2 + tailwind
  validation: pydantic >= 2.10.0

patterns:
  - crews: orchestrate multi-agent workflows (analysis, recipe, chat)
  - agents: factory functions returning configured CrewAI Agent instances
  - tools: crewai-tools for data operations (recipe_db, unlock_calculator)
  - flows: complex multi-step orchestration (cocktail_flow.py)
  - pydantic-io: typed inputs/outputs for all crew operations

key_paths:
  agents: src/app/agents/           # Agent factory functions
  agent_config: src/app/agents/config/  # YAML for prompts, personalities
  crews: src/app/crews/             # Crew orchestration classes
  tools: src/app/tools/             # CrewAI tool implementations
  flows: src/app/flows/             # Multi-step flow orchestration
  models: src/app/models/           # Pydantic models (crew_io.py critical)
  services: src/app/services/       # Data loading, drink database
  routers: src/app/routers/         # Modular FastAPI endpoints (api, flow, chat, drinks, bottles)
  utils: src/app/utils/             # Shared utilities (parsing.py)
  tests: tests/                     # Mirrored structure

commands:
  install: make install             # uv sync + pre-commit install
  dev: make dev                     # uvicorn on port 8888
  test: make test                   # pytest with coverage
  check: make check                 # lint + typecheck + test
  format: make format               # ruff format + fix
  typecheck: make typecheck         # mypy strict

conventions:
  - agent_factories: create_*() functions return configured Agent
  - yaml_configs: prompts in agents/config/agents.yaml, tasks in tasks.yaml
  - pydantic_io: AnalysisInput/Output, RecipeInput/Output for all crews
  - mock_llm_testing: tests use mock responses, no real API calls
  - data_injection: context passed via task description, not agent memory

test_coverage: 78%
test_count: 761
deployment: render.com
```

---

## Philosophy

### LLM for Content, Code for Logic

- **LLM responsibilities**: Creative text generation, mood interpretation, personality-rich responses, storytelling
- **Code responsibilities**: Ingredient matching, drink filtering, score calculation, cabinet analysis
- **Boundary rule**: If an operation has a deterministic answer, use Python. If it requires interpretation or creativity, use the LLM.
- **Example**: Finding makeable drinks = code (set intersection). Explaining why a Manhattan suits a contemplative mood = LLM.

### Configuration Over Code

- **Prompts in YAML**: All agent roles, goals, and backstories live in `agents/config/agents.yaml`
- **Task templates in YAML**: Task descriptions with placeholders in `agents/config/tasks.yaml`
- **LLM settings in YAML**: Model selection, temperature profiles in `agents/config/llm.yaml`
- **Why**: Non-engineers can tune prompts. Version control tracks personality changes. A/B testing becomes config swaps.

### Type Safety Everywhere

- **Pydantic for crew I/O**: `AnalysisInput`, `RecipeOutput`, `BarGrowthOutput` in `models/crew_io.py`
- **Validation on boundaries**: All API inputs validated. All LLM outputs parsed into Pydantic models.
- **Field constraints**: `ge=0`, `le=100`, regex patterns for enums
- **Benefit**: Catch malformed LLM responses early. IDE autocomplete. Self-documenting contracts.

### Graceful Degradation

- **LLM failure**: Return cached/fallback recommendations, not 500 errors
- **Partial results**: If mood matching fails, still return cabinet-based matches
- **Rate limiting**: Built-in request throttling with informative error messages
- **Test isolation**: All tests run with mock LLM responses, never depend on API availability

### Minimize LLM Calls

- **Batch operations**: Analysis crew does cabinet + mood matching in one call, not two
- **Code-first filtering**: Python filters 142 drinks to candidates BEFORE LLM ranks them
- **Cache static data**: Drink database and unlock scores computed once at startup
- **Avoid re-generation**: Recipe structure from database, LLM only adds technique tips

### KISS + YAGNI

- **No agent memory**: Context passed via task description, not persistent agent state
- **No multi-turn planning**: Single-task agents, crew handles orchestration
- **4 focused tools**: (recipe_db, unlock_calculator, flavor_profiler, substitution_finder) now integrated with Raja agent
- **Flat hierarchy**: One level of crews, no nested sub-crews or agent delegation chains

---

## Decision Framework

### 1. Agent vs Tool vs Code

```
Task type?
├─ Creative/interpretive (mood, personality, writing)
│   └─ AGENT (with LLM)
│       Cost: $$$  |  Latency: 500ms+  |  Determinism: Low
│
├─ Data lookup/transformation (recipes, scores, filters)
│   └─ TOOL (deterministic code)
│       Cost: $  |  Latency: <50ms  |  Determinism: High
│
└─ Business logic (routing, validation, state)
    └─ CODE (no LLM needed)
        Cost: $  |  Latency: <10ms  |  Determinism: High
```

**Anti-Pattern**: Using LLM for data lookup → hallucinates, costs 100x more, 10x slower

### 2. Model Selection

```
Output complexity?
├─ Simple: classification, extraction, formatting
│   └─ Haiku ($0.25/1M tokens) - fast, cheap
│
├─ Complex: reasoning, planning, multi-step
│   └─ Sonnet ($3/1M tokens) - balanced
│
└─ Critical: nuanced judgment, high stakes
    └─ Opus ($15/1M tokens) - premium
```

**Checklist for Haiku**: Output is structured, task has clear answers, no multi-step reasoning, high volume

### 3. Sequential vs Parallel Crews

```
Agent dependencies?
├─ Agent B needs Agent A's output
│   └─ SEQUENTIAL (safe default)
│       Total Latency = A + B + C
│
├─ Agents independent, latency matters
│   └─ PARALLEL (asyncio.gather)
│       Total Latency = max(A, B, C) + Join
│
└─ Unsure
    └─ Start SEQUENTIAL, measure, then optimize
```

### 4. Session Storage

```
Deployment context?
├─ Single instance, MVP
│   └─ In-memory dict (zero setup, lost on restart)
│
├─ Multi-instance, production
│   └─ Redis with TTL (shared state, persistence)
│
└─ Privacy-first, no tracking
    └─ Client-side localStorage (user owns data)
```

### 5. Testing Strategy

```
What are you testing?
├─ Model validation, state logic
│   └─ Unit tests (fast, no mocks needed)
│
├─ Agent behavior, tool integration
│   └─ Unit + mock LLM (NEVER real API calls)
│
├─ Crew composition, flows
│   └─ Integration tests (mock external services)
│
└─ User journeys, end-to-end
    └─ BDD features (Gherkin specs)
```

### Quick Reference

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Recipe lookup by ingredient | Tool | Deterministic database query |
| Mood detection from text | Agent (Haiku) | Interpretation needed, simple output |
| Multi-step drink planning | Agent (Sonnet) | Reasoning + multiple constraints |
| Input validation | Code | No LLM needed, performance critical |
| MVP single-server deploy | In-memory dict | Simple, no infra overhead |
| Production multi-pod deploy | Redis with TTL | Shared state required |
| Testing Pydantic models | Unit (no mock) | Pure functions, fast |
| Testing agent output | Unit + mock LLM | Verify behavior, not LLM |

---

## Project Structure

```
my-ai-service/
├── src/app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Environment configuration
│   │
│   ├── agents/                    # One file per agent + config/
│   │   ├── config/
│   │   │   ├── agents.yaml        # Role, goal, backstory
│   │   │   ├── tasks.yaml         # Task templates
│   │   │   └── llm.yaml           # Model configs
│   │   ├── {role}_agent.py        # Factory: create_{role}()
│   │   └── llm_config.py          # Centralized LLM loader
│   │
│   ├── crews/                     # Crew compositions
│   │   └── {purpose}_crew.py      # {Purpose}Crew class
│   │
│   ├── tools/                     # Deterministic data tools
│   │   └── {function}_tool.py     # Tool functions
│   │
│   ├── flows/                     # CrewAI Flow orchestration
│   │   └── {purpose}_flow.py      # Multi-crew orchestration
│   │
│   ├── models/                    # Pydantic models (ALL I/O)
│   │   ├── inputs.py              # Request models
│   │   ├── outputs.py             # Response models
│   │   └── domain.py              # Domain entities
│   │
│   ├── services/                  # Data loading, caching
│   ├── routers/                   # Modular FastAPI endpoints
│   │   ├── api.py                 # Router aggregation + health
│   │   ├── flow.py                # Recommendation pipeline
│   │   ├── chat.py                # Raja conversation
│   │   ├── drinks.py              # Drink catalog
│   │   └── bottles.py             # Bottle suggestions
│   └── utils/                     # Shared utilities
│       └── parsing.py             # Request/response parsing
│
├── tests/                         # Mirror src/ structure
│   ├── conftest.py                # Shared fixtures, mocks
│   ├── agents/
│   ├── crews/
│   ├── tools/
│   └── flows/
│
├── data/                          # JSON/static data
└── scripts/                       # Build/utility scripts
```

---

## Implementation Patterns

### Agent Factory Pattern

```python
# src/app/agents/recipe_writer.py
from crewai import Agent, LLM
from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_default_llm

def create_recipe_writer(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    """Create Recipe Writer agent from YAML config."""
    config = get_agent_config("recipe_writer")

    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

### YAML Config Pattern

```yaml
# src/app/agents/config/agents.yaml
recipe_writer:
  role: "Recipe Writer"
  goal: "Generate clear, skill-appropriate recipes with technique tips"
  backstory: >
    You have taught thousands of home bartenders at every skill level.
    For beginners, you provide detailed technique explanations.
    For adventurous bartenders, you're concise and suggest variations.
  verbose: false
  allow_delegation: false

raja_bartender:
  role: "Raja - Your Bombay Bartender"
  goal: "Have personality-rich conversations about cocktails"
  backstory: >
    You are Raja, a bartender from Colaba, Bombay. You speak warm Hindi-English
    - use "yaar", "bhai", "acha", "bilkul". Keep responses SNAPPY - 2-3 sentences.
```

### Pydantic I/O Pattern

```python
# src/app/models/outputs.py
from pydantic import BaseModel, Field

class AnalysisOutput(BaseModel):
    """Structured output from analysis crew."""

    selected_drink: str = Field(..., description="Drink ID")
    candidates: list[dict] = Field(default_factory=list)
    mood_interpretation: str
    confidence_score: float = Field(ge=0.0, le=1.0)

class RecipeOutput(BaseModel):
    """Structured recipe from recipe crew."""

    name: str
    tagline: str
    ingredients: list[dict]
    instructions: list[str]
    technique_tips: list[str] = Field(default_factory=list)
```

### Tool Design Pattern

```python
# src/app/tools/recipe_db.py
from crewai.tools import tool
import json

@tool("search_recipes")
def search_recipes(
    cabinet: list[str],
    drink_type: str = "both",
) -> str:
    """
    Search for recipes matching cabinet ingredients.

    Args:
        cabinet: List of available ingredients
        drink_type: "cocktails", "mocktails", or "both"

    Returns:
        JSON string with matching recipes
    """
    # Deterministic logic - no LLM here
    matches = find_matching_recipes(cabinet, drink_type)
    return json.dumps({"matches": matches, "count": len(matches)})
```

### Error Handling Pattern

```python
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar("T")

def with_fallback(fallback_value: T) -> Callable:
    """Return fallback on failure instead of crashing."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return fallback_value
        return wrapper
    return decorator

@with_fallback(default_recipe_output)
async def get_recipe(drink_id: str) -> RecipeOutput:
    ...
```

---

## Testing Strategy

### Test Pyramid

```
              /\
             /  \   BDD Features (5%)
            /────\  User journeys
           /      \
          /────────\   Integration (20%)
         /          \  Crews, flows, API
        /────────────\
       /              \   Unit Tests (75%)
      /────────────────\  Models, tools, logic
```

### Always Mock LLM Calls

```python
# tests/conftest.py
import os
os.environ["ANTHROPIC_API_KEY"] = "test-key"  # Before imports!

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_llm_response():
    """Mock LLM that returns predictable responses."""
    mock = MagicMock()
    mock.raw = '{"response": "Mocked response"}'
    return mock

# tests/crews/test_raja_crew.py
@patch("src.app.crews.raja_chat_crew.Crew")
def test_crew_returns_valid_output(mock_crew_class, mock_llm_response):
    mock_crew_class.return_value.kickoff.return_value = mock_llm_response
    # Test crew behavior, not LLM
```

### BDD with Gherkin

```gherkin
# tests/features/recommendation.feature
Feature: Drink Recommendation

  Scenario: Minimal cabinet gets valid recommendation
    Given my cabinet contains:
      | ingredient    |
      | bourbon       |
      | lemons        |
    When I request a recommendation
    Then I receive a cocktail recommendation
    And the recipe uses only cabinet ingredients
```

### Coverage Targets

| Layer | Target | Rationale |
|-------|--------|-----------|
| Models | 100% | Contract layer |
| Tools | 90%+ | Deterministic |
| Agents | 80%+ | With mocks |
| Overall | 70%+ | CI enforced |

---

## Quality & Observability

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: detect-private-key  # Critical for API keys
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
jobs:
  lint:
    steps:
      - run: uv run ruff check src tests
      - run: uv run mypy src

  test:
    steps:
      - run: uv run pytest --cov=src --cov-fail-under=70
        env:
          ANTHROPIC_API_KEY: test-key  # NEVER real keys
```

### Cost Tracking

```python
@dataclass
class LLMCostTracker:
    HAIKU_INPUT: ClassVar[float] = 0.00025   # per 1K tokens
    HAIKU_OUTPUT: ClassVar[float] = 0.00125

    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def record_call(self, input_tokens: int, output_tokens: int) -> float:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        return (input_tokens/1000 * self.HAIKU_INPUT +
                output_tokens/1000 * self.HAIKU_OUTPUT)
```

---

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Agent files | `{role}_agent.py` | `recipe_writer.py` |
| Agent factories | `create_{role}()` | `create_recipe_writer()` |
| Crew classes | `{Purpose}Crew` | `AnalysisCrew` |
| Tool functions | `{verb}_{noun}()` | `search_recipes()` |
| Input models | `{Purpose}Request` | `AnalysisRequest` |
| Output models | `{Purpose}Output` | `AnalysisOutput` |

---

## Checklist

### Before Starting
- [ ] Define what's Agent vs Tool vs Code
- [ ] Choose model tier for each agent
- [ ] Plan crew composition (sequential/parallel)
- [ ] Design Pydantic I/O models

### During Development
- [ ] Agent configs in YAML, not hardcoded
- [ ] Factory functions for all agents
- [ ] Pydantic for all boundaries
- [ ] Mock LLM in all tests

### Before Deploy
- [ ] 70%+ test coverage
- [ ] Pre-commit hooks pass
- [ ] No real API keys in tests
- [ ] Rate limiting configured
- [ ] Error handling with fallbacks

---

*Blueprint v2.0 — Based on Cocktail Cache patterns (761 tests, 78% coverage)*
