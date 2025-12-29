# Cocktail Cache - Product Requirements Document

## Executive Summary

**Cocktail Cache** is an AI-powered home bar advisor that helps you discover and craft great cocktails with whatever bottles you have. Describe your mood and cabinet contents; the app recommends personalized cocktails, teaches technique, and suggests the next bottle that unlocks the most new drinks.

**Dual Purpose**:
1. A polished, usable product for home drink enthusiasts who want to explore what they can make
2. A CrewAI learning project demonstrating multi-agent orchestration patterns

**Timeline**: 4-6 sessions to Polished MVP

**Current Status**: Session 6 complete with enhanced UX features including browse/search functionality, tabbed navigation, and individual drink detail pages.

---

## Problem Statement

### The Party Host's Dilemma

Party hosts face a recurring challenge: guests are arriving, they have a random assortment of bottles accumulated over time, and they want to serve something better than rum-and-coke but don't know what's possible with their ingredients.

**Current Solutions Fall Short:**
- **Google/Recipe sites**: Require knowing what you want to search for
- **Cocktail apps**: Assume you have a full bar; overwhelming for casual users
- **Asking friends**: Hit-or-miss quality, no technique guidance
- **Buying everything**: Expensive, wasteful, bottles expire

**The Gap**: No solution optimizes for "maximize enjoyment with minimal cabinet investment" for occasional users.

### Pain Points

| Pain Point | Impact | Our Solution |
|------------|--------|--------------|
| "I don't know what I can make" | Paralysis, defaults to boring drinks | Show all possibilities from their cabinet |
| "Recipes assume ingredients I don't have" | Frustration, abandoned attempts | Only recommend what's actually makeable |
| "I don't know what to buy next" | Random purchases, cabinet bloat | "Next bottle" with ROI justification |
| "I'll mess up the technique" | Embarrassment at party | Step-by-step with tips |
| "I need something NOW" | No time for research | Fast, confident recommendations |

---

## Target User

### Primary Persona: The Home Drink Enthusiast

**Demographics:**
- Age 25-50
- Makes drinks at home 2-20 times per month (for self, partner, friends, or events)
- Has 5-15 bottles in cabinet (accumulated gifts, past purchases)
- Enjoys cocktails but isn't a mixology expert
- Willing to spend 5 minutes learning, not 30

**Behavioral Traits:**
- Wants to make something better than the basics
- Curious about what's possible with their existing bottles
- Values practical guidance over cocktail snobbery
- Purchases bottles opportunistically, not systematically
- Uses phone while prepping

**Key Insight**: They want to enjoy good drinks at home without becoming a hobbyist. Whether it's a quiet Tuesday night or a dinner party, they want confidence that what they're making is worth the effort.

### Secondary Personas

| Persona | Characteristics | How We Serve Them |
|---------|-----------------|-------------------|
| The Gifted Cabinet | Has nice bottles (gifts) but no knowledge | Help them use what they have |
| The Anxious First-Timer | Making cocktails for the first time | Heavy technique guidance, skill-adapted recipes |
| The Repeat Party Host | Same crowd, needs variety | "Something different" suggestions, recipe history |
| The Sober-Curious Host | Wants delicious non-alcoholic options | Mocktail recommendations |
| The Mixed Crowd Host | Guests with varying preferences | Both cocktails and mocktails from same cabinet |

---

## User Stories

### Core Stories (MVP)

```
As a party host,
I want to see what cocktails I can make with my current bottles
So that I don't waste time on recipes I can't complete.

As a party host,
I want the app to match my mood/occasion to a cocktail
So that I serve something appropriate (not a tiki drink at a somber dinner).

As a party host,
I want step-by-step instructions with tips
So that I don't mess up in front of guests.

As a party host,
I want to know the ONE bottle I should buy next
So that I maximize my options without overspending.

As a return user,
I want my cabinet saved
So that I don't re-enter 15 bottles every time.

As a host with non-drinking guests,
I want mocktail recommendations using my ingredients
So that everyone has a delicious drink option.

As a beginner,
I want recipes adapted to my skill level
So that I don't get overwhelmed by advanced techniques.

As a return user,
I want to see my recipe history
So that I can remake drinks I loved or avoid repeating recent ones.
```

### Enhanced Stories (Post-MVP)

```
As a perfectionist,
I want to rate drinks I've made
So that the app learns my preferences.

As a shopping-mode user,
I want to export a shopping list
So that I can prep before the party.

As a health-conscious host,
I want to see calorie/sugar estimates
So that I can make informed choices.
```

