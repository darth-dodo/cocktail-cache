# Design Document: Parallel Crew Execution

**Author:** Claude Code
**Date:** 2025-12-27
**Status:** Draft
**Branch:** feat/parallel-crew-execution

---

## 1. Problem Statement

The current CocktailFlow executes crews **strictly sequentially**, resulting in unnecessary latency. When bottle advice is enabled, the Recipe Writer and Bottle Advisor tasks run one after another, even though the Bottle Advisor does not depend on the Recipe Writer's output.

**Current Latency (with bottle advice):**
- Fast mode: ~5-6 seconds
- Full mode: ~8-9 seconds

**Target Latency (with bottle advice):**
- Fast mode: ~3-4 seconds (40% reduction)
- Full mode: ~6-7 seconds (25% reduction)

---

## 2. Analysis Summary

### Current Sequential Flow

```
receive_input (0ms)
    │
    ▼
analyze (1.5-4s) ─── 1-2 LLM calls
    │
    ▼
generate_recipe ─┬─ Recipe Writer (1.5-2s) ─── 1 LLM call
                 │
                 └─ Bottle Advisor (1.5-2s) ─── 1 LLM call (WAITS for Recipe)
```

### Key Finding

The `context=[recipe_task]` dependency in `recipe_crew.py:148` is **artificial**.

The Bottle Advisor only needs:
- `cabinet` - Available from flow input
- `drink_type` - Available from flow input
- `UnlockCalculatorTool` - Deterministic data lookup, no LLM dependency

### Proposed Parallel Flow

```
receive_input (0ms)
    │
    ▼
analyze (1.5-4s) ─── 1-2 LLM calls
    │
    ├──────────────────┬───────────────────┐
    │                  │                   │
    ▼                  ▼                   │
Recipe Writer    Bottle Advisor           │  ← PARALLEL (asyncio.gather)
(1.5-2s)         (1.5-2s)                 │
    │                  │                   │
    └──────────────────┴───────────────────┘
                       │
                       ▼
                 merge_results (0ms)
```

---

## 3. Technical Design

### 3.1 New Crew Functions

Create two new single-task crew factories in `recipe_crew.py`:

```python
def create_recipe_only_crew() -> Crew:
    """Create a crew with only the Recipe Writer task."""
    recipe_tools = [RecipeDBTool(), SubstitutionFinderTool()]
    recipe_writer = create_recipe_writer(tools=recipe_tools)

    recipe_task = Task(
        description="...",  # Same as current
        agent=recipe_writer,
        output_pydantic=RecipeOutput,
    )

    return Crew(
        agents=[recipe_writer],
        tasks=[recipe_task],
        process=Process.sequential,
        verbose=False,
    )


def create_bottle_only_crew() -> Crew:
    """Create a crew with only the Bottle Advisor task."""
    bottle_tools = [UnlockCalculatorTool()]
    bottle_advisor = create_bottle_advisor(tools=bottle_tools)

    bottle_task = Task(
        description="...",  # Modified to not reference recipe
        agent=bottle_advisor,
        output_pydantic=BottleAdvisorOutput,
        # NO context dependency
    )

    return Crew(
        agents=[bottle_advisor],
        tasks=[bottle_task],
        process=Process.sequential,
        verbose=False,
    )
```

### 3.2 Flow Changes

Update `cocktail_flow.py` to support parallel execution:

```python
from src.app.config import get_settings

class CocktailFlow(Flow[CocktailFlowState]):

    @listen(analyze)
    async def generate_recipe(self) -> CocktailFlowState:
        """Run Recipe Crew with optional parallel bottle advice."""
        if self.state.error or not self.state.selected:
            return self.state

        settings = get_settings()

        if settings.PARALLEL_CREWS and self.state.include_bottle_advice:
            # Parallel execution
            await self._generate_parallel()
        else:
            # Sequential execution (current behavior)
            await self._generate_sequential()

        return self.state

    async def _generate_parallel(self) -> None:
        """Run Recipe Writer and Bottle Advisor in parallel."""
        recipe_crew = create_recipe_only_crew()
        bottle_crew = create_bottle_only_crew()

        recipe_result, bottle_result = await asyncio.gather(
            recipe_crew.kickoff_async(inputs={
                "cocktail_id": self.state.selected,
                "skill_level": self.state.skill_level,
                "cabinet": self.state.cabinet,
                "drink_type": self.state.drink_type,
            }),
            bottle_crew.kickoff_async(inputs={
                "cabinet": self.state.cabinet,
                "drink_type": self.state.drink_type,
            }),
        )

        self._extract_and_store_results(recipe_result, bottle_result)

    async def _generate_sequential(self) -> None:
        """Run Recipe Crew sequentially (current behavior)."""
        # Existing implementation
        ...
```

### 3.3 Configuration

Add new setting to `config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Performance Settings
    PARALLEL_CREWS: bool = True  # Enable parallel Recipe + Bottle execution
```

---

## 4. Data Flow

### Inputs Required by Each Task

| Task | Required Inputs | Source |
|------|-----------------|--------|
| Recipe Writer | `cocktail_id`, `skill_level`, `cabinet`, `drink_type` | Flow state (from analysis) |
| Bottle Advisor | `cabinet`, `drink_type` | Flow state (from input) |

### Output Structure

Both tasks produce independent Pydantic models that are merged into the flow state:

```python
@dataclass
class ParallelResults:
    recipe: RecipeOutput | None
    bottle_advice: BottleAdvisorOutput | None
```

