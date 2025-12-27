# Cocktail Cache - Implementation Guide

> **Build Order**: Data → Tools → Agents → Crews → Flow → API → UI
>
> Each layer depends only on layers above it. Test each before moving on.

---

## Quick Start

```bash
# Setup
cd cocktail-cache
uv sync
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run Tests (339 tests, 87% coverage)
uv run pytest

# Run specific test suites
uv run pytest tests/tools/
uv run pytest tests/agents/
uv run pytest tests/models/
uv run pytest tests/crews/
uv run pytest tests/flows/

# Development Server
uv run uvicorn src.app.main:app --reload
```

---

## Using the Agents

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

from crewai import Crew, Task
from src.app.agents import create_cabinet_analyst, create_mood_matcher
from src.app.tools import RecipeDBTool, FlavorProfilerTool

# Create tools
recipe_db = RecipeDBTool()
flavor_profiler = FlavorProfilerTool()

# Create agents with tools
cabinet_analyst = create_cabinet_analyst(tools=[recipe_db])
mood_matcher = create_mood_matcher(tools=[flavor_profiler])

# Define tasks
analyze_task = Task(
    description="""Analyze cabinet contents: bourbon, lemons, honey, simple-syrup.
    Find all cocktails that can be made with these ingredients.""",
    expected_output="List of makeable drinks",
    agent=cabinet_analyst,
)

rank_task = Task(
    description="""Rank drinks for mood: 'unwinding after a long week'.""",
    expected_output="Ranked list with explanations",
    agent=mood_matcher,
    context=[analyze_task],
)

# Run the crew
crew = Crew(agents=[cabinet_analyst, mood_matcher], tasks=[analyze_task, rank_task])
result = crew.kickoff()
```

---

## Week 1: Foundation

### Day 1-2: Project Setup

This project uses `uv` for Python package management and follows a `src/` layout.

```bash
# Initialize project (already done - pyproject.toml exists)
uv init

# Create structure
mkdir -p src/app/{agents,crews,tools,flows,models,routers,templates/components,static}
mkdir -p data tests/{features,steps,agents,tools,integration} scripts
```

**Core Files:**

```
src/app/
├── main.py              # FastAPI entry point
├── config.py            # Environment config (ANTHROPIC_API_KEY, etc.)
└── __init__.py

pyproject.toml:
[project]
dependencies = [
    "crewai>=0.80.0",
    "crewai-tools>=0.14.0",
    "anthropic>=0.39.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "jinja2>=3.1.2",
    "pydantic>=2.5.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-bdd>=7.0.0",
]
```

**Install dependencies:**

```bash
uv sync  # Installs all dependencies from pyproject.toml
```

### Day 3-5: Data Layer

**This is the foundation. Get it right.**

#### `data/cocktails.json` - Schema

```json
{
  "id": "gold-rush",
  "name": "Gold Rush",
  "tagline": "Whiskey sour's sophisticated cousin",
  "ingredients": [
    {"amount": "2", "unit": "oz", "item": "bourbon"},
    {"amount": "0.75", "unit": "oz", "item": "lemon-juice"},
    {"amount": "0.75", "unit": "oz", "item": "honey-syrup"}
  ],
  "method": [
    {"action": "Combine", "detail": "Add all to shaker"},
    {"action": "Shake", "detail": "12-15 seconds with ice"},
    {"action": "Strain", "detail": "Into chilled coupe"}
  ],
  "glassware": "coupe",
  "garnish": "lemon twist",
  "flavor_profile": {"sweet": 40, "sour": 50, "bitter": 10, "spirit": 60},
  "tags": ["whiskey", "citrus", "easy"],
  "difficulty": "easy",
  "timing_minutes": 3,
  "is_mocktail": false
}
```

**Target: 50 cocktails** covering major spirit categories.

#### `data/mocktails.json` - Schema

```json
{
  "id": "honey-ginger-fizz",
  "name": "Honey Ginger Fizz",
  "tagline": "Bright and refreshing without the spirits",
  "ingredients": [
    {"amount": "1", "unit": "oz", "item": "honey-syrup"},
    {"amount": "1", "unit": "oz", "item": "lemon-juice"},
    {"amount": "0.5", "unit": "oz", "item": "ginger-juice"},
    {"amount": "4", "unit": "oz", "item": "soda-water"}
  ],
  "method": [
    {"action": "Combine", "detail": "Add honey, lemon, ginger to shaker"},
    {"action": "Shake", "detail": "10 seconds with ice"},
    {"action": "Strain", "detail": "Into highball over fresh ice"},
    {"action": "Top", "detail": "With soda water, stir gently"}
  ],
  "glassware": "highball",
  "garnish": "lemon wheel, candied ginger",
  "flavor_profile": {"sweet": 45, "sour": 40, "bitter": 5, "spirit": 0},
  "tags": ["citrus", "ginger", "refreshing", "easy"],
  "difficulty": "easy",
  "timing_minutes": 3,
  "is_mocktail": true
}
```

**Target: 20+ mocktails** using common fresh ingredients and mixers.

#### `data/ingredients.json` - Structure

```json
{
  "spirits": [
    {"id": "bourbon", "names": ["bourbon", "bourbon whiskey"]},
    {"id": "gin", "names": ["gin", "london dry"]}
  ],
  "modifiers": [
    {"id": "sweet-vermouth", "names": ["sweet vermouth"]}
  ],
  "bitters_syrups": [
    {"id": "angostura", "names": ["angostura", "ango"]}
  ],
  "fresh": [
    {"id": "lemon-juice", "names": ["lemon juice", "lemon"]}
  ],
  "mixers": [
    {"id": "soda-water", "names": ["soda", "club soda"]}
  ]
}
```

#### `scripts/compute_unlock_scores.py`

```python
"""Pre-compute which bottles unlock which cocktails AND mocktails."""
import json
from collections import defaultdict

