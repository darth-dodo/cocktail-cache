# Cocktail Cache - Implementation Guide

> **Build Order**: Data -> Tools -> Agents -> Crews -> Flow -> API -> UI
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

# Environment Variables
# Required:
#   ANTHROPIC_API_KEY=sk-ant-...
#
# Optional:
#   APP_ENV=development      # Options: development, staging, production, test
#   CREWAI_TRACING=false     # Enable flow tracing for debugging

# Run Tests (339 tests, 87% coverage)
uv run pytest

# Run specific test suites
uv run pytest tests/tools/
uv run pytest tests/agents/
uv run pytest tests/models/
uv run pytest tests/crews/
uv run pytest tests/flows/

# Development Server
uv run uvicorn src.app.main:app --reload --port 8888

# Visit http://localhost:8888 to chat with Raja
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

## Week 3: Crews & Flow (COMPLETE)

### Crews

```
src/app/crews/
├── __init__.py          # Exports: create_analysis_crew, create_recipe_crew, run_*
├── analysis_crew.py     # Fast mode (Drink Recommender) or Full mode (Cabinet Analyst → Mood Matcher)
└── recipe_crew.py       # Recipe Writer → Bottle Advisor (bottle advice optional)
```

**Analysis Crew with Fast Mode:**

```python
# src/app/crews/analysis_crew.py
from crewai import Crew, Process, Task
from src.app.agents import create_drink_recommender, create_cabinet_analyst, create_mood_matcher
from src.app.models import AnalysisOutput
from src.app.tools import FlavorProfilerTool, RecipeDBTool

def create_analysis_crew(fast_mode: bool = True) -> Crew:
    """Create the Analysis Crew for finding and ranking drinks.

    Args:
        fast_mode: If True (default), uses a single unified agent for faster
            response (~50% faster). If False, uses two sequential agents.

    Returns:
        Configured Crew ready for execution.

    Performance:
        - Fast mode: 1 LLM call, ~2-3 seconds
        - Full mode: 2 LLM calls, ~4-5 seconds
    """
    if fast_mode:
        # Single agent with both tools - 1 LLM call
        recipe_db = RecipeDBTool()
        flavor_profiler = FlavorProfilerTool()
        drink_recommender = create_drink_recommender(tools=[recipe_db, flavor_profiler])

        unified_task = Task(
            description="Find and rank the best drinks...",
            expected_output="AnalysisOutput JSON",
            agent=drink_recommender,
            output_pydantic=AnalysisOutput,
        )
        return Crew(agents=[drink_recommender], tasks=[unified_task], ...)
    else:
        # Two agents - 2 LLM calls (more detailed)
        # Cabinet Analyst → Mood Matcher pipeline
        ...

def run_analysis_crew(inputs: dict, fast_mode: bool = True) -> AnalysisOutput:
    """Run the Analysis Crew with the given inputs.

    Args:
        inputs: Dict with cabinet, mood, constraints, etc.
        fast_mode: If True (default), uses single-agent mode.

    Returns:
        AnalysisOutput with ranked drink candidates.
    """
    crew = create_analysis_crew(fast_mode=fast_mode)
    return crew.kickoff(inputs=inputs)
```

**Recipe Crew with Optional Bottle Advice:**

```python
# src/app/crews/recipe_crew.py
def create_recipe_crew(include_bottle_advice: bool = True) -> Crew:
    """Create the Recipe Crew.

    Args:
        include_bottle_advice: When False, skips the bottle advisor task
            to save processing time. Defaults to True.

    Returns:
        Configured Crew ready for execution.

    Performance:
        - With bottle advice (sequential): 2 LLM calls, ~3-4 seconds
        - With bottle advice (parallel): 2 LLM calls, ~1.5-2 seconds
        - Without bottle advice: 1 LLM call, ~1.5-2 seconds
    """
    ...

def run_recipe_crew(inputs: dict, include_bottle_advice: bool = True) -> RecipeCrewOutput:
    """Run the Recipe Crew with the given inputs.

    Args:
        inputs: Dict with selected drink, cabinet, skill_level, etc.
        include_bottle_advice: If True (default), includes bottle recommendations.

    Returns:
        RecipeCrewOutput with recipe and optional bottle advice.
    """
    crew = create_recipe_crew(include_bottle_advice=include_bottle_advice)
    return crew.kickoff(inputs=inputs)
```

**Parallel Crew Functions (for concurrent execution):**

