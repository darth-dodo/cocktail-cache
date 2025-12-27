# Cocktail Cache

**Your cabinet. Your mood. Your perfect drink.**

An AI-powered home bar advisor that helps you craft great cocktails with whatever bottles you have. Enter your cabinet contents and mood, get personalized drink recommendations, technique guidance, and smart suggestions for your next bottle purchase.

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
│       ├── models/              # Pydantic models
│       ├── routers/             # API routes
│       ├── templates/           # Jinja2 templates
│       └── static/              # CSS and JS assets
├── data/
│   ├── cocktails.json           # Cocktail recipe database
│   ├── mocktails.json           # Non-alcoholic recipes
│   ├── ingredients.json         # Categorized ingredients
│   ├── substitutions.json       # Ingredient swap mappings
│   └── unlock_scores.json       # Pre-computed bottle ROI
├── tests/                       # Test suite
├── scripts/                     # Build utilities
└── docs/
    ├── product.md               # Product requirements
    ├── architecture.md          # System architecture
    ├── implementation-guide.md  # Implementation details
    ├── BLUEPRINT.md             # Multi-agent AI service patterns
    └── tasks.md                 # Development task tracker
```

---

## Deployment

This project is configured for deployment on Render using the included `render.yaml` configuration.

See the [implementation guide](docs/implementation-guide.md) for detailed deployment instructions.

---

## Documentation

- [Product Requirements](docs/product.md) - Features, user stories, and success metrics
- [Architecture](docs/architecture.md) - System design, agents, and data flow
- [Implementation Guide](docs/implementation-guide.md) - Setup and development details
- [Tasks](docs/tasks.md) - Development task tracker

---

## License

MIT