---

## Functional Requirements

### FR-1: Cabinet Management

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-1.1 | User can select ingredients from categorized grid | P0 | Done | Spirits, modifiers, bitters, fresh, mixers |
| FR-1.2 | User can type free-text ingredients with autocomplete | P1 | Done | Autocomplete suggests matching ingredients as user types |
| FR-1.3 | Cabinet persists in local storage | P0 | Done | No login required |
| FR-1.4 | Dedicated Cabinet tab in navigation | P0 | Done | Separate tab for cabinet management |
| FR-1.5 | Quick-add for common cabinets | P2 | Planned | "Starter kit", "Whiskey lover", etc. |
| FR-1.6 | "I have everything" for full exploration | P2 | Planned | Power user mode |

**UX Consideration**: Cabinet management via dedicated tab with ingredient autocomplete for faster input. Progressive disclosure with collapsible categories.

### FR-2: Mood/Occasion Input

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-2.1 | Pre-set vibe buttons | P0 | Unwinding, Celebrating, Refreshing, Warming up, etc. |
| FR-2.2 | Free-text mood description | P1 | "Sunday afternoon on the patio" |
| FR-2.3 | Constraint checkboxes | P0 | Not too sweet, quick & easy, low effort |
| FR-2.4 | Optional preferred spirit | P1 | "I want to use the bourbon" |
| FR-2.5 | Drink type toggle | P0 | Cocktail / Mocktail / Both |
| FR-2.6 | Skill level selector | P0 | Beginner / Intermediate / Adventurous |

### FR-3: Recommendation Engine

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-3.1 | Generate ranked cocktail/mocktail matches | P0 | Based on cabinet + mood + drink type |
| FR-3.2 | Explain "why this drink" | P0 | Connect recommendation to user's input |
| FR-3.3 | Show flavor profile visualization | P1 | Sweet/sour/bitter/spirit bars |
| FR-3.4 | Handle empty/minimal cabinets gracefully | P0 | "Here's what you CAN make + buy this" |
| FR-3.5 | Filter by skill level | P0 | Beginner sees simpler recipes first |
| FR-3.6 | Mocktail recommendations | P0 | Non-alcoholic options using available ingredients |
| FR-3.7 | Exclude recently made drinks | P1 | Use history to suggest variety |

### FR-4: Recipe Display

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-4.1 | Ingredient list with exact amounts | P0 | oz or ml toggle |
| FR-4.2 | Step-by-step method | P0 | Numbered, clear actions |
| FR-4.3 | Technique tips per step | P0 | "How to know when it's shaken enough" |
| FR-4.4 | Prep steps (e.g., honey syrup) | P1 | Make-ahead instructions |
| FR-4.5 | Timing and difficulty indicator | P1 | "3 minutes, Easy" |
| FR-4.6 | Garnish instructions | P1 | What to use, how to apply |
| FR-4.7 | Skill-adapted instructions | P0 | Beginner gets more detail, advanced gets concise |
| FR-4.8 | Mocktail badge | P0 | Clear visual indicator for non-alcoholic drinks |

### FR-5: Substitutions

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-5.1 | Suggest swaps for missing ingredients | P1 | "Use lime instead of lemon" |
| FR-5.2 | Rate substitution quality | P1 | "Nearly identical" vs "Acceptable" |
| FR-5.3 | Adjust ratios for subs | P2 | "Use 2/3 oz instead of 3/4" |

### FR-6: Next Bottle Recommendation

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-6.1 | Recommend highest-ROI bottle | P0 | Most new drinks unlocked |
| FR-6.2 | Show what drinks it unlocks | P0 | With "you already have X, Y, Z" |
| FR-6.3 | Include price range | P1 | "$20-30 range" |
| FR-6.4 | Runner-up recommendation | P2 | Alternative if first isn't available |

### FR-7: Alternative Recommendations

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-7.1 | "Show me something else" button | P0 | Keeps context, excludes shown drink |
| FR-7.2 | Track rejected drinks in session | P1 | Don't re-suggest |

### FR-8: Sharing

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-8.1 | Copy recipe to clipboard | P1 | Planned | Plain text format |
| FR-8.2 | Shareable URL for individual drinks | P2 | Done | /drink/{id} with full recipe details |
| FR-8.3 | Recipe card image for social | P3 | Planned | Future enhancement |