---

## 5. Error Handling

### Parallel Failure Modes

| Scenario | Handling |
|----------|----------|
| Recipe fails, Bottle succeeds | Return error, discard bottle result |
| Recipe succeeds, Bottle fails | Return recipe, set empty bottle advice |
| Both fail | Return first error |
| Timeout on either | Use `asyncio.wait_for()` with 30s timeout |

### Implementation

```python
async def _generate_parallel(self) -> None:
    try:
        recipe_result, bottle_result = await asyncio.wait_for(
            asyncio.gather(
                recipe_crew.kickoff_async(...),
                bottle_crew.kickoff_async(...),
                return_exceptions=True,  # Don't fail fast
            ),
            timeout=30.0,
        )

        # Handle individual failures
        if isinstance(recipe_result, Exception):
            self.state.error = f"Recipe generation failed: {recipe_result}"
            return

        if isinstance(bottle_result, Exception):
            logger.warning(f"Bottle advice failed: {bottle_result}")
            bottle_result = None  # Continue without bottle advice

        self._extract_and_store_results(recipe_result, bottle_result)

    except asyncio.TimeoutError:
        self.state.error = "Recipe generation timed out"
```

---

## 6. Testing Strategy

### Unit Tests

1. **test_parallel_crews_execute_concurrently**
   - Mock both crews
   - Verify they are called simultaneously (not sequentially)
   - Check timing overlap

2. **test_parallel_recipe_failure_handled**
   - Simulate recipe crew exception
   - Verify error propagates correctly
   - Verify bottle advice is discarded

3. **test_parallel_bottle_failure_handled**
   - Simulate bottle crew exception
   - Verify recipe is still returned
   - Verify empty bottle advice

4. **test_parallel_timeout_handled**
   - Simulate slow crew response
   - Verify timeout triggers error

### Integration Tests

1. **test_e2e_parallel_vs_sequential_timing**
   - Run same request with `PARALLEL_CREWS=true` and `false`
   - Verify parallel is faster

2. **test_parallel_results_match_sequential**
   - Compare outputs from both modes
   - Verify identical results

---

## 7. Rollback Plan

### Feature Flag

The `PARALLEL_CREWS` environment variable provides instant rollback:

```bash
# Disable parallel execution
export PARALLEL_CREWS=false
```

### Code Rollback

If issues are discovered post-deployment:

1. Set `PARALLEL_CREWS=false` immediately
2. Investigate logs for race conditions or state corruption
3. If needed, revert the entire branch

---

## 8. Performance Metrics

### Instrumentation Points

Add timing logs in flow:

```python
import time

async def generate_recipe(self) -> CocktailFlowState:
    start = time.perf_counter()

    if settings.PARALLEL_CREWS:
        await self._generate_parallel()
        mode = "parallel"
    else:
        await self._generate_sequential()
        mode = "sequential"

    elapsed = time.perf_counter() - start
    logger.info(f"Recipe generation ({mode}): {elapsed:.2f}s")
```

### Expected Results

| Mode | Metric | Expected |
|------|--------|----------|
| Sequential | Recipe step duration | 3-4s |
| Parallel | Recipe step duration | 1.5-2s |
| Parallel | Improvement | 40-50% |

---

## 9. Implementation Plan

### Phase 1: Create New Crew Functions (Low Risk)

1. Add `create_recipe_only_crew()` to `recipe_crew.py`
2. Add `create_bottle_only_crew()` to `recipe_crew.py`
3. Add unit tests for new functions

### Phase 2: Add Configuration (Low Risk)

1. Add `PARALLEL_CREWS` setting to `config.py`
2. Default to `True` for new behavior

### Phase 3: Update Flow (Moderate Risk)

1. Refactor `generate_recipe()` to support both modes
2. Add `_generate_parallel()` method
3. Add error handling and timeout logic

### Phase 4: Testing & Validation (Essential)

1. Run full test suite
2. Measure latency improvement
3. Validate no regressions

### Phase 5: Documentation

1. Update architecture.md
2. Update implementation-guide.md
3. Add performance tuning section

---

## 10. Alternatives Considered

### Alternative A: CrewAI Parallel Process

CrewAI has a `Process.parallel` mode, but it's designed for independent agents working on the same task, not multiple tasks with different outputs.

**Rejected:** Not suitable for our use case.

### Alternative B: Background Task for Bottle Advice

Run bottle advice as a fire-and-forget background task, return recipe immediately.

**Rejected:** Complicates API response model, requires polling or websockets.

### Alternative C: Pre-compute Bottle Advice

Cache bottle recommendations based on cabinet hash.

**Rejected:** Cache invalidation complexity, storage overhead.

---

## 11. Decision

**Approved Approach:** Parallel crew execution using `asyncio.gather()` with feature flag.

This provides:
- 40-50% latency reduction for recipe+bottle requests
- Easy rollback via feature flag
- Minimal code changes
- No breaking API changes

---

## Appendix: File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/app/config.py` | Add | `PARALLEL_CREWS` setting |
| `src/app/crews/recipe_crew.py` | Add | `create_recipe_only_crew()`, `create_bottle_only_crew()` |
| `src/app/flows/cocktail_flow.py` | Modify | Parallel execution support |
| `tests/crews/test_recipe_crew.py` | Add | Tests for new crew functions |
| `tests/flows/test_cocktail_flow.py` | Add | Tests for parallel execution |
| `docs/architecture.md` | Update | Document parallel execution |