```python
# src/app/crews/recipe_crew.py

def create_recipe_only_crew() -> Crew:
    """Create a crew with only the Recipe Writer task.

    Used for parallel execution where Recipe Writer and Bottle Advisor
    run concurrently via asyncio.gather().

    Returns:
        Crew configured with single Recipe Writer task.
    """
    recipe_tools = [RecipeDBTool(), SubstitutionFinderTool()]
    recipe_writer = create_recipe_writer(tools=recipe_tools)

    recipe_task = Task(
        description="...",
        agent=recipe_writer,
        output_pydantic=RecipeOutput,
    )

    return Crew(
        agents=[recipe_writer],
        tasks=[recipe_task],
        process=Process.sequential,
        verbose=False,
    )


def create_bottle_only_crew() -> Crew:
    """Create a crew with only the Bottle Advisor task.

    Used for parallel execution. This crew has no dependency on
    Recipe Writer output - it only needs cabinet and drink_type
    from the flow state.

    Returns:
        Crew configured with single Bottle Advisor task.
    """
    bottle_tools = [UnlockCalculatorTool()]
    bottle_advisor = create_bottle_advisor(tools=bottle_tools)

    bottle_task = Task(
        description="...",
        agent=bottle_advisor,
        output_pydantic=BottleAdvisorOutput,
        # NO context dependency - enables parallel execution
    )

    return Crew(
        agents=[bottle_advisor],
        tasks=[bottle_task],
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

    def __init__(self, fast_mode: bool = True, include_bottle_advice: bool = True):
        super().__init__()
        self.fast_mode = fast_mode
        self.include_bottle_advice = include_bottle_advice

    @start()
    def receive_input(self) -> CocktailFlowState:
        # Normalize inputs, validate cabinet
        return self.state

    @listen(receive_input)
    def analyze(self) -> CocktailFlowState:
        # Run Analysis Crew, parse results
        crew = create_analysis_crew(fast_mode=self.fast_mode)
        result = crew.kickoff(inputs={...})
        # Update state.candidates
        return self.state

    @listen(analyze)
    def select(self) -> CocktailFlowState:
        # Select top candidate from ranked list
        return self.state

    @listen(select)
    async def generate_recipe(self) -> CocktailFlowState:
        # Run Recipe Crew with optional parallel execution
        settings = get_settings()

        if settings.PARALLEL_CREWS and self.include_bottle_advice:
            # Parallel: Recipe Writer and Bottle Advisor run concurrently
            await self._generate_parallel()
        else:
            # Sequential: Original behavior
            crew = create_recipe_crew(include_bottle_advice=self.include_bottle_advice)
            result = crew.kickoff(inputs={...})
        return self.state

    async def _generate_parallel(self) -> None:
        """Run Recipe Writer and Bottle Advisor in parallel using asyncio.gather()."""
        recipe_crew = create_recipe_only_crew()
        bottle_crew = create_bottle_only_crew()

        recipe_result, bottle_result = await asyncio.gather(
            recipe_crew.kickoff_async(inputs={...}),
            bottle_crew.kickoff_async(inputs={...}),
            return_exceptions=True,
        )
        # Handle results and exceptions...

# Convenience functions
def run_cocktail_flow(
    cabinet: list[str],
    mood: str,
    fast_mode: bool = True,
    include_bottle_advice: bool = True,
    **kwargs
) -> CocktailFlowState:
    """Run the complete cocktail recommendation flow.

    Args:
        cabinet: List of available ingredients.
        mood: User's mood or occasion description.
        fast_mode: If True (default), uses single-agent analysis for faster response.
        include_bottle_advice: If True (default), includes next bottle recommendations.
        **kwargs: Additional parameters (constraints, skill_level, etc.)

    Returns:
        CocktailFlowState with complete recommendation.

    Performance Modes:
        - fast_mode=True, include_bottle_advice=False: ~3-4 seconds (2 LLM calls)
        - fast_mode=True, include_bottle_advice=True: ~5 seconds (3 LLM calls)
        - fast_mode=False, include_bottle_advice=True: ~8 seconds (4 LLM calls)
    """
    flow = CocktailFlow(fast_mode=fast_mode, include_bottle_advice=include_bottle_advice)
    return flow.kickoff(inputs={"cabinet": cabinet, "mood": mood, **kwargs})

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

## Week 4: API & UI (COMPLETE)

### Chat Interface with Raja

The application uses a conversational chat interface instead of a traditional form.
Raja, the AI mixologist, guides users through the recommendation process.

**Key Features:**
- Conversational flow: Cabinet -> Mood -> Skill -> Recommendations
- Mixology facts loading screen (20 cocktail history facts)
- Collapsible recipe sections for easy mobile viewing
- "Try Another" and "I Made This" actions

### FastAPI Endpoints

```python
# src/app/routers/api.py

@router.post("/api/recommend")
async def recommend(request: RecommendRequest):
    """Get drink recommendation based on cabinet and mood."""
    # Uses fast_mode=True by default for ~50% faster response
    ...

@router.post("/api/another")
async def another(request: AnotherRequest):
    """Get alternative recommendation, excluding previous."""
    ...
