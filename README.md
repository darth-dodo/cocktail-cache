# Cocktail Cache

**Your cabinet. Your mood. Your perfect drink.**

An AI-powered home bar advisor that helps you craft great cocktails with whatever bottles you have. Enter your cabinet contents and mood, get personalized drink recommendations, technique guidance, and smart suggestions for your next bottle purchase.

---

## Development Status

> **Current Phase**: Week 1 Complete → Week 2 CrewAI Core (Next)

| Component | Status | Details |
|-----------|--------|---------|
| Data Layer | ✅ Complete | 50 cocktails, 24 mocktails, 134 ingredients |
| Pydantic Models | ✅ Complete | Drink, Ingredient, UnlockScores models |
| Project Structure | ✅ Complete | FastAPI skeleton, tests, scripts |
| CrewAI Agents | 🔲 Pending | Week 2 |
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

## Documentation

- [Tasks](tasks.md) - Development task tracker with phase status

---

## License

MIT