def main():
    # Load both cocktails and mocktails
    with open("data/cocktails.json") as f:
        cocktails = json.load(f)
    with open("data/mocktails.json") as f:
        mocktails = json.load(f)

    all_drinks = cocktails + mocktails

    bottle_unlocks = defaultdict(list)
    for c in all_drinks:
        ingredients = {i["item"] for i in c["ingredients"]}
        for ing in ingredients:
            bottle_unlocks[ing].append({
                "id": c["id"],
                "name": c["name"],
                "is_mocktail": c.get("is_mocktail", False),
                "other": list(ingredients - {ing})
            })

    with open("data/unlock_scores.json", "w") as f:
        json.dump(dict(bottle_unlocks), f, indent=2)

if __name__ == "__main__":
    main()
```

**Run with:**

```bash
uv run python scripts/compute_unlock_scores.py
```

---

## Week 2: CrewAI Core ✅ COMPLETE

### Models (Pydantic) ✅

```
src/app/models/
├── __init__.py          # Exports all models
├── cabinet.py           # Cabinet model
├── cocktail.py          # CocktailMatch model
├── recipe.py            # Recipe, RecipeStep, TechniqueTip
├── recommendation.py    # Recommendation, BottleRec
├── user_prefs.py        # SkillLevel, DrinkType, UserPreferences
└── history.py           # HistoryEntry, RecipeHistory
```

### Tools ✅

```
src/app/tools/
├── __init__.py              # Tool exports
├── recipe_db.py             # RecipeDBTool - query drinks by ingredients
├── flavor_profiler.py       # FlavorProfilerTool - analyze flavor profiles
├── substitution_finder.py   # SubstitutionFinderTool - find ingredient swaps
└── unlock_calculator.py     # UnlockCalculatorTool - calculate bottle ROI
```

**All tools are deterministic** - they query pre-computed JSON data and return JSON strings.

### Agents ✅

```
src/app/agents/
├── __init__.py          # Factory exports + LLM config
├── llm_config.py        # Centralized Claude Haiku configuration
├── cabinet_analyst.py   # Finds makeable cocktails
├── mood_matcher.py      # Ranks by mood fit
├── recipe_writer.py     # Generates full recipes
└── bottle_advisor.py    # Recommends next purchase
```

**LLM Configuration (Claude Haiku):**

```python
# src/app/agents/llm_config.py
from crewai import LLM

