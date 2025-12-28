# Design Document: Suggest Another Bottle Feature

**Author:** Claude Code
**Date:** 2025-12-28
**Status:** Draft
**Branch:** ux-improvements

---

## 1. Overview

### 1.1 Problem Statement

Users of Cocktail Cache have a cabinet of ingredients stored in localStorage, but currently lack a dedicated way to discover which bottles would provide the best return on investment (ROI) for expanding their drink-making capabilities. While the `/api/flow` endpoint already returns `next_bottle` recommendations as part of the drink recommendation flow, there is no standalone page where users can:

1. View their current cabinet at a glance
2. See a ranked list of bottle purchase suggestions
3. Understand the unlock potential of each suggested bottle
4. Make informed purchasing decisions to maximize their cocktail repertoire

### 1.2 User Value

- **Discovery**: Help users discover which bottles unlock the most new drinks
- **Planning**: Enable informed purchasing decisions based on ROI analysis
- **Engagement**: Provide a reason for users to return and check recommendations as their cabinet evolves
- **Utility**: Surface the existing UnlockCalculatorTool functionality in a user-friendly interface

### 1.3 Success Metrics

- Users can access bottle suggestions within 2 clicks from any page
- Page loads with recommendations in under 500ms
- Users understand the unlock potential through visual representation
- Mobile-responsive design consistent with existing UI patterns

---

## 2. Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                        │
├─────────────────────────────────────────────────────────────────┤
│  localStorage                                                    │
│  ├── cocktail-cache-cabinet: ["bourbon", "gin", ...]            │
│                                                                  │
│  suggest-bottle.html Template                                   │
│  ├── Current Cabinet Display                                    │
│  ├── Top 5 Recommendations List                                 │
│  └── Visual unlock potential indicators                         │
│                                                                  │
│  JavaScript                                                      │
│  ├── Read cabinet from localStorage                             │
│  ├── POST to /api/suggest-bottles                               │
│  └── Render recommendations with drinks list                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ POST /api/suggest-bottles
                              │ { cabinet: [...], limit: 5 }
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  api.py Router                                                   │
│  └── POST /api/suggest-bottles                                  │
│      ├── Validate request                                        │
│      ├── Invoke UnlockCalculatorTool._run()                     │
│      └── Return structured JSON response                        │
│                                                                  │
│  UnlockCalculatorTool (existing)                                │
│  └── Calculate which bottles unlock most drinks                 │
│      ├── Load unlock_scores from data                           │
│      ├── Find currently makeable drinks                         │
│      ├── Score each missing ingredient                          │
│      └── Return ranked recommendations                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
1. User navigates to /suggest-bottle
   │
2. Page loads, JavaScript reads localStorage
   │  cabinet = ["bourbon", "lemons", "honey", ...]
   │
3. POST /api/suggest-bottles
   │  Request: { cabinet: [...], drink_type: "both", limit: 5 }
   │
4. Backend calls UnlockCalculatorTool._run()
   │  ├── Loads unlock_scores.json
   │  ├── Calculates makeable drinks with current cabinet
   │  ├── For each missing ingredient:
   │  │   └── Count how many new drinks it would complete
   │  └── Sort by unlock count, take top 5
   │
5. Return response
   │  {
   │    "current_status": { "drinks_you_can_make": 8, ... },
   │    "recommendations": [
   │      { "ingredient_id": "sweet-vermouth", "new_drinks_unlocked": 5, "drinks": [...] },
   │      ...
   │    ]
   │  }
   │
6. Frontend renders recommendations
   └── Display cards with unlock potential bars and drink lists
```

### 2.3 Component Dependencies

| Component | Depends On | Provides |
|-----------|------------|----------|
| Navbar (base.html) | - | Link to /suggest-bottle |
| suggest-bottle.html | base.html, glassmorphic.css | Page template |
| /suggest-bottle route | FastAPI pages router | HTML page serving |
| /api/suggest-bottles | UnlockCalculatorTool | JSON recommendations |
| UnlockCalculatorTool | unlock_scores.json, drinks.json | Calculation logic |

---

## 3. API Endpoint Specification

### 3.1 Endpoint Definition

**POST /api/suggest-bottles**

Calculates and returns bottle purchase recommendations based on the user's current cabinet.

### 3.2 Request Model

```python
class SuggestBottlesRequest(BaseModel):
    """Request model for bottle suggestions."""

    cabinet: list[str] = Field(
        ...,
        description="List of ingredient IDs the user already has",
        min_items=0,
    )
    drink_type: Literal["cocktails", "mocktails", "both"] = Field(
        default="both",
        description="Filter recommendations by drink type",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of recommendations to return",
    )
