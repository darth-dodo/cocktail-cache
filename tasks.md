# Cocktail Cache - Implementation Tasks

> **Status**: Week 4 API & UI Complete
>
> **Build Order**: Data -> Tools -> Agents -> Crews -> Flow -> API -> UI
>
> **Test Coverage**: 339 tests passing, 87% coverage

## Recent Changes (Week 4)

- **Fast Mode for Analysis Crew**: `fast_mode=True` (default) uses unified Drink Recommender agent for ~50% faster response
- **Optional Bottle Advice**: `include_bottle_advice=False` to skip bottle recommendations
- **Raja the AI Mixologist**: Named the conversational bot "Raja"
- **Mixology Facts Loading Screen**: 20 cocktail history facts rotate during API loading
- **Fixed Ingredient IDs**: Frontend ingredient IDs now match database exactly
- **Structured Pydantic Models**: RecipeOutput, AnalysisOutput, BottleAdvisorOutput for typed crew I/O
- **Deployment**: Render.com with GitHub Actions CI/CD

---

## Week 1: Foundation

### Phase 1.1: Project Infrastructure (Architect)

**Duration**: 1-2 hours
**Status**: COMPLETE

#### Tasks

- [x] Initialize project with `uv` and `pyproject.toml`
- [x] Configure pre-commit hooks (`.pre-commit-config.yaml`)
- [x] Create `Makefile` with standard commands
- [x] Create `Dockerfile` for containerized deployment
- [x] Create `render.yaml` for Render deployment
- [x] Create `.env.example` with required environment variables
- [x] Create `.gitignore` with Python/Node exclusions
- [x] Run `uv sync` to install dependencies

#### Quality Gate: Infrastructure Review

- [x] `uv sync` completes without errors
- [x] `make install` works
- [x] Pre-commit hooks installed and functional
- [x] Docker build succeeds
- [x] All config files follow BLUEPRINT.md patterns

---

### Phase 1.2: Project Structure (Architect)

**Duration**: 30 minutes
**Status**: COMPLETE

#### Tasks

- [x] Create `src/app/` directory structure:
  ```
  src/app/
  ├── __init__.py
  ├── main.py           # FastAPI entry point
  ├── config.py         # Environment config
  ├── agents/           # CrewAI agents
  ├── crews/            # Crew compositions
  ├── tools/            # Deterministic tools
  ├── flows/            # CrewAI flows
  ├── models/           # Pydantic models
  ├── routers/          # FastAPI routers
  ├── services/         # Data loading services
  ├── templates/        # Jinja2 templates
  │   └── components/   # HTMX components
  └── static/           # CSS, JS assets
  ```
- [x] Create `data/` directory for JSON databases
- [x] Create `tests/` directory structure:
  ```
  tests/
  ├── __init__.py
  ├── conftest.py
  ├── features/         # BDD feature files
  ├── steps/            # BDD step definitions
  ├── tools/            # Tool unit tests
  ├── agents/           # Agent tests
  └── integration/      # Integration tests
  ```
- [x] Create `scripts/` directory for utility scripts
- [x] Add `__init__.py` files to all packages

#### Quality Gate: Structure Review

- [x] All directories created with correct nesting
- [x] All `__init__.py` files present
- [x] Structure matches BLUEPRINT.md conventions
- [x] `python -c "from src.app import main"` works

---

### Phase 1.3: Data Layer - Cocktails (Developer)

**Duration**: 2-3 hours
**Status**: COMPLETE

#### Tasks

- [x] Create `data/cocktails.json` with 50 cocktails following schema:
  ```json
  {
    "id": "drink-id",
    "name": "Drink Name",
    "tagline": "Short description",
    "ingredients": [{"amount": "2", "unit": "oz", "item": "bourbon"}],
    "method": [{"action": "Shake", "detail": "12-15 seconds"}],
    "glassware": "coupe",
    "garnish": "lemon twist",
    "flavor_profile": {"sweet": 40, "sour": 50, "bitter": 10, "spirit": 60},
    "tags": ["whiskey", "citrus"],
    "difficulty": "easy|medium|hard|advanced",
    "timing_minutes": 3,
    "is_mocktail": false
  }
  ```