### FR-9: Recipe History

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-9.1 | Track made drinks in local storage | P0 | Timestamp + recipe ID |
| FR-9.2 | Display "Recently Made" list | P0 | Last 10-20 drinks |
| FR-9.3 | "Make Again" quick action | P1 | One-tap to view recipe |
| FR-9.4 | Mark as made from recipe view | P0 | "I made this" button |
| FR-9.5 | Exclude recent from recommendations | P1 | Configurable: last 3/5/10 |
| FR-9.6 | Clear history option | P2 | Privacy control |

### FR-10: Skill Level System

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-10.1 | Skill level persists in local storage | P0 | Beginner, Intermediate, Adventurous |
| FR-10.2 | Recipes tagged with difficulty | P0 | Easy, Medium, Advanced |
| FR-10.3 | Beginner mode shows simpler recipes first | P0 | Filter + sort |
| FR-10.4 | Beginner recipes have expanded tips | P0 | More hand-holding |
| FR-10.5 | Adventurous mode includes complex drinks | P1 | Egg whites, infusions, etc. |
| FR-10.6 | Skill level affects technique detail | P0 | Progressive disclosure |

### FR-11: Mocktails

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-11.1 | Mocktail database (39 drinks) | P0 | Done | Non-alcoholic recipes |
| FR-11.2 | Mocktail toggle on main input | P0 | Done | Cocktail / Mocktail / Both |
| FR-11.3 | Mocktails use same cabinet ingredients | P0 | Done | Citrus, syrups, herbs, mixers |
| FR-11.4 | Flavor profiles for mocktails | P0 | Done | Same visualization as cocktails |
| FR-11.5 | "Spirit-free" badge on recipes | P0 | Done | Clear visual indicator |
| FR-11.6 | Mocktail-specific technique tips | P1 | Planned | Building complexity without alcohol |

### FR-12: Browse and Search (Session 6)

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-12.1 | Browse page with full drink catalog | P0 | Done | 142 drinks (103 cocktails + 39 mocktails) |
| FR-12.2 | Text search by drink name | P0 | Done | Real-time filtering as user types |
| FR-12.3 | Filter by drink type (Cocktail/Mocktail) | P0 | Done | Toggle buttons with active state |
| FR-12.4 | Filter by difficulty level | P0 | Done | Easy, Medium, Hard, Advanced options |
| FR-12.5 | Individual drink detail pages | P0 | Done | /drink/{id} with full recipe, ingredients, flavor profile |
| FR-12.6 | "Ask AI Instead" option from browse | P1 | Done | Link to chat interface for personalized recommendations |
| FR-12.7 | Drink cards with key info preview | P0 | Done | Name, tagline, type badge, difficulty, timing |

### FR-13: Tabbed Navigation (Session 6)

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| FR-13.1 | Three-tab navigation structure | P0 | Done | Chat, Cabinet, Browse tabs |
| FR-13.2 | Chat tab as primary interface | P0 | Done | AI-powered recommendation flow |
| FR-13.3 | Cabinet tab for ingredient management | P0 | Done | Dedicated ingredient selection interface |
| FR-13.4 | Browse tab links to search page | P0 | Done | Full catalog exploration |
| FR-13.5 | Visual indicator for active tab | P0 | Done | Highlighted border and text color |
| FR-13.6 | Cabinet count badge | P1 | Done | Shows number of selected ingredients |

---

## Non-Functional Requirements

### NFR-1: Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Time to first recommendation | < 8 seconds | Party host is impatient |
| Recipe generation | < 5 seconds | After recommendation selected |
| Page load (cached) | < 1 second | Repeat visits |
| Mobile performance | 90+ Lighthouse | Primary use device |

**Implication**: This constrains CrewAI architecture. Can't have 10 sequential LLM calls.

### NFR-2: Reliability

| Metric | Target | Notes |
|--------|--------|-------|
| Uptime | 99% | Acceptable for side project |
| Graceful degradation | Required | If AI fails, show cached recommendations |
| Valid recipe output | 100% | Never suggest impossible drinks |

### NFR-3: Cost

| Metric | Target | Notes |
|--------|--------|-------|
| Cost per recommendation | < $0.10 | Sustainable without monetization |
| Monthly hosting | < $20 | Fly.io free tier + minimal compute |

### NFR-4: Usability

| Metric | Target | Notes |
|--------|--------|-------|
| Mobile-first | Required | Phone in kitchen is primary context |
| Time to first recommendation | < 60 seconds | From landing to result |
| Return user friction | < 10 seconds | Cabinet already saved |

