# Redesign "Grow Your Bar" Suggest Feature (CrewAI Agent)

## Problem Statement
The current suggest feature recommends bottles but counts ALL missing ingredients, making recommendations less actionable. A user with bourbon + simple syrup sees "add gin to unlock 22 drinks" but can't actually make those drinks without also having fresh ingredients, mixers, etc.

## Solution: CrewAI "Bar Growth Advisor" Agent
Create a dedicated CrewAI agent that provides **intelligent, personalized recommendations** with reasoning - not just a list of bottles.

## Design Philosophy
**Track your BAR (bottles), assume your KITCHEN (fresh/mixers)**

Users should only need to track bottles they've invested in. Fresh ingredients, mixers, and basic syrups are assumed available from any grocery store.

## Ingredient Tier Classification

| Tier | Categories | Tracking | Recommendations |
|------|-----------|----------|-----------------|
| **Core Bottles** | Spirits, Modifiers (liqueurs), Non-Alcoholic | Track in cabinet | Recommend as purchases |
| **Essentials** | Bitters, specialty syrups (orgeat, falernum) | Optional tracking | Show in separate "Don't forget" section |
| **Kitchen** | Fresh (juices, herbs, garnishes), Mixers, basic syrups | Assume available | Never require for "makeable" count |

## Algorithm Changes

### 1. "Drinks Makeable Now" (Lenient)
```
makeable = drinks where user has ALL Core Bottles (spirits + liqueurs)
ignore: bitters, syrups, fresh, mixers
```

### 2. "Bottle Recommendations"
```
for each missing Core Bottle:
  count drinks where:
    - user has all OTHER Core Bottles needed
    - (don't check bitters/fresh/mixers)
  recommend bottles that unlock the most drinks
```

### 3. "Essentials" Section (New)
```
for each missing Essential (bitters, specialty syrup):
  count drinks it appears in (that user can otherwise make)
  show as "Don't forget: Angostura bitters (used in 15 drinks)"
```

## UI Layout

```
┌─────────────────────────────────────────┐
│ Grow Your Bar                           │
│ Based on your 4 bottles                 │
│                                    12   │
│                          drinks you can │
│                                    make │
├─────────────────────────────────────────┤
│ Recommended Bottles                     │
│                                         │
│ 🍸 Gin                      +8 drinks  │
│    Unlocks: G&T, Martini, Negroni...   │
│    [Add to Bar]                         │
│                                         │
│ 🥃 White Rum                +5 drinks  │
│    Unlocks: Mojito, Daiquiri...        │
│    [Add to Bar]                         │
├─────────────────────────────────────────┤
│ Don't Forget (Essentials)               │
│                                         │
│ 🧪 Angostura Bitters    in 15 drinks   │
│ 🧪 Orange Bitters       in 8 drinks    │
└─────────────────────────────────────────┘
```

## CrewAI Agent Architecture

### New Agent: `bar_growth_advisor.py`
Following the existing pattern (no tools, data injection):
- Agent provides personalized recommendations with reasoning
- Pre-computed data injected into task description
- Pydantic output model for structured responses

### Agent Config (`agents.yaml`)
```yaml
bar_growth_advisor:
  role: "Bar Growth Advisor"
  goal: "Provide strategic bottle purchase recommendations to maximize cocktail-making potential"
  backstory: |
    You are an expert bartender and bar consultant who helps home bartenders
    build their collection strategically. You understand that building a home bar
    is an investment, and you help prioritize purchases that unlock the most
    classic and versatile cocktails.

    You consider:
    - Which bottles unlock the most new drinks
    - Synergy with existing collection (e.g., if they have bourbon, recommend vermouth for Manhattans)
    - Classic vs. specialty bottles (prioritize versatile staples)
    - Budget-friendly alternatives when relevant

    You always explain WHY each bottle is recommended, not just what to buy.
  verbose: false
  allow_delegation: false
```

### Output Models (`models/crew_io.py`)
```python
class BarGrowthRecommendation(BaseModel):
    """A single bottle recommendation with reasoning."""
    ingredient_id: str
    name: str
    unlocks: int
    reasoning: str
    signature_drinks: list[str]

class BarGrowthOutput(BaseModel):
    """Output from the Bar Growth Advisor agent."""
    summary: str
    top_recommendation: BarGrowthRecommendation
    additional_recommendations: list[BarGrowthRecommendation]
    essentials_note: str | None
    next_milestone: str
```

## Data Flow

```
POST /api/suggest-bottles
    ↓
[1] Pre-compute (Python, no LLM):
    - Classify ingredients by tier
    - Calculate drinks_makeable (Core Bottles only)
    - Rank bottles by unlock potential
    - Check essentials status
    ↓
[2] Format for Agent:
    - cabinet_formatted: "Bourbon, Gin, Sweet Vermouth"
    - makeable_drinks_list: "Old Fashioned, Martini, Manhattan..."
    - bottle_rankings: "1. Vodka (+8 drinks), 2. Rum (+6 drinks)..."
    - essentials_status: "Missing: Angostura (in 15 drinks)"
    ↓
[3] Run BarGrowthCrew:
    - crew.run(inputs={...})
    - Agent generates personalized recommendations with reasoning
    ↓
[4] Return Response:
    - summary, top_recommendation, additional, essentials_note
```

## Files to Create/Modify

### New Files
| File | Description |
|------|-------------|
| `src/app/agents/bar_growth_advisor.py` | Agent factory function |
| `src/app/crews/bar_growth_crew.py` | Crew for bar growth analysis |

### Modified Files
| File | Changes |
|------|---------|
| `src/app/agents/config/agents.yaml` | Add `bar_growth_advisor` config |
| `src/app/agents/config/tasks.yaml` | Add `advise_bar_growth` task |
| `src/app/models/crew_io.py` | Add `BarGrowthOutput`, `BarGrowthRecommendation` |
| `src/app/routers/api.py` | Update `/api/suggest-bottles` to use crew |
| `src/app/static/js/suggest-panel.js` | Display AI-generated summary and reasoning |

## Implementation Steps

1. Add tier classification functions in `api.py`
2. Create output models in `models/crew_io.py`
3. Add agent config to `agents.yaml`
4. Add task config to `tasks.yaml`
5. Create agent `bar_growth_advisor.py`
6. Create crew `bar_growth_crew.py`
7. Update API endpoint to use crew
8. Update frontend to display AI summary and reasoning

## Testing

- Test with cabinet: `[bourbon]` → should show many makeable (Old Fashioned, etc.)
- Test with cabinet: `[bourbon, gin, vodka]` → should show high makeable count
- Verify AI reasoning is helpful and personalized
- Verify essentials note mentions missing bitters
- Test edge cases: empty cabinet, complete bar