- [x] Cover major spirit categories:
  - [x] Whiskey/Bourbon cocktails
  - [x] Gin cocktails
  - [x] Vodka cocktails
  - [x] Rum cocktails
  - [x] Tequila/Mezcal cocktails
  - [x] Brandy/Other cocktails
- [x] Include difficulty distribution across easy, medium, hard, advanced
- [x] Validate JSON schema consistency with Pydantic models

#### Quality Gate: Cocktails Data Review

- [x] 50 cocktails in database
- [x] All required fields populated
- [x] JSON parses without errors (validated by Pydantic)
- [x] Difficulty tags on all recipes
- [x] Flavor profiles sum to reasonable values

---

### Phase 1.4: Data Layer - Mocktails (Developer)

**Duration**: 1-2 hours
**Status**: COMPLETE

#### Tasks

- [x] Create `data/mocktails.json` with 24 mocktails following same schema
- [x] Include variety of flavor profiles:
  - [x] Citrus-forward recipes
  - [x] Sweet/fruity recipes
  - [x] Herbal/botanical recipes
  - [x] Spicy/ginger recipes
- [x] Focus on common fresh ingredients (lemons, limes, ginger, mint)
- [x] All recipes have `is_mocktail: true`
- [x] Validate JSON schema consistency with Pydantic models

#### Quality Gate: Mocktails Data Review

- [x] 24 mocktails in database
- [x] All required fields populated
- [x] JSON parses without errors (validated by Pydantic)
- [x] Variety of flavor profiles represented
- [x] All have `is_mocktail: true`

---

### Phase 1.5: Data Layer - Ingredients & Substitutions (Developer)

**Duration**: 1 hour
**Status**: COMPLETE

#### Tasks

- [x] Create `data/ingredients.json` with 134 categorized ingredients:
  ```json
  {
    "spirits": [{"id": "bourbon", "names": ["bourbon", "bourbon whiskey"]}],
    "modifiers": [{"id": "sweet-vermouth", "names": ["sweet vermouth"]}],
    "bitters_syrups": [{"id": "angostura", "names": ["angostura", "ango"]}],
    "fresh": [{"id": "lemon-juice", "names": ["lemon juice", "lemon"]}],
    "mixers": [{"id": "soda-water", "names": ["soda", "club soda"]}],
    "non_alcoholic": [{"id": "seedlip-grove", "names": ["seedlip grove"]}]
  }
  ```
- [x] Create `data/substitutions.json` with 118 substitution rules across 7 categories:
  - spirits, modifiers, bitters_syrups, fresh, mixers
  - non_alcoholic_to_alcoholic, alcoholic_to_non_alcoholic
- [x] Ensure all cocktail/mocktail ingredients have entries
- [x] Validate with Pydantic models (IngredientsDatabase, SubstitutionsDatabase)

#### Quality Gate: Ingredients Data Review

- [x] All 6 categories populated (134 total ingredients)
- [x] All cocktail ingredients have entries
- [x] Substitutions include alcoholic↔non-alcoholic mappings
- [x] JSON parses without errors (validated by Pydantic)

---

### Phase 1.6: Unlock Scores Script (Developer)

**Duration**: 30 minutes
**Status**: COMPLETE

#### Tasks

- [x] Create `scripts/compute_unlock_scores.py` with Pydantic validation
- [x] Create `scripts/validate_data.py` for comprehensive data validation
- [x] Run script: `uv run python scripts/compute_unlock_scores.py`
- [x] Verify `data/unlock_scores.json` created correctly