---

## Technical Architecture

### Simplified CrewAI Design

The original spec proposed 3 crews with 7+ agents. This creates:
- High latency (20-30 seconds)
- High cost ($0.20+ per request)
- Complexity that obscures learning

**Revised Architecture**: 2 crews, 5 agents, with pre-computed data optimization and configurable performance modes.

#### Performance Modes

| Mode | LLM Calls | Latency | Use Case |
|------|-----------|---------|----------|
| Fast mode + no bottle advice | 2 | ~3-4s | Quick recommendations |
| Fast mode + bottle advice (parallel) | 3 | ~3-4s | Standard experience (default) |
| Fast mode + bottle advice (sequential) | 3 | ~5-6s | Fallback mode |
| Full mode + bottle advice | 4 | ~6-8s | Detailed analysis |

**Configuration Options**:
- `fast_mode` (default: True): Uses single unified Drink Recommender agent instead of two sequential agents
- `include_bottle_advice` (default: True): When False, skips the bottle advisor for faster responses
- `PARALLEL_CREWS` (default: True): When enabled, runs Recipe Writer and Bottle Advisor concurrently, reducing latency by ~40%

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│  Cabinet + Mood + Constraints                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-COMPUTED DATA                            │
│  • Cocktail DB with ingredients                                 │
│  • Flavor profiles (static)                                     │
│  • Ingredient categories                                        │
│  • Substitution mappings                                        │
│  • Unlock scores (computed at build time)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CREW 1: ANALYSIS CREW                          │
│                                                                 │
│  Fast Mode (default):                                           │
│  ┌──────────────────────────────────────────┐                  │
│  │        Drink Recommender (unified)       │                  │
│  │              (1 LLM call)                │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
│  Full Mode (fast_mode=False):                                   │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Cabinet Analyst │ →  │   Mood Matcher   │                  │
│  │  (1 LLM call)    │    │   (1 LLM call)   │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  Output: Ranked candidate cocktails (from pre-computed matches) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CREW 2: RECIPE CREW                            │
│                                                                 │
│  Parallel Mode (default, PARALLEL_CREWS=true):                  │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Recipe Writer   │    │  Bottle Advisor  │ ← CONCURRENT     │
│  │  (1 LLM call)    │    │  (1 LLM call)    │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  Sequential Mode (PARALLEL_CREWS=false):                        │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Recipe Writer   │ →  │  Bottle Advisor  │ (optional)       │
│  │  (1 LLM call)    │    │  (1 LLM call)    │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  Output: Full recipe + technique tips + next bottle (optional)  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESPONSE                                  │
│  Recipe + Flavor Profile + Substitutions + Next Bottle          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Optimization**: Heavy pre-computation reduces LLM calls from ~10 to 2-4 depending on mode.

### Data Layer

```
data/
├── cocktails.json          # 103 classic cocktails
│   ├── name
│   ├── ingredients[]
│   ├── method
│   ├── flavor_profile{}
│   └── tags[]
│
├── mocktails.json          # 39 non-alcoholic drinks
│   ├── name
│   ├── ingredients[]
│   ├── method
│   ├── flavor_profile{}
│   └── tags[]
│
├── ingredients.json        # Categorized ingredient list
│   ├── spirits[]
│   ├── modifiers[]
│   ├── bitters_syrups[]
│   ├── fresh[]
│   └── mixers[]
│
├── substitutions.json      # Ingredient swap mappings
│   └── {ingredient: [{sub, quality, ratio_adjust}]}
│
└── unlock_scores.json      # Pre-computed at build time
    └── {bottle: {unlocks: [], score: int}}
```

**Total Drink Database**: 142 drinks (103 cocktails + 39 mocktails)

### API Design

```
POST /api/recommend
  Body: {cabinet: [], mood: str, constraints: [], preferred_spirit?: str}
  Response: {recommendation: Cocktail, alternatives: [], next_bottle: Bottle}

POST /api/another
  Body: {session_id: str, rejected: str}
  Response: {recommendation: Cocktail, ...}

GET /api/recipe/{cocktail_id}
  Response: {recipe: Recipe}

GET /api/cabinet/suggestions
  Response: {quick_cabinets: [{name, ingredients}]}
```

---

## CrewAI Learning Objectives

Since this is also a learning project, the architecture should demonstrate:

| Concept | Where Demonstrated |
|---------|-------------------|
| Agent definition with persona | Bartender agent backstory/voice |
| Tool creation | RecipeDB, FlavorProfiler, SubstitutionFinder |
| Sequential crew execution | Analysis → Recipe flow |
| State management in flows | CocktailFlowState with session |
| Structured output (Pydantic) | Recipe, Recommendation models |
| Anthropic LLM configuration | Temperature, model selection |
| Error handling | Fallback when AI fails |

---

## UX Requirements

### Mobile-First Design

**Main Interface - Tabbed Navigation**
```
┌─────────────────────────┐
│  🍸 Raja                │
│  Your AI Mixologist     │
├─────────────────────────┤
│ [ Chat ] [ Cabinet ] [ Browse ]
├─────────────────────────┤
│                         │
│  Chat messages area     │
│  or Cabinet panel       │
│                         │
├─────────────────────────┤
│  Input controls         │
└─────────────────────────┘
```

**Browse Page**
```
┌─────────────────────────┐
│  Browse Drinks          │
├─────────────────────────┤
│ [🔍 Search drinks...   ]│
│ [All][Cocktails][Mocktails]
│ Difficulty: [Any][Easy]...
├─────────────────────────┤
│  142 drinks found       │
│ ┌───────────────────┐  │
│ │ Drink Card        │  │
│ │ Name + Tagline    │  │
│ │ Type | Difficulty │  │
│ └───────────────────┘  │
├─────────────────────────┤
│ [Ask AI Instead →]      │
└─────────────────────────┘
```

**Key UX Decisions:**

1. **Tabbed navigation** - Chat, Cabinet, Browse as distinct modes
2. **Cabinet as dedicated tab** - Full-screen ingredient management with autocomplete
3. **Browse for exploration** - Full drink catalog with search and filters
4. **Collapsible ingredient categories** - Don't overwhelm with 50 checkboxes
5. **Vibe buttons are large and tappable** - Primary input, make it easy
6. **Loading state is informative** - "Analyzing cabinet... Matching mood..."
7. **Recipe is scannable** - Bold actions, indented details, tips in asides
8. **Individual drink pages** - Deep-linkable recipes with full details

### Critical Flows

**Flow 1: First-Time User (AI Chat)**
1. Land on page → See chat interface with Raja (AI Mixologist)
2. Switch to Cabinet tab → Select ingredients with autocomplete
3. Return to Chat tab → Select mood/vibe
4. Tap "Make Me Something"
5. See recipe in <8 seconds
6. Cabinet saved automatically to localStorage

**Flow 2: Return User (AI Chat)**
1. Land on page → Cabinet pre-filled from local storage
2. Adjust mood if needed in Chat tab
3. Tap "Make Me Something"
4. Total time: <10 seconds to recommendation

**Flow 3: "Show Me Something Else"**
1. View recommendation
2. Tap "Show Me Something Else"
3. New recommendation appears (excluding previous)
4. Repeat as needed

**Flow 4: Browse and Search (New in Session 6)**
1. Navigate to Browse tab or /browse page
2. Browse full catalog of 142 drinks
3. Use search to filter by name
4. Filter by type (Cocktail/Mocktail) or difficulty
5. Tap drink card → View full recipe on /drink/{id}
6. Option: "Ask AI Instead" to get personalized recommendation

**Flow 5: Direct Drink Access**
1. Access /drink/{drink-id} directly (shareable URL)
2. View complete recipe with:
   - Ingredients list with amounts
   - Step-by-step method
   - Flavor profile visualization
   - Timing and difficulty
   - Garnish instructions
3. Navigate back to Browse or Chat as needed

---

## Success Metrics

### Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Recommendation completion rate | >70% | Users who get a result after submitting |
| Time to recommendation | <8 seconds | Server-side timing |
| Return visit rate | >30% | Local storage fingerprinting |
| "Another" button usage | >40% | Users explore multiple options |

### Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cabinet size (avg) | >5 ingredients | Proxy for engagement depth |
| Recipe copy/share rate | >10% | Feature usage |
| Mobile vs desktop | >60% mobile | Validates mobile-first bet |

### Learning Metrics (CrewAI)

| Metric | Target |
|--------|--------|
| Crew execution time | <6 seconds total |
| LLM token usage | <4000 tokens per request |
| Tool call success rate | >99% |

---

## MVP Scope

### Completed (Sessions 1-6)

