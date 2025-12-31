# Playwright Testing Guide

> **Last Updated**: December 2025
> **Test Status**: All core flows passing
> **Application**: Cocktail Cache - AI-Powered Drink Recommendations

---

## Quick Start

### Prerequisites
```bash
# Start the application server
uvicorn src.app.main:app --host 0.0.0.0 --port 8000

# Verify server is running
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development","version":"0.1.0"}
```

### Running Tests with Playwright MCP
Use the Playwright MCP server tools for browser automation:
- `browser_navigate` - Navigate to URLs
- `browser_snapshot` - Capture page state (preferred over screenshots)
- `browser_click` - Click elements by ref
- `browser_type` - Type into inputs
- `browser_wait_for` - Wait for text/elements

---

## Test Report (December 2025)

### Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Homepage & Navigation | ✅ Pass | 4 tabs load correctly |
| Browse Tab | ✅ Pass | 142 drinks, search/filter working |
| Chat with Raja | ✅ Pass | AI responds with recommendations |
| Drink Detail Pages | ✅ Pass | Full recipe display |
| Cabinet Selection | ✅ Pass | Categorized ingredients |
| Suggest/Grow Your Bar | ✅ Pass | Smart bottle recommendations |

### Metrics Captured
- **Total Drinks**: 142 (103 cocktails + 39 mocktails)
- **Ingredient Categories**: 6 (Spirits, Liqueurs, Bitters, Fresh, Mixers, Non-Alcoholic)
- **With 2 ingredients** (Bourbon, Sweet Vermouth): 44 makeable drinks (54%)
- **With 3 ingredients** (+ Gin): 53 makeable drinks (62%)

---

## Application Structure

### URL Routes
| Route | Description |
|-------|-------------|
| `/` | Main SPA with tabbed interface |
| `/browse` | Full drink catalog (alternative entry) |
| `/drink/{drink_id}` | Individual drink detail page |
| `/health` | Health check endpoint |

### Tab Navigation
The main interface uses a tabbed navigation system:

1. **Chat** - Conversation with Raja AI bartender
2. **Cabinet** - Manage your ingredient inventory
3. **Browse** - Search and filter all drinks
4. **Suggest** - Get bottle purchase recommendations

---

## User Flows to Test

### Flow 1: First-Time User Experience
```
1. Navigate to http://localhost:8000/
2. Verify header shows "Cocktail Cache" with "Raja - Your AI Mixologist"
3. Verify 4 tabs visible: Chat, Cabinet, Browse, Suggest
4. Chat tab should be active by default
5. Raja's welcome message should be visible
```

**Expected Elements**:
- Heading: "Cocktail Cache"
- Subheading: "Raja - Your AI Mixologist"
- Raja greeting contains: "welcome" and "mood today"

### Flow 2: Browse and Search Drinks
```
1. Click "Browse" tab
2. Verify drink grid loads with count (e.g., "142 drinks")
3. Type "whiskey" in search box
4. Verify filtered results show whiskey-related drinks
5. Click difficulty filter (e.g., "Easy")
6. Verify results update
7. Click a drink card to view details
```

**Test Data**:
- Search "margarita" → Should find Margarita, Tommy's Margarita
- Search "negroni" → Should find Negroni, Boulevardier
- Filter "mocktail" → Should show ~39 results

### Flow 3: Chat with Raja
```
1. Click "Chat" tab
2. Type a message: "What whiskey cocktails can you recommend?"
3. Submit message (Enter or click send)
4. Wait for Raja's response
5. Verify response contains drink recommendation
6. Click on any drink link in response
7. Verify navigation to drink detail page
```

**Raja Response Characteristics**:
- Uses Hindi-English phrases: "yaar", "Arrey", "bilkul"
- Provides specific drink recommendations
- Includes drink IDs as clickable links

### Flow 4: Cabinet Management
```
1. Click "Cabinet" tab
2. Verify category sections visible:
   - Spirits (26 items)
   - Liqueurs & Modifiers (41 items)
   - Bitters & Syrups (29 items)
   - Fresh & Produce (41 items)
   - Mixers (31 items)
   - Non-Alcoholic (12 items)
3. Click a category header to expand/collapse
4. Click an ingredient to select (e.g., "Bourbon")
5. Verify ingredient appears in "selected" area
6. Verify badge on Cabinet tab updates
7. Click X on selected ingredient to remove
8. Use search box to filter ingredients
```

**Important**: Categories may be collapsed by default. Click category header to expand before selecting ingredients within.

### Flow 5: Suggest/Grow Your Bar
```
1. Add 2+ ingredients to Cabinet (e.g., Bourbon, Sweet Vermouth)
2. Click "Suggest" tab
3. Verify "Grow Your Bar" heading appears
4. Verify shows "X drinks you can make"
5. Verify progress bar and percentage
6. Verify bottle recommendations with "+N drinks" badges
7. Click "Add to Cabinet" on a recommendation
8. Verify drink count increases
```

**Expected Behavior**:
- Shows personalized recommendations based on cabinet
- Recommendations sorted by unlock potential
- Categories: Spirits, Liqueurs & Modifiers, etc.