```

### 3.3 Response Model

```python
class UnlockedDrink(BaseModel):
    """A drink that would be unlocked by purchasing a bottle."""

    id: str = Field(..., description="Drink identifier")
    name: str = Field(..., description="Display name")
    is_mocktail: bool = Field(..., description="Whether it's a mocktail")
    difficulty: str = Field(..., description="Difficulty level")


class BottleRecommendation(BaseModel):
    """A single bottle recommendation."""

    ingredient_id: str = Field(..., description="Ingredient ID to purchase")
    ingredient_name: str = Field(..., description="Human-readable ingredient name")
    new_drinks_unlocked: int = Field(..., description="Number of new drinks this unlocks")
    drinks: list[UnlockedDrink] = Field(..., description="List of drinks this would unlock")


class SuggestBottlesResponse(BaseModel):
    """Response model for bottle suggestions."""

    current_status: dict = Field(
        ...,
        description="Current cabinet status including makeable drink count",
    )
    recommendations: list[BottleRecommendation] = Field(
        ...,
        description="Ranked list of bottle recommendations",
    )
    total_recommendations: int = Field(
        ...,
        description="Total number of possible recommendations (before limit)",
    )
```

### 3.4 Example Request/Response

**Request:**
```json
POST /api/suggest-bottles
Content-Type: application/json

{
    "cabinet": ["bourbon", "lemons", "honey", "angostura-bitters"],
    "drink_type": "both",
    "limit": 5
}
```

**Response:**
```json
{
    "current_status": {
        "drinks_you_can_make": 3,
        "drinks_makeable": [
            { "id": "whiskey-sour", "name": "Whiskey Sour", "is_mocktail": false },
            { "id": "gold-rush", "name": "Gold Rush", "is_mocktail": false },
            { "id": "honey-lemonade", "name": "Honey Lemonade", "is_mocktail": true }
        ]
    },
    "recommendations": [
        {
            "ingredient_id": "sweet-vermouth",
            "ingredient_name": "Sweet Vermouth",
            "new_drinks_unlocked": 5,
            "drinks": [
                { "id": "manhattan", "name": "Manhattan", "is_mocktail": false, "difficulty": "easy" },
                { "id": "boulevardier", "name": "Boulevardier", "is_mocktail": false, "difficulty": "easy" }
            ]
        },
        {
            "ingredient_id": "gin",
            "ingredient_name": "Gin",
            "new_drinks_unlocked": 4,
            "drinks": [
                { "id": "bee-knees", "name": "Bee's Knees", "is_mocktail": false, "difficulty": "easy" }
            ]
        }
    ],
    "total_recommendations": 42
}
```

### 3.5 Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| 400 | Invalid drink_type | `{ "detail": "drink_type must be 'cocktails', 'mocktails', or 'both'" }` |
| 422 | Validation error | Standard Pydantic validation error |

---

## 4. UI Design

### 4.1 Wireframe Description

The page follows the existing glassmorphic design patterns established in `browse.html`.

```
┌──────────────────────────────────────────────────────────────────┐
│  [Logo] Cocktail Cache          [Cabinet] [Browse] [Suggest] [API]│
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│     ┌─────────────────────────────────────────────────────┐      │
│     │  glass-card: Header                                  │      │
│     │  ═══════════════════════════════════════════════════│      │
│     │  "Suggest Your Next Bottle"                         │      │
│     │  "Discover which bottles unlock the most drinks"    │      │
│     └─────────────────────────────────────────────────────┘      │
│                                                                   │
│     ┌─────────────────────────────────────────────────────┐      │
│     │  glass-card: Your Cabinet                           │      │
│     │  ═══════════════════════════════════════════════════│      │
│     │  [bourbon] [gin] [lemons] [honey] [+ 3 more]        │      │
│     │                                                      │      │
│     │  You can make 8 drinks                              │      │
│     │  [Edit Cabinet →]                                   │      │
│     └─────────────────────────────────────────────────────┘      │
│                                                                   │
│     ┌─────────────────────────────────────────────────────┐      │
│     │  glass-card: Top Recommendations                    │      │
│     │  ═══════════════════════════════════════════════════│      │
│     │                                                      │      │
│     │  ┌─────────────────────────────────────────────┐   │      │
│     │  │  #1 Sweet Vermouth                          │   │      │
│     │  │  ═══════════════════════════════════════════│   │      │
│     │  │  Unlocks 5 new drinks                       │   │      │
│     │  │  [████████████████████░░░░░░] 5/142         │   │      │
│     │  │                                              │   │      │
│     │  │  Drinks unlocked:                           │   │      │
│     │  │  [Manhattan] [Boulevardier] [Negroni] ...   │   │      │
│     │  └─────────────────────────────────────────────┘   │      │
│     │                                                      │      │
│     │  ┌─────────────────────────────────────────────┐   │      │
│     │  │  #2 Gin                                      │   │      │
│     │  │  ═══════════════════════════════════════════│   │      │
│     │  │  Unlocks 4 new drinks                       │   │      │
│     │  │  [█████████████████░░░░░░░░░] 4/142         │   │      │
│     │  │  ...                                         │   │      │
│     │  └─────────────────────────────────────────────┘   │      │
│     │                                                      │      │
│     │  [... 3 more recommendation cards ...]              │      │
│     │                                                      │      │
│     └─────────────────────────────────────────────────────┘      │
│                                                                   │
│     ┌─────────────────────────────────────────────────────┐      │
│     │  glass-card: Empty State (if cabinet empty)         │      │
│     │  ═══════════════════════════════════════════════════│      │
│     │  [icon] Add some bottles to your cabinet first      │      │
│     │  [Go to Cabinet →]                                  │      │
│     └─────────────────────────────────────────────────────┘      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Visual Components