**Results:**
- 110 ingredients with unlock entries
- 293 total unlock mappings
- Top versatile ingredients: simple-syrup (25), fresh-lime-juice (16), fresh-lemon-juice (15)

#### Quality Gate: Unlock Scores Review

- [x] Script runs without errors
- [x] `unlock_scores.json` generated (70KB)
- [x] All ingredients have unlock entries
- [x] Both cocktails and mocktails included

---

### Phase 1.7: Week 1 Validation (QA)

**Duration**: 30 minutes
**Status**: COMPLETE

#### Tasks

- [x] Verify all data files parse correctly with Pydantic validation
- [x] Cross-reference ingredients between all JSON files
- [x] Validate schema consistency across all cocktails/mocktails
- [x] Run unlock scores script and verify output
- [x] Test basic project setup (`uv sync`, `make lint`)
- [x] Pre-commit hooks pass (ruff, mypy, trailing whitespace)

#### Quality Gate: Week 1 Complete

- [x] Project structure matches BLUEPRINT.md conventions
- [x] 50 cocktails in DB with all fields
- [x] 24 mocktails in DB with all fields
- [x] 134 ingredients categorized across 6 categories
- [x] 118 substitution rules defined across 7 categories
- [x] Unlock scores computed (110 ingredients → 293 mappings)
- [x] All JSON files valid and Pydantic-validated

**Additional Deliverables:**
- Created Pydantic models in `src/app/models/` (drinks.py, ingredients.py, unlock_scores.py)
- Created data loader service in `src/app/services/data_loader.py`
- Created validation script `scripts/validate_data.py`

---

## Week 2: CrewAI Core ✅ COMPLETE

### Phase 2.1: Pydantic Models ✅

**Status**: COMPLETE

- [x] Created `src/app/models/__init__.py` with exports
- [x] Created `src/app/models/cabinet.py` (Cabinet model)
- [x] Created `src/app/models/cocktail.py` (CocktailMatch, FlavorProfile)
- [x] Created `src/app/models/recipe.py` (Recipe, RecipeStep, TechniqueTip)
- [x] Created `src/app/models/recommendation.py` (Recommendation, BottleRec)
- [x] Created `src/app/models/user_prefs.py` (SkillLevel, DrinkType, UserPreferences enums)
- [x] Created `src/app/models/history.py` (HistoryEntry, RecipeHistory)
- [x] Unit tests passing in `tests/models/`

---

### Phase 2.2: Tools ✅

**Status**: COMPLETE

- [x] Created `src/app/tools/__init__.py` with exports
- [x] Created `src/app/tools/recipe_db.py` (RecipeDBTool)
- [x] Created `src/app/tools/flavor_profiler.py` (FlavorProfilerTool)
- [x] Created `src/app/tools/substitution_finder.py` (SubstitutionFinderTool)
- [x] Created `src/app/tools/unlock_calculator.py` (UnlockCalculatorTool)
- [x] All tools are deterministic (no LLM calls)
- [x] Tool tests passing: `uv run pytest tests/tools/`

---

### Phase 2.3: Agents ✅

**Status**: COMPLETE

- [x] Created `src/app/agents/__init__.py` with factory exports and LLM config
- [x] Created `src/app/agents/llm_config.py` (Claude Haiku configuration)
- [x] Created `src/app/agents/cabinet_analyst.py`
- [x] Created `src/app/agents/mood_matcher.py`
- [x] Created `src/app/agents/recipe_writer.py`
- [x] Created `src/app/agents/bottle_advisor.py`
- [x] All agents use Claude Haiku (`anthropic/claude-3-5-haiku-20241022`)
- [x] Agent tests passing: `uv run pytest tests/agents/`

**LLM Configuration:**
```python
DEFAULT_MODEL = "anthropic/claude-3-5-haiku-20241022"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
```

**Environment Variable Required:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

### Week 2 Quality Gate: PASSED ✅