DEFAULT_MODEL = "anthropic/claude-3-5-haiku-20241022"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7

def get_default_llm() -> LLM:
    return LLM(model=DEFAULT_MODEL, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE)
```

**Agent Factory Pattern:**

```python
from crewai import LLM, Agent
from src.app.agents.llm_config import get_default_llm

def create_cabinet_analyst(
    tools: list | None = None,
    llm: LLM | None = None,
) -> Agent:
    return Agent(
        role="Cabinet Analyst",
        goal="Identify all drinks makeable with available ingredients",
        backstory="You are an expert mixologist...",
        tools=tools or [],
        llm=llm or get_default_llm(),
        verbose=False,
        allow_delegation=False,
    )
```

### Tests ✅

- **212 tests passing** with 90% coverage
- Agent factory tests in `tests/agents/test_agents.py`
- Tool unit tests in `tests/tools/test_tools.py`
- Model validation tests in `tests/models/`

Run tests:
```bash
uv run pytest                    # All tests
uv run pytest tests/agents/      # Agent tests only
uv run pytest tests/tools/       # Tool tests only
uv run pytest --cov=src/app      # With coverage
```

---

## Week 3: Crews & Flow ✅ COMPLETE

### Crews

```
src/app/crews/
├── __init__.py          # Exports: create_analysis_crew, create_recipe_crew, run_*
├── analysis_crew.py     # Cabinet Analyst → Mood Matcher
└── recipe_crew.py       # Recipe Writer → Bottle Advisor
```

**Crew Implementation (Actual):**

```python
# src/app/crews/analysis_crew.py
from crewai import Crew, Process, Task
from src.app.agents import create_cabinet_analyst, create_mood_matcher
from src.app.tools import FlavorProfilerTool, RecipeDBTool

def create_analysis_crew() -> Crew:
    """Create the Analysis Crew for cabinet analysis and mood matching."""
    recipe_db = RecipeDBTool()
    flavor_profiler = FlavorProfilerTool()

    cabinet_analyst = create_cabinet_analyst(tools=[recipe_db])
    mood_matcher = create_mood_matcher(tools=[flavor_profiler])

    analyze_task = Task(
        description="""Analyze cabinet: {cabinet}. Drink type: {drink_type}.
        Find all makeable drinks, excluding: {exclude}.""",
        expected_output="JSON list of makeable drinks with match scores",
        agent=cabinet_analyst,
    )

    match_task = Task(
        description="""Rank candidates for mood: {mood}.
        Skill level: {skill_level}. Exclude: {exclude}.""",
        expected_output="Ranked list ordered by mood fit",
        agent=mood_matcher,
        context=[analyze_task],  # Dependency on analyze_task
    )

    return Crew(
        agents=[cabinet_analyst, mood_matcher],
        tasks=[analyze_task, match_task],
        process=Process.sequential,
        verbose=False,
    )
```

### Flow

```python
# src/app/flows/cocktail_flow.py
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

