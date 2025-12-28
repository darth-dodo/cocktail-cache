# Cocktail Cache

**Your cabinet. Your mood. Your perfect drink.**

An AI-powered home bar advisor that helps you craft great cocktails with whatever bottles you have. Chat with Raja, your AI mixologist, to get personalized drink recommendations, technique guidance, and smart suggestions for your next bottle purchase.

---

## Development Status

> **Current Phase**: Week 5 UX Improvements Complete

| Component | Status | Details |
|-----------|--------|---------|
| Data Layer | ✅ Complete | 103 cocktails, 39 mocktails, 180 ingredients |
| Pydantic Models | ✅ Complete | Structured crew I/O with RecipeOutput, AnalysisOutput, BottleAdvisorOutput |
| CrewAI Agents | ✅ Complete | 5 agents including unified Drink Recommender for fast mode |
| CrewAI Tools | ✅ Complete | 4 deterministic tools for data operations |
| Crews & Flow | ✅ Complete | Analysis Crew (fast mode), Recipe Crew, CocktailFlow |
| API Routes | ✅ Complete | FastAPI endpoints with session management |
| Chat UI | ✅ Complete | Conversational interface with Raja the AI Mixologist |
| Browse & Search | ✅ Complete | Full drink catalog with search, filters, and detail pages |
| Deployment | ✅ Complete | Render.com with GitHub Actions CI/CD |

---

## Features

### AI-Powered Recommendations
- **Chat with Raja** - Conversational AI mixologist that guides you to your perfect drink
- **AI-powered recommendations** - Get drinks matched to your available ingredients and mood
- **Fast mode analysis** - Single-agent mode for ~50% faster recommendations
- **Skill level adaptation** - Beginner-friendly recipes to adventurous techniques
- **"Next bottle" recommendations** - Maximize your drink potential with smart ROI suggestions

### Browse and Discover
- **142 drinks catalog** - Browse 103 cocktails and 39 mocktails with detailed recipes
- **Search and filter** - Find drinks by name, tags, or ingredients
- **Filter by type** - Toggle between cocktails, mocktails, or view all
- **Filter by difficulty** - Easy, medium, or advanced recipes
- **Individual drink pages** - Detailed view with ingredients, instructions, and tips

### User Experience
- **Tabbed navigation** - Switch between Chat, Cabinet, and Browse views
- **Ingredient autocomplete** - Smart suggestions when building your cabinet
- **Mixology facts loading screen** - Learn cocktail history while waiting
- **Mobile-first design** - Optimized for use in the kitchen
- **Mocktail support** - Spirit-free options for non-alcoholic preferences

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12 |
| API Framework | FastAPI |
| AI Orchestration | CrewAI |
| LLM Provider | Anthropic Claude |
| Frontend | HTMX + Jinja2 |
| Package Manager | uv |
| Deployment | Render |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/darth-dodo/cocktail-cache.git
cd cocktail-cache

# Copy environment file and add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install dependencies and start development server
make install
make dev

