# Cocktail Cache

> **Your cabinet. Your mood. Your perfect drink.**

<p align="center">
  <a href="https://cocktail-cache.onrender.com">
    <img src="https://img.shields.io/badge/🍸_Try_it_Live-cocktail--cache.onrender.com-amber?style=for-the-badge&labelColor=1a1a1a" alt="Live Demo">
  </a>
</p>

<p align="center">
  <a href="https://github.com/darth-dodo/cocktail-cache">
    <img src="https://img.shields.io/badge/GitHub-darth--dodo%2Fcocktail--cache-blue?logo=github" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Tests-751_passing-brightgreen?logo=pytest" alt="Tests: 751 passing">
  <img src="https://img.shields.io/badge/Coverage-78%25-green?logo=codecov" alt="Coverage: 78%">
</p>

---

An AI-powered home bar advisor that helps you craft great cocktails with whatever bottles you have. Chat with Raja, your AI mixologist, to get personalized drink recommendations, technique guidance, and smart suggestions for your next bottle purchase.

---

## Meet Raja, Your AI Mixologist

<p align="center">
  <img src=".playwright-mcp/raja-chat-working.png" alt="Raja Chat Interface" width="300">
</p>

**Raja** is a 20-year bartender veteran from Colaba, Bombay. He knows his craft, tells great stories, and speaks with warmth:

> *"Arrey bhai! Feeling relaxed after a long day? With your bourbon and lemons, let me suggest a Gold Rush — ekdum first class for unwinding!"*

Just tell Raja what you have and how you're feeling. He'll find the perfect drink.

---

## How It Works

### 1. Tell Raja What You Have
Add your bottles to your cabinet — spirits, mixers, bitters, fresh ingredients. Your cabinet is saved automatically.

### 2. Describe Your Mood
"Celebrating a promotion" • "Quiet evening alone" • "Cocktail nights with friends" • "Sunday afternoon vibes"

### 3. Get Your Perfect Drink
Raja recommends drinks you can actually make, with step-by-step instructions adapted to your skill level.

### 4. Know What to Buy Next
Raja tells you which single bottle will unlock the most new drinks — maximum impact for your next purchase.

---

## Features

| Feature | Description |
|---------|-------------|
| **142 Drinks** | 103 cocktails + 39 mocktails with detailed recipes |
| **Smart Matching** | Only shows drinks you can make with your cabinet |
| **Skill Adaptation** | Beginner-friendly to adventurous techniques |
| **Next Bottle Advice** | ROI-based suggestions for cabinet expansion |
| **Browse & Search** | Explore the full catalog with filters |
| **Mobile-First** | Designed for use in the kitchen |

---

## Screenshots

<p align="center">
  <img src=".playwright-mcp/mobile-chat-tab.png" alt="Chat Tab" width="200">
  <img src=".playwright-mcp/mobile-cabinet-tab.png" alt="Cabinet Tab" width="200">
  <img src=".playwright-mcp/mobile-browse-tab.png" alt="Browse Tab" width="200">
</p>

<p align="center">
  <em>Chat with Raja • Build Your Cabinet • Browse All Drinks</em>
</p>

---

## Try It Now

**[cocktail-cache.onrender.com](https://cocktail-cache.onrender.com)**

No signup required. Just start chatting with Raja.

---

## For Developers

<details>
<summary><strong>Tech Stack & Architecture</strong></summary>

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Runtime** | Python 3.12 |
| **API** | FastAPI |
| **AI** | CrewAI + Anthropic Claude |
| **Frontend** | HTMX + Jinja2 + Tailwind |
| **Deployment** | Render |

### Codebase Health

| Metric | Value |
|--------|-------|
| **Test Suite** | 714 tests |
| **Code Coverage** | 78% |
| **Models** | 100% covered |
| **Services** | 96%+ covered |
| **Type Checking** | Strict mypy |
| **Linting** | Ruff + pre-commit hooks |

### Quick Start

```bash
git clone https://github.com/darth-dodo/cocktail-cache.git
cd cocktail-cache

cp .env.example .env
# Add your ANTHROPIC_API_KEY

make install
make dev
# Visit http://localhost:8888
```

### Architecture

```mermaid
flowchart LR
    User[User] --> Chat[Chat with Raja]
    Chat --> AI[CrewAI Agents]
    AI --> Claude[Anthropic Claude]
    AI --> Data[(142 Drinks<br/>180 Ingredients)]
    AI --> Recipe[Recipe + Tips]
    Recipe --> User
```

### AI Agents

- **Raja Bartender** — Conversational AI with Bombay personality
- **Drink Recommender** — Matches cabinet + mood to drinks
- **Recipe Writer** — Generates skill-adapted instructions
- **Bottle Advisor** — Calculates next bottle ROI

### Documentation

- [Architecture](docs/architecture.md) — System design
- [Product Requirements](docs/product.md) — PRD and user stories
- [API Reference](docs/api.md) — REST endpoints

</details>

<details>
<summary><strong>Development Commands</strong></summary>

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make dev` | Start dev server (port 8888) |
| `make test` | Run test suite |
| `make check` | Linting and type checks |
| `make format` | Format code |

</details>

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push and open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with</strong><br/>
  <a href="https://crewai.com">CrewAI</a> •
  <a href="https://anthropic.com">Anthropic Claude</a> •
  <a href="https://fastapi.tiangolo.com">FastAPI</a> •
  <a href="https://htmx.org">HTMX</a>
</p>

<p align="center">
  <a href="https://cocktail-cache.onrender.com"><strong>Try it Live →</strong></a>
</p>