- [x] 212 tests passing
- [x] 90% code coverage
- [x] All models use Pydantic v2 patterns
- [x] All tools are deterministic (no LLM calls)
- [x] All agents use Claude Haiku via factory pattern
- [x] Pre-commit hooks passing (ruff, mypy)

---

## Week 3: Crews & Flow ✅ COMPLETE

### Phase 3.1: Analysis Crew (Developer)

**Duration**: 1-2 hours
**Status**: COMPLETE

#### Tasks

- [x] Create `src/app/crews/__init__.py`
- [x] Create `src/app/crews/analysis_crew.py`:
  - Cabinet Analyst → Mood Matcher pipeline
  - Task context/dependency chaining
  - Sequential process with verbose=False
- [x] Write crew tests in `tests/crews/test_analysis_crew.py` (32 tests)

#### Quality Gate: Analysis Crew Review

- [x] Crew composes correctly
- [x] Context flows between tasks
- [x] Handles drink_type, skill_level, exclude parameters
- [x] Tests pass with mocked agents

---

### Phase 3.2: Recipe Crew (Developer)

**Duration**: 1-2 hours
**Status**: COMPLETE

#### Tasks

- [x] Create `src/app/crews/recipe_crew.py`:
  - Recipe Writer → Bottle Advisor pipeline
  - Task context/dependency chaining
  - Sequential process with verbose=False
- [x] Write crew tests in `tests/crews/test_recipe_crew.py` (43 tests)

#### Quality Gate: Recipe Crew Review

- [x] Skill-adapted tips in recipe output
- [x] Bottle advisor considers current cabinet
- [x] Tests pass with mocked agents

---

### Phase 3.3: Flow Orchestration (Developer)

**Duration**: 2-3 hours
**Status**: COMPLETE

#### Tasks

- [x] Create `src/app/flows/__init__.py`
- [x] Create `src/app/flows/cocktail_flow.py`:
  - CocktailFlowState with Pydantic v2 models
  - Flow steps: receive_input → analyze → select → generate_recipe
  - State normalization (lowercase cabinet, default values)
  - Error handling for empty cabinet
- [x] Add `request_another()` for rejection workflow
- [x] Write flow tests in `tests/flows/test_cocktail_flow.py` (52 tests)

#### Quality Gate: Flow Review

- [x] State transitions correctly
- [x] Crews invoked with proper inputs
- [x] Rejection/another flow works
- [x] Tests pass with mocked crews

---

### Week 3 Quality Gate: PASSED ✅

- [x] 127 new tests for crews and flows
- [x] 339 total tests passing
- [x] 87% code coverage
- [x] Pre-commit hooks passing (ruff, mypy)
- [x] All crews use sequential processing
- [x] Flow state management with Pydantic v2

---

## Week 4: API & UI (COMPLETE)

### Phase 4.1: FastAPI Setup

**Status**: COMPLETE

- [x] FastAPI app with routers and templates
- [x] Pydantic Settings configuration
- [x] CORS configured for development
- [x] Health check endpoint: `GET /health`
- [x] Static file serving for CSS/JS

### Phase 4.2: Chat Interface with Raja

**Status**: COMPLETE

- [x] Conversational chat UI (not traditional form)
- [x] Raja the AI Mixologist persona
- [x] Ingredient selection with category grouping
- [x] Mood and skill level selection
- [x] Recipe display with collapsible sections
- [x] "Try Another" and "I Made This" actions
- [x] Mixology facts loading screen (20 facts)

### Phase 4.3: Crew Optimizations

**Status**: COMPLETE

- [x] Fast mode for Analysis Crew (`fast_mode=True` default)
  - Single Drink Recommender agent vs two-agent flow
  - ~50% faster response time
- [x] Optional bottle advice (`include_bottle_advice=False`)
  - Skip bottle recommendations when not needed
- [x] Structured Pydantic output models
  - `AnalysisOutput`: Ranked drink candidates
  - `RecipeOutput`: Complete recipe with tips
  - `BottleAdvisorOutput`: Bottle recommendations
  - `RecipeCrewOutput`: Combined crew output

