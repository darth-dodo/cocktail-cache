# Cocktail Cache - Product Requirements Document

## Executive Summary

**Cocktail Cache** is an AI-powered home bar advisor that helps you discover and craft great cocktails with whatever bottles you have. Describe your mood and cabinet contents; the app recommends personalized cocktails, teaches technique, and suggests the next bottle that unlocks the most new drinks.

**Dual Purpose**:
1. A polished, usable product for home drink enthusiasts who want to explore what they can make
2. A CrewAI learning project demonstrating multi-agent orchestration patterns

**Timeline**: 4-6 weeks to Polished MVP

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

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1.1 | User can select ingredients from categorized grid | P0 | Spirits, modifiers, bitters, fresh, mixers |
| FR-1.2 | User can type free-text ingredients | P1 | AI parses "bourbon" from "Maker's Mark" |
| FR-1.3 | Cabinet persists in local storage | P0 | No login required |
| FR-1.4 | Quick-add for common cabinets | P2 | "Starter kit", "Whiskey lover", etc. |
| FR-1.5 | "I have everything" for full exploration | P2 | Power user mode |

**UX Consideration**: Progressive disclosure. Start with just spirits, expand on demand.

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

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-8.1 | Copy recipe to clipboard | P1 | Plain text format |
| FR-8.2 | Shareable URL | P2 | /recipe/{id} |
| FR-8.3 | Recipe card image for social | P3 | Future enhancement |

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

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-11.1 | Mocktail database (20+ drinks) | P0 | Non-alcoholic recipes |
| FR-11.2 | Mocktail toggle on main input | P0 | Cocktail / Mocktail / Both |
| FR-11.3 | Mocktails use same cabinet ingredients | P0 | Citrus, syrups, herbs, mixers |
| FR-11.4 | Flavor profiles for mocktails | P0 | Same visualization as cocktails |
| FR-11.5 | "Spirit-free" badge on recipes | P0 | Clear visual indicator |
| FR-11.6 | Mocktail-specific technique tips | P1 | Building complexity without alcohol |

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

**Revised Architecture**: 2 crews, 4 agents, with pre-computed data optimization

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
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Recipe Writer   │ →  │  Bottle Advisor  │                  │
│  │  (1 LLM call)    │    │  (1 LLM call)    │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  Output: Full recipe + technique tips + next bottle             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESPONSE                                  │
│  Recipe + Flavor Profile + Substitutions + Next Bottle          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Optimization**: Heavy pre-computation reduces LLM calls from ~10 to ~4.

### Data Layer

```
data/
├── cocktails.json          # 100+ classic cocktails
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

```
┌─────────────────────────┐
│  COCKTAIL CACHE         │
├─────────────────────────┤
│  What's the vibe?       │
│  ┌─────┐ ┌─────┐       │
│  │Chill│ │Party│ ...   │
│  └─────┘ └─────┘       │
├─────────────────────────┤
│  Your Cabinet           │
│  ▼ Spirits (tap to expand)
│    ☑ Bourbon            │
│    ☑ Gin                │
│    ☐ Vodka              │
│  ▼ Modifiers            │
│  ▼ Bitters & Syrups     │
│  ▼ Fresh                │
├─────────────────────────┤
│  Any constraints?       │
│  ┌─────────┐ ┌────────┐│
│  │Not sweet│ │Quick   ││
│  └─────────┘ └────────┘│
├─────────────────────────┤
│  [ MAKE ME SOMETHING ]  │
└─────────────────────────┘
```

**Key UX Decisions:**

1. **Collapsible ingredient categories** - Don't overwhelm with 50 checkboxes
2. **Vibe buttons are large and tappable** - Primary input, make it easy
3. **"Make Me Something" is the only CTA** - Clear single action
4. **Loading state is informative** - "Analyzing cabinet... Matching mood..."
5. **Recipe is scannable** - Bold actions, indented details, tips in asides

### Critical Flows

**Flow 1: First-Time User**
1. Land on page → See clear value prop
2. Select vibes (2 taps)
3. Expand "Spirits" → Check 2-3 boxes
4. Optional: expand other categories
5. Tap "Make Me Something"
6. See recipe in <8 seconds
7. Cabinet saved automatically

**Flow 2: Return User**
1. Land on page → Cabinet pre-filled from local storage
2. Adjust mood if needed
3. Tap "Make Me Something"
4. Total time: <10 seconds to recommendation

**Flow 3: "Show Me Something Else"**
1. View recommendation
2. Tap "Show Me Something Else"
3. New recommendation appears (excluding previous)
4. Repeat as needed

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

### In Scope (4-6 weeks)

| Feature | Week |
|---------|------|
| Project setup, CrewAI config | 1 |
| Cocktail database (50 drinks) + Mocktail database (20 drinks) | 1 |
| Skill level system + difficulty tagging | 1 |
| Analysis Crew (cabinet + mood + skill + drink type) | 2 |
| Recipe Crew (recipe + tips + skill-adapted instructions) | 2 |
| Flow orchestration | 3 |
| FastAPI + HTMX frontend | 3-4 |
| "Next bottle" recommendation | 4 |
| "Show me something else" | 4 |
| Local storage (cabinet + skill level + recipe history) | 4 |
| Recipe history UI + "I made this" tracking | 4-5 |
| Mobile optimization | 5 |
| Fly.io deployment | 5 |
| Error handling & polish | 6 |

### Out of Scope (Future)

- User accounts
- Shopping list export
- Recipe ratings/feedback
- Measurement unit toggle
- Social sharing cards

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM latency too high | Medium | High | Pre-compute more, parallelize crews |
| LLM cost unsustainable | Medium | Medium | Cache common requests, use Haiku for simple tasks |
| Invalid recipe generation | Low | High | Validate against DB, fallback to cached recipes |
| Cocktail DB licensing issues | Low | High | Build our own from public domain sources |
| Mobile UX fails | Medium | High | Test on real devices week 3 |
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
| Crew parallelization | Sequential vs parallel | Week 2 |
| Caching strategy | Redis vs in-memory | Week 3 |
| Cocktail data source | Curate vs license | Week 1 |

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

## Next Steps

1. **Week 1**: Project setup + cocktail database curation
2. **Week 2**: CrewAI agents and crews
3. **Week 3**: FastAPI + HTMX frontend
4. **Week 4**: Integration + "next bottle" logic
5. **Week 5**: Mobile optimization + deployment
6. **Week 6**: Polish, error handling, documentation

---

*Document Version: 1.0*
*Created: 2025-12-27*
*Status: Ready for Implementation*