| Feature | Session | Status |
|---------|------|--------|
| Project setup, CrewAI config | 1 | Done |
| Cocktail database (103 drinks) | 1 | Done |
| Mocktail database (39 drinks) | 1 | Done |
| Skill level system + difficulty tagging | 1 | Done |
| Analysis Crew (cabinet + mood + skill + drink type) | 2 | Done |
| Recipe Crew (recipe + tips + skill-adapted instructions) | 2 | Done |
| Flow orchestration with parallel execution | 3 | Done |
| FastAPI + HTMX frontend | 3-4 | Done |
| "Next bottle" recommendation | 4 | Done |
| "Show me something else" | 4 | Done |
| Local storage (cabinet + skill level) | 4 | Done |
| Mobile optimization | 5 | Done |
| Render deployment | 5 | Done |
| Browse page with search and filters | 6 | Done |
| Individual drink detail pages (/drink/{id}) | 6 | Done |
| Tabbed navigation (Chat/Cabinet/Browse) | 6 | Done |
| Ingredient autocomplete | 6 | Done |
| Flavor profile visualization | 6 | Done |

### Out of Scope (Future)

- User accounts
- Shopping list export
- Recipe ratings/feedback
- Measurement unit toggle
- Social sharing cards
- Recipe history UI + "I made this" tracking
- Quick-add cabinet presets ("Starter kit", "Whiskey lover")

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM latency too high | Medium | High | Pre-compute more, parallelize crews |
| LLM cost unsustainable | Medium | Medium | Cache common requests, use Haiku for simple tasks |
| Invalid recipe generation | Low | High | Validate against DB, fallback to cached recipes |
| Cocktail DB licensing issues | Low | High | Build our own from public domain sources |
| Mobile UX fails | Medium | High | Test on real devices session 3 |
| CrewAI breaking changes | Low | Medium | Pin versions, follow changelog |

---

## Technical Decisions

### Confirmed

| Decision | Rationale |
|----------|-----------|
| Python + FastAPI | CrewAI requirement, good async support |
| HTMX for frontend | Simple, no build step, good for learning |
| Local storage for cabinet | No auth complexity for MVP |
| Fly.io for deployment | Good free tier, simple deployment |
| SQLite for recipe DB | Simple, no external dependency |

### To Decide During Implementation

| Decision | Options | Decide By |
|----------|---------|-----------|
| Crew parallelization | Sequential vs parallel | Session 2 |
| Caching strategy | Redis vs in-memory | Session 3 |
| Cocktail data source | Curate vs license | Session 1 |

---

## Appendix: Cocktail Database Schema

```json
{
  "id": "gold-rush",
  "name": "Gold Rush",
  "tagline": "Whiskey sour's sophisticated cousin",
  "ingredients": [
    {"amount": "2", "unit": "oz", "ingredient": "bourbon"},
    {"amount": "0.75", "unit": "oz", "ingredient": "lemon juice"},
    {"amount": "0.75", "unit": "oz", "ingredient": "honey syrup"}
  ],
  "method": [
    {"action": "Combine", "detail": "Add all ingredients to shaker"},
    {"action": "Shake", "detail": "With ice for 12-15 seconds"},
    {"action": "Strain", "detail": "Into chilled coupe or over fresh ice"}
  ],
  "glassware": "coupe",
  "garnish": "lemon twist",
  "flavor_profile": {
    "sweet": 40,
    "sour": 50,
    "bitter": 10,
    "spirit_forward": 60
  },
  "tags": ["whiskey", "citrus", "easy", "classic"],
  "difficulty": "easy",
  "timing": "3 minutes"
}
```

---

## Development Timeline (Completed)

1. **Session 1**: Project setup + cocktail database curation (103 cocktails, 39 mocktails)
2. **Session 2**: CrewAI agents and crews with parallel execution
3. **Session 3**: FastAPI + HTMX frontend
4. **Session 4**: Integration + "next bottle" logic
5. **Session 5**: Mobile optimization + Render deployment
6. **Session 6**: UX improvements - browse/search, tabbed navigation, drink detail pages

## Future Enhancements

- Recipe history tracking with "I made this" feature
- Quick-add cabinet presets
- Recipe ratings and favorites
- Shopping list export
- Social sharing cards

---

*Document Version: 1.3*
*Created: 2025-12-27*
*Updated: 2025-12-28*
*Status: In Production*
*Changes: Session 6 UX improvements - added browse/search functionality (FR-12), tabbed navigation (FR-13), individual drink detail pages, ingredient autocomplete, updated drink counts (142 total: 103 cocktails + 39 mocktails), revised user flows*
