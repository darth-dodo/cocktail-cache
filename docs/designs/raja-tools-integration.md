# Design Document: Raja Tools Integration

> **Status**: Draft
> **Author**: Claude Code
> **Date**: 2025-12-31
> **Branch**: `feat/raja-tools-integration`

## Overview

Repurpose the existing but unused CrewAI tools (`src/app/tools/`) to give Raja the bartender dynamic data access capabilities during chat conversations.

## Problem Statement

### Current State
- 4 tools exist in `src/app/tools/` but are **never used**
- Raja receives pre-injected data via prompt context
- Large prompts with full drink database on every message
- Tools duplicate functionality in `src/app/services/drink_data.py`

### Issues
1. **Dead code**: Tools are defined but not wired to any agent
2. **Large context**: Every chat message includes full drink list
3. **Static responses**: Raja can't dynamically look up information
4. **Duplication**: Same logic in tools and services

## Proposed Solution

Wire the existing tools into Raja's agent, allowing dynamic data access during conversation.

### Architecture Change

```
BEFORE (Prompt Injection):
┌─────────────────────────────────────────────────────┐
│ User Message                                        │
│ + Full Drink Database (injected)                    │
│ + Cabinet Contents (injected)                       │
│ + Substitutions (injected)                          │
└─────────────────────┬───────────────────────────────┘
                      ▼
              ┌───────────────┐
              │  Raja Agent   │
              │  (no tools)   │
              └───────────────┘

AFTER (Tool-Based):
┌─────────────────────────────────────────────────────┐
│ User Message + Cabinet Context (minimal)            │
└─────────────────────┬───────────────────────────────┘
                      ▼
              ┌───────────────┐
              │  Raja Agent   │◄────┐
              │  (with tools) │     │
              └───────┬───────┘     │
                      │             │
        ┌─────────────┼─────────────┼─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
   │ Recipe  │  │ Substi-  │  │ Unlock   │  │ Flavor  │
   │ DBTool  │  │ tution   │  │ Calc     │  │ Profiler│
   └─────────┘  └──────────┘  └──────────┘  └─────────┘
```

## Tool Specifications

### 1. RecipeDBTool (Search Drinks)

**Current**: Returns JSON list of drinks
**Repurposed**: Returns Raja-friendly conversational response

```python
# Input
{"cabinet": ["vodka", "lime"], "mood": "refreshing", "limit": 3}

# Output (conversational)
"Arrey, with vodka and lime you can make these beauties:
1. **Moscow Mule** - Refreshing ginger kick, easy to make
2. **Vodka Gimlet** - Classic and elegant, yaar
3. **Cosmopolitan** - Pink and fancy, perfect for celebrations"
```

### 2. SubstitutionFinderTool (Find Alternatives)

**Current**: Returns JSON substitution rules
**Repurposed**: Natural language suggestions

```python
# Input
{"ingredient": "bourbon"}

# Output (conversational)
"No bourbon? No problem, bhai! You can use:
- **Rye whiskey** - Spicier but works perfectly
- **Tennessee whiskey** - Smoother, very close taste
- **Scotch** - Different character but interesting twist"
```

### 3. UnlockCalculatorTool (Bar Growth Advice)

**Current**: Returns ranked bottle recommendations
**Repurposed**: Personalized shopping advice

```python
# Input
{"cabinet": ["vodka", "gin"], "limit": 3}

# Output (conversational)
"Want to level up your bar? Here's my advice:
1. **Sweet Vermouth** - Unlocks 8 new drinks including Negroni and Manhattan
2. **Campari** - Opens up the whole bitter cocktail world
3. **Triple Sec** - Essential for Margaritas and Cosmos"
```

### 4. FlavorProfilerTool (Compare Flavors)

**Current**: Returns flavor profile data
**Repurposed**: Taste descriptions and comparisons

```python
# Input
{"cocktail_ids": ["margarita", "daiquiri"]}

# Output (conversational)
"Both are sour-forward classics! The **Margarita** has that tequila earthiness
with salt rim contrast, while **Daiquiri** is lighter, more rum-sweet.
If you like one, you'll probably enjoy the other, yaar!"
```

## Implementation Plan

### Phase 1: Tool Refactoring
1. Add `conversational_output` method to each tool
2. Keep existing `_run()` for backward compatibility
3. Add Raja personality to tool outputs

### Phase 2: Agent Integration
1. Update `create_raja_bartender()` to include tools
2. Modify tool descriptions for Raja's persona
3. Update agent backstory to mention tool capabilities

### Phase 3: Crew Updates
1. Simplify prompt injection (cabinet only, not full DB)
2. Let Raja use tools for dynamic lookups
3. Update task descriptions

### Phase 4: Testing
1. Unit tests for conversational tool outputs
2. Integration tests for Raja with tools
3. E2E chat flow tests

## Files to Modify

| File | Changes |
|------|---------|
| `src/app/tools/recipe_db.py` | Add `format_conversational()` method |
| `src/app/tools/substitution_finder.py` | Add conversational output |
| `src/app/tools/unlock_calculator.py` | Add conversational output |
| `src/app/tools/flavor_profiler.py` | Add conversational output |
| `src/app/agents/raja_bartender.py` | Wire tools to agent |
| `src/app/crews/raja_chat_crew.py` | Simplify prompt, rely on tools |
| `tests/tools/test_tools.py` | Add conversational output tests |
| `tests/agents/test_raja_bartender.py` | Add tool integration tests |

## Trade-offs

### Pros
- ✅ Smaller prompt context (less tokens per message)
- ✅ Dynamic data access (more natural conversation)
- ✅ Eliminates dead code (tools become useful)
- ✅ Cleaner architecture (single source of truth)
- ✅ More engaging UX ("Let me check..." feels natural)

### Cons
- ⚠️ More LLM calls (tool use adds round-trips)
- ⚠️ Slightly slower responses (tool execution time)
- ⚠️ Potential for tool errors mid-conversation

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Prompt size | ~4000 tokens | ~1000 tokens |
| Tool usage | 0% | 60%+ of conversations |
| Response relevance | Good | Improved (dynamic data) |
| Dead code | 4 files | 0 files |

## Rollback Plan

If tool-based approach causes issues:
1. Keep tools wired but add `use_tools=False` flag
2. Fall back to prompt injection mode
3. Monitor and iterate

## Next Steps

1. Create branch `feat/raja-tools-integration`
2. Implement in parallel subagents
3. Test with real conversations
4. Merge and deploy