#### Cabinet Display
- **Ingredient chips**: Use existing `glass-chip` styling with ingredient emojis
- **Count indicator**: "You can make X drinks" in `text-amber-300`
- **Edit link**: Ghost button linking to home page cabinet editor

#### Recommendation Card
- **Rank badge**: Circular badge with position number (1-5)
- **Ingredient name**: Large heading in `text-amber-300`
- **Unlock count**: Secondary text showing number of new drinks
- **Progress bar**: Visual representation of unlock potential
  - Width proportional to `new_drinks_unlocked / max_unlocked`
  - Use amber gradient: `from-amber-500 to-orange-500`
- **Drinks list**: Horizontal scrollable list of drink chips
  - Click navigates to `/drink/{id}` detail page
  - Show cocktail/mocktail badge on each

#### Empty States
- **No cabinet**: Prompt user to add bottles with link to home
- **No recommendations**: "You have all the bottles!" celebration message

### 4.3 Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| Mobile (<640px) | Single column, stacked cards, horizontal scroll for drink chips |
| Tablet (640-1024px) | Single column with wider cards |
| Desktop (>1024px) | Centered max-w-4xl container |

---

## 5. Implementation Tasks

### Phase 1: Backend API (Priority: High)

| Task | Description | Estimate |
|------|-------------|----------|
| 5.1.1 | Create Pydantic request/response models in `api.py` | 15 min |
| 5.1.2 | Implement POST `/api/suggest-bottles` endpoint | 30 min |
| 5.1.3 | Add ingredient name resolution (ID to display name) | 15 min |
| 5.1.4 | Add unit tests for the endpoint | 20 min |

**Total Phase 1:** ~1.5 hours

### Phase 2: Frontend Template (Priority: High)

| Task | Description | Estimate |
|------|-------------|----------|
| 5.2.1 | Create `suggest-bottle.html` template extending base.html | 20 min |
| 5.2.2 | Implement cabinet display section | 20 min |
| 5.2.3 | Create recommendation card template with progress bar | 30 min |
| 5.2.4 | Implement JavaScript for API call and rendering | 30 min |
| 5.2.5 | Add empty state handling | 15 min |
| 5.2.6 | Add loading state animation | 10 min |

**Total Phase 2:** ~2 hours

### Phase 3: Navigation Integration (Priority: High)

