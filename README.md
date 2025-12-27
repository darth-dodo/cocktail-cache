# Cocktail Cache

**Your cabinet. Your mood. Your perfect drink.**

An AI-powered home bar advisor that helps you craft great cocktails with whatever bottles you have. Enter your cabinet contents and mood, get personalized drink recommendations, technique guidance, and smart suggestions for your next bottle purchase.

---

## Development Status

> **Current Phase**: Week 2 Complete → Week 3 Crews & Flow (Next)

| Component | Status | Details |
|-----------|--------|---------|
| Data Layer | ✅ Complete | 50 cocktails, 24 mocktails, 134 ingredients |
| Pydantic Models | ✅ Complete | Cabinet, Recipe, UserPrefs, History + Phase 1 models |
| Project Structure | ✅ Complete | FastAPI skeleton, tests, scripts |
| CrewAI Agents | ✅ Complete | 4 agents with Claude Haiku (Anthropic) |
| CrewAI Tools | ✅ Complete | 4 deterministic tools for data operations |
| Crews & Flow | 🔲 Pending | Week 3 |
| API Routes | 🔲 Pending | Week 4 |
| UI/HTMX | 🔲 Pending | Week 5 |

---

## Features

- **AI-powered cocktail recommendations** - Get drinks matched to your available ingredients
- **Mood-based drink matching** - Unwinding, celebrating, or hosting? We've got you covered
- **Skill level adaptation** - Beginner-friendly recipes to adventurous techniques
- **Mocktail support** - Spirit-free options for non-alcoholic preferences
- **"Next bottle" recommendations** - Maximize your drink potential with smart ROI suggestions
- **Recipe history tracking** - Remember what you made and avoid recent repeats
- **Mobile-first design** - Optimized for use in the kitchen

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
git clone https://github.com/your-username/cocktail-cache.git
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
│   ├── cocktails.json           # 50 cocktail recipes
│   ├── mocktails.json           # 24 non-alcoholic recipes
│   ├── ingredients.json         # 134 categorized ingredients
│   ├── substitutions.json       # 118 ingredient swap rules
│   └── unlock_scores.json       # Pre-computed bottle ROI (293 mappings)
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
    Find all cocktails and mocktails that can be made with these ingredients.
    The user prefers cocktails and has intermediate skill level.""",
    expected_output="List of makeable drinks with match scores",
    agent=cabinet_analyst,
)

rank_task = Task(
    description="""The user's mood is 'unwinding after a long week'.
    Rank the candidate drinks by how well they fit this mood.
    Consider flavor profiles and complexity.""",
    expected_output="Ranked list of drinks with explanations",
    agent=mood_matcher,
    context=[analyze_task],  # Uses output from analyze_task
)

# Create crew and run
crew = Crew(
    agents=[cabinet_analyst, mood_matcher],
    tasks=[analyze_task, rank_task],
    verbose=True,
)
result = crew.kickoff()
print(result)
```

### Available Agents

| Agent | Purpose | Primary Tool |
|-------|---------|--------------|
| Cabinet Analyst | Find makeable drinks from cabinet | RecipeDBTool |
| Mood Matcher | Rank drinks by mood fit | FlavorProfilerTool |
| Recipe Writer | Generate skill-appropriate recipes | RecipeDBTool, SubstitutionFinderTool |
| Bottle Advisor | Recommend next bottle purchase | UnlockCalculatorTool |

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