class CocktailFlowState(BaseModel):
    """State container for the cocktail recommendation flow."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cabinet: list[str] = Field(default_factory=list)
    mood: str = ""
    constraints: list[str] = Field(default_factory=list)
    drink_type: str = "cocktail"
    skill_level: str = "intermediate"
    recent_history: list[str] = Field(default_factory=list)
    candidates: list[dict] = Field(default_factory=list)
    selected: str | None = None
    recipe: dict | None = None
    next_bottle: dict | None = None
    rejected: list[str] = Field(default_factory=list)
    error: str | None = None

class CocktailFlow(Flow[CocktailFlowState]):
    """Main flow orchestrating Analysis → Recipe crews."""

    @start()
    def receive_input(self) -> CocktailFlowState:
        # Normalize inputs, validate cabinet
        return self.state

    @listen(receive_input)
    def analyze(self) -> CocktailFlowState:
        # Run Analysis Crew, parse results
        crew = create_analysis_crew()
        result = crew.kickoff(inputs={...})
        # Update state.candidates
        return self.state

    @listen(analyze)
    def select(self) -> CocktailFlowState:
        # Select top candidate from ranked list
        return self.state

    @listen(select)
    def generate_recipe(self) -> CocktailFlowState:
        # Run Recipe Crew, parse results
        crew = create_recipe_crew()
        result = crew.kickoff(inputs={...})
        return self.state

# Convenience functions
def run_cocktail_flow(...) -> CocktailFlowState:
    """Run the complete cocktail recommendation flow."""
    flow = CocktailFlow()
    return flow.kickoff(inputs={...})

def request_another(state: CocktailFlowState) -> CocktailFlowState:
    """Handle 'show me something else' by adding to rejected list."""
    ...
```

### Tests

- **127 tests** for crews and flows
- Tests verify crew configuration, tool assignments, task dependencies
- Tests use mocking to avoid LLM calls
- Run: `uv run pytest tests/crews/ tests/flows/ -v`

---

## Week 4: API & Integration

### FastAPI Routes

```python
# src/app/routers/api.py

@router.post("/recommend")
async def recommend(request: RecommendRequest):
    state = CocktailFlowState(
        session_id=str(uuid.uuid4()),
        cabinet=request.cabinet,
        mood=request.mood,
        constraints=request.constraints,
        drink_type=request.drink_type,  # "cocktail" | "mocktail" | "both"
        skill_level=request.skill_level,  # "beginner" | "intermediate" | "adventurous"
        recent_history=request.recent_history  # Recipe IDs from local storage
    )
    flow = CocktailFlow()
    result = flow.kickoff(state)
    return {"session_id": state.session_id, "recommendation": result}

@router.post("/another")
async def another(request: AnotherRequest):
    # Get session, add rejected, re-run flow
    pass

@router.post("/made")
async def mark_made(request: MarkMadeRequest):
    """Called when user clicks 'I made this'. Client-side adds to history."""
    return {"status": "ok", "recipe_id": request.recipe_id, "made_at": datetime.now()}
```

### Session Management

```python
# Simple in-memory for MVP
sessions: dict[str, CocktailFlowState] = {}

# YAGNI: Redis only if we need persistence
```

---

## Week 5: UI & Deploy

### HTMX Frontend

```html
<form hx-post="/api/recommend"
      hx-target="#result"
      hx-indicator="#loading">

  <!-- Drink type toggle: Cocktail / Mocktail / Both -->
  {% include "components/drink_type_toggle.html" %}

  <!-- Skill level selector -->
  {% include "components/skill_selector.html" %}

  <!-- Cabinet grid with collapsible categories -->
  {% include "components/cabinet_grid.html" %}

  <!-- Mood buttons -->
  {% include "components/mood_selector.html" %}

  <!-- Hidden: Recent history from local storage -->
  <input type="hidden" id="recent-history" name="recent_history" value="">

  <button type="submit">Make Me Something</button>
</form>

<div id="result">
  <!-- Recipe card renders here (includes "I made this" button) -->
</div>

<!-- Recently Made sidebar/section -->
{% include "components/history_list.html" %}
```

**Local Storage Schema:**

```javascript
// cocktail-cache-prefs
{
  "skill_level": "intermediate",
  "drink_type": "cocktail",
  "exclude_count": 5
}

// cocktail-cache-history
[
  {"recipe_id": "gold-rush", "name": "Gold Rush", "made_at": "2025-12-27T18:30:00Z", "is_mocktail": false},
  {"recipe_id": "negroni", "name": "Negroni", "made_at": "2025-12-25T20:00:00Z", "is_mocktail": false}
]
```

### Deployment (Render)

**1. Create `render.yaml` in project root:**

```yaml
services:
  - type: web
    name: cocktail-cache
    runtime: python
    buildCommand: pip install uv && uv sync
    startCommand: uv run uvicorn src.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.12"
      - key: ANTHROPIC_API_KEY
        sync: false  # Set manually in Render dashboard
    healthCheckPath: /health
```

**2. Deploy to Render:**

```bash
# Connect your GitHub repository to Render
# 1. Go to https://dashboard.render.com
# 2. New → Web Service → Connect your repo
# 3. Render auto-detects render.yaml

# Set environment variables in Render Dashboard:
# Settings → Environment → Add Environment Variable
#   ANTHROPIC_API_KEY = sk-ant-...

# Deploy happens automatically on push to main
git push origin main
```

**Alternative: Manual Render Setup (without render.yaml)**

1. Create a new Web Service on Render Dashboard
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install uv && uv sync`
   - **Start Command**: `uv run uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.12
4. Add environment variables in Settings:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key

---

## Testing Strategy

### BDD Features

```gherkin
# tests/features/recommendation.feature

Scenario: Minimal cabinet gets recommendation
  Given cabinet contains ["bourbon", "lemons", "honey"]
  And mood is "unwinding"
  When I request recommendation
  Then I receive a makeable cocktail
  And I receive next bottle suggestion
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test directories
uv run pytest tests/tools/
uv run pytest tests/agents/
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src/app
```

### Test Pyramid

```
Integration (10%)  - Full flow tests
      ^
Crew Tests (30%)   - Crew behavior tests
      ^
Agent Tests (30%)  - Agent output tests
      ^
Tool Tests (30%)   - Deterministic tool tests
```

---

## Performance Targets

| Metric | Target | How |
|--------|--------|-----|
| Time to recommendation | <8s | Pre-compute, limit LLM calls to 4 |
| Cost per request | <$0.10 | Use Haiku where possible |
| Mobile Lighthouse | 90+ | HTMX, minimal JS |

---

## Checklist

### Week 1 ✅ COMPLETE
- [x] Project structure (`src/` layout)
- [x] `pyproject.toml` configured
- [x] `uv sync` installs all dependencies
- [x] 50 cocktails in DB
- [x] 24 mocktails in DB (exceeded target of 20+)
- [x] Difficulty tags on all recipes (easy/medium/hard/advanced)
- [x] 134 ingredients categorized (6 categories)
- [x] Unlock scores computed (110 entries covering cocktails + mocktails)
- [x] Pydantic models for all data types
- [x] Data validation script (`scripts/validate_data.py`)
- [x] Pre-commit hooks configured (ruff, mypy)

### Week 2 ✅ COMPLETE
- [x] Pydantic models (Cabinet, Recipe, UserPrefs, History, Recommendation)
- [x] 4 tools working (RecipeDB, FlavorProfiler, SubstitutionFinder, UnlockCalculator)
- [x] 4 agents defined with Claude Haiku
- [x] LLM configuration centralized in `llm_config.py`
- [x] Tool tests passing (`uv run pytest tests/tools/`)
- [x] Agent tests passing (`uv run pytest tests/agents/`)
- [x] Model tests passing (`uv run pytest tests/models/`)
- [x] 212 tests total, 90% coverage

### Week 3 ✅ COMPLETE
- [x] Analysis Crew (Cabinet Analyst → Mood Matcher)
- [x] Recipe Crew (Recipe Writer → Bottle Advisor)
- [x] Flow orchestration (CocktailFlow with state management)
- [x] "Show me something else" rejection workflow
- [x] Crew tests passing (`uv run pytest tests/crews/`)
- [x] Flow tests passing (`uv run pytest tests/flows/`)
- [x] 127 new tests, 339 total tests, 87% coverage

### Week 4
- [ ] API endpoints (including /made)
- [ ] Session management
- [ ] Integration tests (`uv run pytest tests/integration/`)
- [ ] <8s latency
- [ ] Local storage (cabinet + skill + history)
- [ ] Recipe history UI

### Week 5
- [ ] HTMX frontend
- [ ] Drink type toggle (Cocktail/Mocktail/Both)
- [ ] Skill level selector
- [ ] "I made this" button + history list
- [ ] Mobile responsive
- [ ] `render.yaml` configured
- [ ] Deployed to Render

### Week 6
- [ ] Error handling
- [ ] Edge cases (empty history, no mocktails match, etc.)
- [ ] Documentation
- [ ] Ready for users

---

*Implementation Guide v1.2*
*Applies BLUEPRINT.md patterns to Cocktail Cache*
*Updated: Week 1 complete, uv for package management, Render for deployment*
*Last Updated: 2025-12-27*