| Task | Description | Estimate |
|------|-------------|----------|
| 5.3.1 | Add "Suggest" link to navbar in `base.html` | 10 min |
| 5.3.2 | Add page route in FastAPI pages router | 10 min |
| 5.3.3 | Verify navigation works from all pages | 5 min |

**Total Phase 3:** ~25 minutes

### Phase 4: Polish & Testing (Priority: Medium)

| Task | Description | Estimate |
|------|-------------|----------|
| 5.4.1 | Mobile responsiveness testing and fixes | 20 min |
| 5.4.2 | Accessibility audit (ARIA labels, keyboard nav) | 15 min |
| 5.4.3 | Cross-browser testing | 15 min |
| 5.4.4 | Integration test for full user flow | 20 min |

**Total Phase 4:** ~1 hour

### Total Estimated Implementation Time: ~5 hours

---

## 6. Technical Notes

### 6.1 Reusing UnlockCalculatorTool

The existing `UnlockCalculatorTool._run()` method returns a JSON string. The new API endpoint will:

1. Parse the JSON output from the tool
2. Transform it into the typed response model
3. Add `ingredient_name` field using the ingredient database

```python
# In api.py
from src.app.tools.unlock_calculator import UnlockCalculatorTool

@router.post("/suggest-bottles", response_model=SuggestBottlesResponse)
async def suggest_bottles(request: SuggestBottlesRequest) -> SuggestBottlesResponse:
    tool = UnlockCalculatorTool()
    result_json = tool._run(
        cabinet=request.cabinet,
        drink_type=request.drink_type,
        limit=request.limit,
    )
    result = json.loads(result_json)

    # Add ingredient names from database
    ingredients_db = load_ingredients()
    for rec in result["recommendations"]:
        rec["ingredient_name"] = get_ingredient_name(rec["ingredient_id"], ingredients_db)

    return SuggestBottlesResponse(**result)
```

### 6.2 localStorage Synchronization

The page should listen for cabinet updates to refresh recommendations:

```javascript
// Listen for same-tab updates
window.addEventListener('cabinet-updated', fetchRecommendations);

// Listen for cross-tab updates
window.addEventListener('storage', (e) => {
    if (e.key === 'cocktail-cache-cabinet') {
        fetchRecommendations();
    }
});
```

### 6.3 Caching Considerations

For future optimization, recommendations could be cached:
- **Client-side**: Cache response in sessionStorage keyed by cabinet hash
- **Server-side**: Memoize `UnlockCalculatorTool._run()` with LRU cache

---

## 7. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| Filter by drink type | Toggle between cocktails/mocktails/both | Medium |
| Sort options | Sort by unlock count, alphabetically, by price estimate | Low |
| Purchase links | External links to buy recommended bottles | Low |
| Cabinet comparison | "If you also had X, you could make Y more drinks" | Low |
| Shareable recommendations | Generate shareable link with cabinet state | Low |

---

## 8. Open Questions

1. **Should we show drinks the user can already make?**
   - Current design shows only new unlocks
   - Could add collapsible "You can already make..." section

2. **How to handle very long drink lists?**
   - Current design shows all drinks in horizontal scroll
   - Could limit to 5-6 with "+X more" indicator

3. **Should recommendations update live as cabinet changes?**
   - Current design requires page load or cabinet-updated event
   - Could add real-time updates with WebSocket (overkill for MVP)

---

## 9. Appendix

### A. Related Files

| File | Purpose |
|------|---------|
| `/src/app/templates/base.html` | Navbar structure, cabinet indicator script |
| `/src/app/tools/unlock_calculator.py` | Core calculation logic |
| `/src/app/routers/api.py` | API patterns and existing endpoints |
| `/src/app/templates/browse.html` | Page design patterns |
| `/src/app/static/css/glassmorphic.css` | Styling classes |
| `/src/app/services/data_loader.py` | Data loading utilities |

### B. CSS Classes to Use

From `glassmorphic.css`:
- `.glass-card` - Main container cards
- `.glass-card-accent` - Highlighted recommendation card (top pick)
- `.glass-chip` - Ingredient and drink chips
- `.glass-btn-primary` - Call-to-action buttons
- `.glass-btn-secondary` - Secondary actions
- `.animate-fade-in` - Entry animation
- `.text-amber-300` - Primary headings
- `.text-stone-400` - Secondary text
