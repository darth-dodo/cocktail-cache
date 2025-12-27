# Cocktail Cache - Implementation Tasks

> **Status**: Week 2 CrewAI Core (Complete) → Week 3 Crews & Flow (Next)
>
> **Build Order**: Data -> Tools -> Agents -> Crews -> Flow -> API -> UI
>
> **Test Coverage**: 212 tests passing, 90% coverage

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

## Week 3: Crews & Flow

### Phase 3.1: Analysis Crew (Developer)

**Duration**: 1-2 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/crews/__init__.py`
- [ ] Create `src/app/crews/analysis_crew.py`:
  ```python
  def create_analysis_crew():
      """Cabinet Analyst -> Mood Matcher crew."""
      analyst = create_cabinet_analyst()
      matcher = create_mood_matcher()

      analyze_task = Task(
          description="""Analyze cabinet: {cabinet}
          Drink type: {drink_type}
          Exclude recent: {exclude}""",
          agent=analyst
      )

      match_task = Task(
          description="""Rank candidates for mood: {mood}
          Skill level: {skill_level}""",
          agent=matcher,
          context=[analyze_task]
      )

      return Crew(
          agents=[analyst, matcher],
          tasks=[analyze_task, match_task]
      )
  ```
- [ ] Write crew tests in `tests/crews/test_analysis_crew.py`

#### Quality Gate: Analysis Crew Review

- [ ] Crew composes correctly
- [ ] Context flows between tasks
- [ ] Handles drink_type, skill_level, exclude parameters
- [ ] Tests pass with mocked agents

---

### Phase 3.2: Recipe Crew (Developer)

**Duration**: 1-2 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/crews/recipe_crew.py`:
  ```python
  def create_recipe_crew():
      """Recipe Writer -> Bottle Advisor crew."""
      writer = create_recipe_writer()
      advisor = create_bottle_advisor()

      recipe_task = Task(
          description="""Generate recipe for: {cocktail_id}
          Skill level: {skill_level}""",
          agent=writer
      )

      bottle_task = Task(
          description="""Recommend next bottle based on:
          Cabinet: {cabinet}
          Drink type: {drink_type}""",
          agent=advisor,
          context=[recipe_task]
      )

      return Crew(
          agents=[writer, advisor],
          tasks=[recipe_task, bottle_task]
      )
  ```
- [ ] Write crew tests in `tests/crews/test_recipe_crew.py`

#### Quality Gate: Recipe Crew Review

- [ ] Skill-adapted tips in recipe output
- [ ] Bottle advisor considers current cabinet
- [ ] Tests pass with mocked agents

---

### Phase 3.3: Flow Orchestration (Developer)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/flows/__init__.py`
- [ ] Create `src/app/flows/cocktail_flow.py`:
  ```python
  class CocktailFlowState(BaseModel):
      session_id: str
      cabinet: list[str]
      mood: str
      constraints: list[str] = []
      drink_type: str = "cocktail"
      skill_level: str = "intermediate"
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
          result = crew.kickoff(inputs={...})
          # Update state with candidates
          return self.state

      @listen(analyze)
      def generate_recipe(self):
          crew = create_recipe_crew()
          result = crew.kickoff(inputs={...})
          # Update state with recipe
          return self.state
  ```
- [ ] Add "another" flow for rejecting and getting new recommendation
- [ ] Write flow tests in `tests/flows/test_cocktail_flow.py`

#### Quality Gate: Flow Review

- [ ] State transitions correctly
- [ ] Crews invoked with proper inputs
- [ ] Rejection/another flow works
- [ ] Tests pass with mocked crews

---

## Week 4: API & Integration

### Phase 4.1: FastAPI Setup (Developer)

**Duration**: 1-2 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/main.py` with FastAPI app
- [ ] Create `src/app/config.py` with Pydantic Settings
- [ ] Configure CORS for development
- [ ] Add lifespan management for resources
- [ ] Create health check endpoint: `GET /health`

#### Quality Gate: API Setup Review

- [ ] `uv run uvicorn src.app.main:app --reload` works
- [ ] Health check returns 200
- [ ] CORS configured for localhost

---

### Phase 4.2: API Routes (Developer)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/routers/__init__.py`
- [ ] Create `src/app/routers/api.py`:
  ```python
  @router.post("/recommend")
  async def recommend(request: RecommendRequest):
      """Get cocktail recommendation based on cabinet and mood."""

  @router.post("/another")
  async def another(request: AnotherRequest):
      """Reject current and get another recommendation."""

  @router.post("/made")
  async def mark_made(request: MarkMadeRequest):
      """Mark a drink as made (for client-side history)."""
  ```
- [ ] Create request/response Pydantic models
- [ ] Implement session management (in-memory for MVP)
- [ ] Add proper error handling

#### Quality Gate: Routes Review

- [ ] All endpoints documented (OpenAPI)
- [ ] Request validation works
- [ ] Error responses follow standard format
- [ ] Sessions persist across requests

---

### Phase 4.3: Integration Tests (QA)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Create `tests/integration/test_api.py`:
  - [ ] Test `/recommend` with various cabinets
  - [ ] Test `/another` rejection flow
  - [ ] Test `/made` history marking
  - [ ] Test error scenarios (empty cabinet, invalid mood)