### Phase 4.4: Deployment

**Status**: COMPLETE

- [x] `render.yaml` with proper uv commands
- [x] GitHub Actions CI/CD (`.github/workflows/ci-cd.yml`)
  - Lint and type checking
  - Test suite with coverage
  - Automatic deployment to Render
- [x] Dockerfile fixes for uv package manager

### Phase 4.5: Bug Fixes

**Status**: COMPLETE

- [x] Fixed ingredient IDs to match database exactly
- [x] Better drink matching results

---

## Week 5: UI & Deploy (COMPLETE)

> Note: UI implementation used a chat interface instead of HTMX form approach.
> See Week 4 Phase 4.2 for chat UI details.

### Phase 5.1: Chat UI (COMPLETE)

- [x] Conversational interface with Raja
- [x] Mobile-first responsive design
- [x] Tailwind CSS styling
- [x] Vanilla JS (no HTMX dependency)

### Phase 5.2: Deployment (COMPLETE)

- [x] `render.yaml` configured with uv package manager
- [x] GitHub Actions CI/CD workflow
- [x] Auto-deploy on push to main
- [x] Health check endpoint working

---

## Week 6: Polish (IN PROGRESS)

### Phase 6.1: Error Handling

**Status**: PENDING

- [ ] Graceful fallbacks for LLM failures
- [ ] Empty cabinet scenario handling
- [ ] No matches for mood/preferences handling
- [ ] Retry logic for transient failures
- [ ] User-friendly error messages

### Phase 6.2: Performance Optimization

**Status**: PARTIAL (fast mode implemented)

- [x] Fast mode (~50% faster with single-agent analysis)
- [x] Optional bottle advice to skip unnecessary LLM calls
- [ ] Profile recommendation latency
- [ ] Optimize JSON loading (caching)
- [ ] Measure Lighthouse scores

### Phase 6.3: Documentation

**Status**: COMPLETE

- [x] README.md updated with fast mode and Raja
- [x] Architecture.md updated with crew diagrams
- [x] Implementation guide updated with Week 4 progress
- [ ] API documentation (OpenAPI export)
- [ ] User guide
- [ ] Demo video/screenshots

---

## Session Log Template

```markdown
## Session [N]: [Phase Name]

**Agent**: [Architect | Developer | QA]
**Duration**: [X] minutes/hours
**Status**: [In Progress | Complete | Blocked]

### Completed
- [x] Task 1
- [x] Task 2

### In Progress
- [ ] Task 3 (X% complete)

### Blockers
- [Blocker description if any]

### Decisions Made
- [Key decision 1]
- [Key decision 2]

### Next Steps
- [What to do next session]
```

---

## Quality Gates Summary

| Phase | Gate | Criteria | Status |
|-------|------|----------|--------|
| Week 1 | Data Complete | 50 cocktails, 24 mocktails, all JSON valid | PASSED |
| Week 2 | Core Complete | Models, Tools, Agents tested (212 tests, 90% coverage) | PASSED |
| Week 3 | Crews Complete | Flow orchestration working (339 tests, 87% coverage) | PASSED |
| Week 4 | API Complete | Fast mode, chat UI, structured outputs | PASSED |
| Week 5 | UI Complete | Mobile responsive, deployed to Render | PASSED |
| Week 6 | Ready | Error handling, optimization, docs | IN PROGRESS |

---

## Performance Targets

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| Time to recommendation | <8s | ~5s (fast mode) | Single-agent analysis |
| Cost per request | <$0.10 | ~$0.05 | 2-3 LLM calls in fast mode |
| Mobile Lighthouse | 90+ | TBD | Vanilla JS, minimal deps |
| Test coverage | 70%+ | 87% | 339 tests passing |
| LLM calls per request | 4 | 2-3 | Fast mode default |