```

### Deployment (COMPLETE)

**Render.com Configuration** (`render.yaml`):
- Auto-deploy on push to main branch
- Python 3.12 with uv package manager
- Health check endpoint at `/health`
- Environment variables for API keys

**GitHub Actions CI/CD** (`.github/workflows/ci-cd.yml`):
- Lint and type checking (ruff, mypy)
- Test suite with coverage reporting
- Automatic deployment trigger to Render

### Structured Pydantic Models

The crews use typed Pydantic models for reliable I/O:

```python
# src/app/models/crew_io.py

class AnalysisOutput(BaseModel):
    """Output from Analysis Crew."""
    candidates: list[DrinkCandidate]
    total_found: int
    mood_summary: str

class RecipeOutput(BaseModel):
    """Output from Recipe Writer."""
    id: str
    name: str
    ingredients: list[RecipeIngredient]
    method: list[RecipeStep]
    technique_tips: list[TechniqueTip]
    ...

class BottleAdvisorOutput(BaseModel):
    """Output from Bottle Advisor."""
    recommendations: list[BottleRecommendation]
    total_new_drinks: int

class RecipeCrewOutput(BaseModel):
    """Combined output from Recipe Crew."""
    recipe: RecipeOutput
    bottle_advice: BottleAdvisorOutput
```

---

## Week 5-6: Polish & Documentation

### Remaining Tasks
- [ ] Error handling for edge cases
- [ ] Performance optimization profiling
- [ ] User guide documentation
- [ ] Demo video/screenshots

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
| Time to recommendation | <5s (fast mode) | Single-agent analysis, optional bottle advice |
| Cost per request | <$0.05 | Fast mode uses 2-3 LLM calls vs 4 |
| Mobile Lighthouse | 90+ | Vanilla JS, minimal dependencies |

### Configuration Options

| Parameter | Default | Effect |
|-----------|---------|--------|
| `fast_mode` | `True` | Uses unified Drink Recommender (1 LLM call) vs Cabinet Analyst + Mood Matcher (2 LLM calls) |
| `include_bottle_advice` | `True` | When False, skips bottle advisor step saving 1 LLM call |
| `PARALLEL_CREWS` | `True` | Environment variable. Runs Recipe Writer and Bottle Advisor concurrently |

### Performance by Mode

| Mode | LLM Calls | Latency | Best For |
|------|-----------|---------|----------|
| Fast + no bottle | 2 | ~3-4s | Quick recommendations |
| Fast + bottle (sequential) | 3 | ~5-6s | Fallback mode |
| Fast + bottle (parallel) | 3 | ~3-4s | Standard experience (default) |
| Full + bottle | 4 | ~6-8s | Detailed analysis |

### Parallel Execution

When `PARALLEL_CREWS=true` (the default), the Recipe Writer and Bottle Advisor execute concurrently:

```bash
# Enable parallel execution (default)
export PARALLEL_CREWS=true

# Disable for rollback
export PARALLEL_CREWS=false
```

This reduces latency by approximately 40% for requests with bottle advice.

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

### Week 3 (COMPLETE)
- [x] Analysis Crew with fast mode (Drink Recommender) and full mode
- [x] Recipe Crew with optional bottle advice
- [x] Structured Pydantic outputs (AnalysisOutput, RecipeOutput, BottleAdvisorOutput)
- [x] Flow orchestration (CocktailFlow with state management)
- [x] "Show me something else" rejection workflow
- [x] Crew tests passing (`uv run pytest tests/crews/`)
- [x] Flow tests passing (`uv run pytest tests/flows/`)
- [x] 127 new tests, 339 total tests, 87% coverage

### Week 4 (COMPLETE)
- [x] API endpoints (/recommend, /another)
- [x] Session management (in-memory)
- [x] Fast mode enabled by default (~50% faster)
- [x] Chat UI with Raja the AI Mixologist
- [x] Mixology facts loading screen (20 facts)
- [x] Fixed ingredient IDs matching database
- [x] Mobile responsive design

### Week 5 (COMPLETE)
- [x] Conversational chat interface (not HTMX form)
- [x] Drink type toggle (Cocktail/Mocktail/Both)
- [x] Skill level selector
- [x] "Try Another" and "I Made This" buttons
- [x] Collapsible recipe sections
- [x] `render.yaml` configured with proper uv commands
- [x] GitHub Actions CI/CD workflow
- [x] Deployed to Render

### Week 6 (IN PROGRESS)
- [ ] Error handling for edge cases
- [ ] Performance optimization profiling
- [ ] User documentation
- [ ] Demo video/screenshots

---

*Implementation Guide v1.5*
*Applies BLUEPRINT.md patterns to Cocktail Cache*
*Updated: Added PARALLEL_CREWS feature, parallel crew functions, updated performance tables*
*Last Updated: 2025-12-27*