- [ ] Create BDD features in `tests/features/`:
  - [ ] `recommendation.feature`
  - [ ] `history.feature`
- [ ] Measure and validate latency (<8s target)
- [ ] Test with mock LLM responses

#### Quality Gate: Integration Review

- [ ] All integration tests pass
- [ ] Latency within target
- [ ] Error handling comprehensive
- [ ] Run: `uv run pytest tests/integration/`

---

## Week 5: UI & Deploy

### Phase 5.1: Templates & Components (Developer)

**Duration**: 3-4 hours
**Status**: PENDING

#### Tasks

- [ ] Create `src/app/templates/base.html` with HTMX setup
- [ ] Create `src/app/templates/index.html` main page
- [ ] Create components in `src/app/templates/components/`:
  - [ ] `cabinet_grid.html` - Ingredient selection grid
  - [ ] `mood_selector.html` - Mood buttons
  - [ ] `skill_selector.html` - Skill level toggle
  - [ ] `drink_type_toggle.html` - Cocktail/Mocktail/Both
  - [ ] `recipe_card.html` - Recipe display with "I made this"
  - [ ] `history_list.html` - Recently made sidebar
- [ ] Create `src/app/static/css/styles.css`
- [ ] Create `src/app/static/js/app.js`:
  - [ ] Local storage for cabinet
  - [ ] Local storage for preferences
  - [ ] Local storage for history
  - [ ] Hydrate hidden inputs from storage

#### Quality Gate: UI Review

- [ ] All components render correctly
- [ ] HTMX interactions work
- [ ] Local storage persists across sessions
- [ ] Mobile responsive (test on various widths)

---

### Phase 5.2: HTMX Integration (Developer)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Wire form to `/api/recommend` with HTMX
- [ ] Implement loading indicators
- [ ] Handle "Another" button with HTMX
- [ ] Implement "I made this" button
- [ ] Update history list on successful make
- [ ] Add error state handling in UI

#### Quality Gate: HTMX Review

- [ ] Form submissions work without page reload
- [ ] Loading states display correctly
- [ ] Errors display user-friendly messages
- [ ] History updates in real-time

---

### Phase 5.3: Deployment (Developer)

**Duration**: 1-2 hours
**Status**: PENDING

#### Tasks

- [ ] Verify `render.yaml` configuration
- [ ] Test Docker build locally: `make docker-build`
- [ ] Test Docker run locally: `make docker-dev`
- [ ] Push to GitHub main branch
- [ ] Configure Render dashboard:
  - [ ] Set ANTHROPIC_API_KEY environment variable
  - [ ] Verify auto-deploy from main
- [ ] Test deployed application

#### Quality Gate: Deployment Review

- [ ] Render deployment succeeds
- [ ] Health check passes on production
- [ ] All features work on deployed version
- [ ] Performance acceptable (<8s recommendations)

---

## Week 6: Polish

### Phase 6.1: Error Handling (Developer)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Add graceful fallbacks for LLM failures
- [ ] Handle empty cabinet scenario
- [ ] Handle no matches for mood/preferences
- [ ] Handle all drinks in history (nothing new to suggest)
- [ ] Add retry logic for transient failures
- [ ] Improve error messages for users

#### Quality Gate: Error Handling Review

- [ ] All edge cases handled gracefully
- [ ] User sees helpful messages, not stack traces
- [ ] Fallback recommendations work

---

### Phase 6.2: Performance Optimization (Developer)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Profile recommendation latency
- [ ] Optimize JSON loading (caching)
- [ ] Minimize LLM calls (target: 4 per request)
- [ ] Add request caching where appropriate
- [ ] Optimize frontend asset loading
- [ ] Measure and improve Lighthouse scores

#### Quality Gate: Performance Review

- [ ] Time to recommendation <8s
- [ ] Cost per request <$0.10
- [ ] Mobile Lighthouse score 90+

---

### Phase 6.3: Documentation & Final QA (QA)

**Duration**: 2-3 hours
**Status**: PENDING

#### Tasks

- [ ] Update README.md with usage instructions
- [ ] Add API documentation (OpenAPI export)
- [ ] Create user guide in `docs/`
- [ ] Perform final end-to-end testing
- [ ] Test on multiple browsers/devices
- [ ] Create demo video/screenshots

#### Quality Gate: Final Review

- [ ] All documentation complete
- [ ] All tests passing
- [ ] Production deployment stable
- [ ] Ready for users

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
| Week 1 | Data Complete | 50 cocktails, 24 mocktails, all JSON valid | ✅ PASSED |
| Week 2 | Core Complete | Models, Tools, Agents tested (212 tests, 90% coverage) | ✅ PASSED |
| Week 3 | Crews Complete | Flow orchestration working | 🔲 PENDING |
| Week 4 | API Complete | <8s latency, all endpoints tested | 🔲 PENDING |
| Week 5 | UI Complete | Mobile responsive, deployed | 🔲 PENDING |
| Week 6 | Ready | All polish complete, documentation done | 🔲 PENDING |

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to recommendation | <8s | API response time |
| Cost per request | <$0.10 | LLM API costs |
| Mobile Lighthouse | 90+ | Performance score |
| Test coverage | 70%+ | Unit + integration |
| LLM calls per request | 4 | Agent invocations |