# Visit http://localhost:8888
```

---

## Usage

### Chat with Raja
1. Open the **Chat** tab
2. Add ingredients to your cabinet (with autocomplete suggestions)
3. Set your mood, skill level, and drink preference
4. Get personalized recommendations from Raja, your AI mixologist
5. View detailed recipes with technique tips and "next bottle" suggestions

### Browse the Catalog
1. Open the **Browse** tab to see all 142 drinks
2. **Search** by drink name, tags, or ingredients
3. **Filter by type**: All, Cocktails only, or Mocktails only
4. **Filter by difficulty**: Easy, Medium, or Advanced
5. Click any drink card to view the full recipe and instructions

### Build Your Cabinet
1. Open the **Cabinet** tab
2. Add ingredients using the autocomplete search
3. Your cabinet is saved and used for AI recommendations

---

## Development Commands

| Command | Description |
|---------|-------------|
| `make install` | Install project dependencies with uv |
| `make dev` | Start development server with hot reload |
| `make test` | Run test suite |
| `make check` | Run linting and type checks |
| `make format` | Format code with ruff |
| `make clean` | Remove build artifacts and caches |

---

## Project Structure

```
cocktail-cache/
├── src/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── config.py            # Environment configuration
│       ├── agents/              # CrewAI agent definitions
│       ├── crews/               # Crew compositions
│       ├── tools/               # CrewAI tools (RecipeDB, etc.)
│       ├── flows/               # Flow orchestration
│       ├── models/              # Pydantic models (Drink, Ingredient, etc.)
│       ├── services/            # Data loading and business logic
│       ├── routers/             # API routes
│       ├── templates/           # Jinja2 templates
│       └── static/              # CSS and JS assets
├── data/
│   ├── cocktails.json           # 103 cocktail recipes
│   ├── mocktails.json           # 39 non-alcoholic recipes
│   ├── ingredients.json         # 180 categorized ingredients
│   ├── substitutions.json       # Ingredient swap rules
│   └── unlock_scores.json       # Pre-computed bottle ROI mappings
├── scripts/
│   ├── compute_unlock_scores.py # Generate bottle recommendations
│   └── validate_data.py         # Pydantic data validation
├── tests/                       # Test suite
└── tasks.md                     # Development task tracker
```

---

## Data Validation

Run the validation script to verify all data files:

```bash
uv run python scripts/validate_data.py
```

To recompute unlock scores after modifying recipes:

```bash
uv run python scripts/compute_unlock_scores.py
```

---

## Deployment

This project is configured for deployment on Render using the included `render.yaml` configuration.

---

## Using the Agents

The CrewAI agents can be used directly for testing and development:

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

# Option 1: Use the high-level flow (recommended)
from src.app.flows import run_cocktail_flow

result = run_cocktail_flow(
    cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
    mood="unwinding after a long week",
    skill_level="intermediate",
    drink_type="cocktail",
)
print(f"Selected: {result.selected}")
print(f"Recipe: {result.recipe}")
print(f"Next bottle: {result.next_bottle}")

# Option 2: Use individual crews with fast mode (default)
from src.app.crews import run_analysis_crew, run_recipe_crew

# Run analysis crew in fast mode (~50% faster)
analysis_result = run_analysis_crew(
    cabinet=["bourbon", "lemons", "honey", "simple-syrup"],
    mood="unwinding after a long week",
    skill_level="intermediate",
    drink_type="cocktail",
    fast_mode=True,  # Default: uses unified Drink Recommender agent
)
for candidate in analysis_result.candidates:
    print(f"{candidate.name}: {candidate.mood_score}% match")

# Run recipe crew (optionally skip bottle advice for faster response)
recipe_result = run_recipe_crew(
    cocktail_id="gold-rush",
    skill_level="beginner",
    cabinet=["bourbon", "lemons", "honey"],
    include_bottle_advice=False,  # Skip bottle recommendations
)
print(f"Recipe: {recipe_result.recipe.name}")
```

### Available Components

#### Flows
| Flow | Purpose | Crews Used |
|------|---------|------------|
| CocktailFlow | Full recommendation pipeline | Analysis → Recipe |

#### Crews
| Crew | Mode | Purpose |
|------|------|---------|
| Analysis Crew | Fast (default) | Single Drink Recommender agent (~50% faster) |
| Analysis Crew | Full | Cabinet Analyst → Mood Matcher (detailed analysis) |
| Recipe Crew | Standard | Recipe Writer → Bottle Advisor |
| Recipe Crew | Recipe Only | Recipe Writer (skip bottle advice) |

#### Agents
| Agent | Purpose | Primary Tool |
|-------|---------|--------------|
| Drink Recommender | Find and rank drinks in one call (fast mode) | RecipeDBTool, FlavorProfilerTool |
| Cabinet Analyst | Find makeable drinks from cabinet | RecipeDBTool |
| Mood Matcher | Rank drinks by mood fit | FlavorProfilerTool |
| Recipe Writer | Generate skill-appropriate recipes | RecipeDBTool, SubstitutionFinderTool |
| Bottle Advisor | Recommend next bottle purchase | UnlockCalculatorTool |

#### Structured Output Models
| Model | Purpose |
|-------|---------|
| AnalysisOutput | Crew output with ranked drink candidates |
| RecipeOutput | Complete recipe with technique tips |
| BottleAdvisorOutput | Bottle recommendations with ROI data |
| RecipeCrewOutput | Combined recipe + bottle advice |

### Environment Variables

```bash
# Required for running agents
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Documentation

- [Architecture](docs/architecture.md) - System design and agent specifications
- [Implementation Guide](docs/implementation-guide.md) - Build order and weekly milestones
- [Tasks](tasks.md) - Development task tracker with phase status

---

## License

MIT
