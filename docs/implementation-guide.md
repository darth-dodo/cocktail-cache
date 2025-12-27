# Cocktail Cache - Implementation Guide

> **Build Order**: Data → Tools → Agents → Crews → Flow → API → UI
>
> Each layer depends only on layers above it. Test each before moving on.

---

## Quick Start

```bash
# Week 1: Foundation
cd cocktail-cache
uv sync

# Week 2-3: Build & Test
uv run python scripts/compute_unlock_scores.py
uv run pytest tests/tools/
uv run pytest tests/agents/

# Week 4-5: Run & Deploy
uv run uvicorn src.app.main:app --reload
git push origin main  # Render auto-deploys from main branch
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

## Week 2: CrewAI Core

### Models (Pydantic)

```
src/app/models/
├── __init__.py
├── cabinet.py      # Cabinet, Ingredient
├── cocktail.py     # CocktailMatch, FlavorProfile
├── recipe.py       # Recipe, RecipeStep, TechniqueTip
├── recommendation.py  # Recommendation, BottleRec
├── user_prefs.py   # SkillLevel, DrinkType
└── history.py      # HistoryEntry, RecipeHistory
```

**Key Model: `Recipe`**

```python
class Recipe(BaseModel):
    id: str
    name: str
    tagline: str
    why: str  # Why this drink for this mood
    flavor_profile: FlavorProfile
    ingredients: list[RecipeIngredient]
    prep: list[PrepStep] = []
    method: list[RecipeStep]
    glassware: str
    garnish: str
    timing: str
    difficulty: str  # "easy" | "medium" | "advanced"
    technique_tips: list[TechniqueTip]  # Adapted based on skill level
    variations: list[Variation]
    is_mocktail: bool = False
```

**Key Model: `UserPreferences`** (loaded from local storage)

```python
class UserPreferences(BaseModel):
    skill_level: str = "intermediate"  # "beginner" | "intermediate" | "adventurous"
    drink_type: str = "cocktail"  # "cocktail" | "mocktail" | "both"
    exclude_count: int = 5  # How many recent drinks to exclude
```

**Key Model: `HistoryEntry`**

```python
class HistoryEntry(BaseModel):
    recipe_id: str
    recipe_name: str
    made_at: datetime
    is_mocktail: bool = False
```

### Tools

```
src/app/tools/
├── __init__.py
├── recipe_db.py         # Query cocktails, get recipes
├── flavor_profiler.py   # Get flavor profiles
├── substitution_finder.py  # Find ingredient swaps
└── unlock_calculator.py    # Calculate bottle ROI
```

**All tools are deterministic** - they query pre-computed JSON data.

### Agents

```
src/app/agents/
├── __init__.py
├── cabinet_analyst.py   # Finds makeable cocktails
├── mood_matcher.py      # Ranks by mood fit
├── recipe_writer.py     # Generates full recipes
└── bottle_advisor.py    # Recommends next purchase
```

**Agent Pattern:**

```python
from crewai import Agent

def create_cabinet_analyst() -> Agent:
    return Agent(
        role="Cabinet Analyst",
        goal="Identify all drinks makeable with available ingredients",
        backstory="You know every classic cocktail's and mocktail's ingredients...",
        tools=[RecipeDBTool()],
        verbose=True
    )

def create_recipe_writer() -> Agent:
    return Agent(
        role="Recipe Writer",
        goal="Generate clear, skill-appropriate recipes with technique tips",
        backstory="""You've taught thousands of home bartenders at every level.
        For beginners, you explain techniques in detail. For adventurous users,
        you're concise and suggest variations.""",
        tools=[RecipeDBTool(), SubstitutionFinderTool()],
        verbose=True
    )
```

---

## Week 3: Crews & Flow

### Crews

```
src/app/crews/
├── __init__.py
├── analysis_crew.py   # Cabinet Analyst → Mood Matcher
└── recipe_crew.py     # Recipe Writer → Bottle Advisor
```

**Crew Pattern:**

```python
from crewai import Crew, Task

def create_analysis_crew():
    analyst = create_cabinet_analyst()
    matcher = create_mood_matcher()

    task1 = Task(
        description="Analyze cabinet: {cabinet}",
        agent=analyst
    )
    task2 = Task(
        description="Rank for mood: {mood}",
        agent=matcher,
        context=[task1]
    )

    return Crew(
        agents=[analyst, matcher],
        tasks=[task1, task2]
    )
```

### Flow

```python
# src/app/flows/cocktail_flow.py

class CocktailFlowState(BaseModel):
    session_id: str
    cabinet: list[str]
    mood: str
    constraints: list[str] = []

    # New: User preferences
    drink_type: str = "cocktail"  # "cocktail" | "mocktail" | "both"
    skill_level: str = "intermediate"  # "beginner" | "intermediate" | "adventurous"

    # New: History (recipe IDs to exclude)
    recent_history: list[str] = []

    candidates: list[dict] = []
    selected: str | None = None
    recipe: dict | None = None
    next_bottle: dict | None = None
    rejected: list[str] = []

class CocktailFlow(Flow[CocktailFlowState]):

    @start()
    def receive_input(self):
        return self.state

    @listen(receive_input)
    def analyze(self):
        crew = create_analysis_crew()
        result = crew.kickoff(inputs={
            "cabinet": self.state.cabinet,
            "mood": self.state.mood,
            "drink_type": self.state.drink_type,
            "skill_level": self.state.skill_level,
            "exclude": self.state.recent_history + self.state.rejected
        })
        # Update state
        return self.state

    @listen(analyze)
    def generate_recipe(self):
        crew = create_recipe_crew()
        result = crew.kickoff(inputs={
            "cocktail_id": self.state.selected,
            "skill_level": self.state.skill_level  # For tip adaptation
        })
        return self.state
```

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

### Week 1
- [ ] Project structure (`src/` layout)
- [ ] `pyproject.toml` configured
- [ ] `uv sync` installs all dependencies
- [ ] 50 cocktails in DB
- [ ] 20+ mocktails in DB
- [ ] Difficulty tags on all recipes
- [ ] Ingredients categorized
- [ ] Unlock scores computed (cocktails + mocktails)

### Week 2
- [ ] Pydantic models (including UserPrefs, HistoryEntry)
- [ ] 4 tools working
- [ ] 4 agents defined
- [ ] Skill-level awareness in Recipe Writer
- [ ] Tool tests passing (`uv run pytest tests/tools/`)

### Week 3
- [ ] Analysis Crew (with drink_type, skill_level, exclude)
- [ ] Recipe Crew (with skill-adapted tips)
- [ ] Flow orchestration
- [ ] Crew tests passing (`uv run pytest tests/agents/`)

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

*Implementation Guide v1.1*
*Applies BLUEPRINT.md patterns to Cocktail Cache*
*Updated: uv for package management, Render for deployment*