### Flow 6: Drink Detail Page
```
1. Navigate to a drink (via Browse, Chat, or direct URL)
2. Verify drink name and tagline
3. Verify metadata: difficulty, timing, glassware
4. Verify ingredients list with amounts
5. Verify method steps
6. Verify flavor profile visualization (if present)
7. Click "Back to Browse" or browser back
```

**Test URLs**:
- `/drink/whiskey-sour`
- `/drink/margarita`
- `/drink/old-fashioned`
- `/drink/negroni`

---

## Element Reference Guide

### Common Selectors

| Element | How to Find | Notes |
|---------|-------------|-------|
| Chat tab | `tab "Chat"` | First tab |
| Cabinet tab | `tab "Cabinet"` | Shows ingredient count badge |
| Browse tab | `tab "Browse"` | Links to browse page |
| Suggest tab | `tab "Suggest"` | Shows recommendations |
| Search input | `textbox "Search"` | In Browse and Cabinet |
| Drink cards | `heading` within card | Click to view details |
| Category headers | `button` with category name | Click to expand/collapse |
| Ingredient buttons | `button` with ingredient name | Click to select/deselect |
| Add to Cabinet | `button "Add to Cabinet"` | In Suggest tab |

### Snapshot Analysis Tips

1. **Use `browser_snapshot`** instead of screenshots for element refs
2. **Look for `[ref=eXXX]`** values to use with `browser_click`
3. **Check `[selected]` or `[active]`** attributes for state
4. **Categories may be collapsed** - click header first if ingredients not visible

---

## Known Issues & Workarounds

### Issue 1: Click Intercepted by Collapsed Category
**Symptom**: Timeout when clicking ingredient in collapsed category
**Solution**: Click category header first to expand, then click ingredient

```
# Wrong: Direct click on ingredient in collapsed section
browser_click(element="Sweet Vermouth", ref="e123")  # May timeout

# Right: Expand category first
browser_click(element="Liqueurs & Modifiers category", ref="e100")
browser_click(element="Sweet Vermouth", ref="e123")
```

### Issue 2: Cabinet Badge Sync After Suggest Add
**Symptom**: Adding ingredient via Suggest may not immediately update Cabinet badge
**Impact**: Minor visual inconsistency
**Workaround**: Refresh page or switch tabs to sync

### Issue 3: Loading States
**Symptom**: Actions may show "Loading..." or "Finding recommendations..."
**Solution**: Use `browser_wait_for` to wait for content:
```
browser_wait_for(text="drinks you can make")
browser_wait_for(text="Grow Your Bar")
```

---

## Test Data Reference

### Sample Ingredients for Testing
| Category | Good Test Items |
|----------|-----------------|
| Spirits | Bourbon, Gin, Vodka, White Rum, Tequila |
| Liqueurs | Sweet Vermouth, Dry Vermouth, Campari, Triple Sec |
| Bitters | Angostura Bitters, Orange Bitters |
| Fresh | Lemon Juice, Lime Juice, Mint |
| Mixers | Soda Water, Tonic Water, Ginger Beer |

### Sample Drink IDs
- `whiskey-sour`
- `old-fashioned`
- `margarita`
- `negroni`
- `mojito`
- `manhattan`
- `daiquiri`
- `tom-collins`

### Cabinet Combinations to Test
| Ingredients | Expected Drinks |
|-------------|-----------------|
| Bourbon, Sweet Vermouth | ~44 drinks |
| Bourbon, Sweet Vermouth, Gin | ~53 drinks |
| Gin, Dry Vermouth | Martini-family drinks |
| Rum, Lime Juice, Simple Syrup | Daiquiri, Mojito base |

---

## Automated Test Checklist

Use this checklist for regression testing:

- [ ] Server starts and health check passes
- [ ] Homepage loads with all 4 tabs
- [ ] Browse shows 142 drinks
- [ ] Search filters drinks correctly
- [ ] Type filter (cocktail/mocktail) works
- [ ] Difficulty filter works
- [ ] Drink detail page loads
- [ ] Chat sends and receives messages
- [ ] Raja responds with personality
- [ ] Drink links in chat are clickable
- [ ] Cabinet categories expand/collapse
- [ ] Ingredients can be selected/deselected
- [ ] Cabinet persists across tab switches
- [ ] Suggest shows recommendations
- [ ] Add to Cabinet from Suggest works
- [ ] Drink count updates after adding ingredients

---

## Future Test Expansion

### Recommended Additional Tests
1. **Mobile viewport testing** - Resize browser to 375x667
2. **Accessibility testing** - Tab navigation, ARIA labels
3. **Error states** - Invalid drink IDs, network failures
4. **Edge cases** - Empty cabinet, no matching drinks
5. **Performance** - Page load times, response times

### Integration with CI/CD
Consider adding Playwright tests to CI pipeline:
```yaml
# Example GitHub Actions step
- name: Run Playwright Tests
  run: |
    uvicorn src.app.main:app &
    sleep 5
    # Run playwright test script
```
