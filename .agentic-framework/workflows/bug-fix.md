# Bug Fix Workflow

**Purpose**: Systematic workflow for investigating, fixing, and verifying bug resolutions.

**Duration**: 1-4 hours (depending on bug complexity)

**Agents**: Developer → Developer → QA

---

## Phase 1: Investigate (Developer Agent)

**Duration**: 30-90 minutes

**Objective**: Root cause analysis and fix strategy development.

### Tasks

- [ ] Reproduce the bug consistently
- [ ] Document reproduction steps
- [ ] Analyze error messages and stack traces
- [ ] Review recent code changes (git log)
- [ ] Identify affected components and modules
- [ ] Trace execution flow to pinpoint issue
- [ ] Review related test cases
- [ ] Determine root cause (not just symptoms)
- [ ] Assess impact and scope
- [ ] Develop fix strategy with alternatives
- [ ] Estimate fix complexity and risks
- [ ] Create investigation report

### Bug Report Template

```markdown
# Bug Investigation: [Brief Description]

**Bug ID**: [Tracking ID if applicable]
**Severity**: [Critical / High / Medium / Low]
**Priority**: [Urgent / High / Normal / Low]
**Reported**: [Date]
**Investigator**: Developer Agent

## Symptom Description

Brief description of the observed problem from user perspective.

## Reproduction Steps

1. Step 1
2. Step 2
3. Step 3
   **Result**: [What happens]
   **Expected**: [What should happen]

## Environment

- Version: [X.Y.Z]
- Platform: [OS, browser, etc.]
- Configuration: [Relevant settings]
- Data state: [Any special conditions]

## Analysis

### Stack Trace / Error Messages
```

[Paste relevant error output]

```

### Affected Components
- Component A: [How affected]
- Component B: [How affected]

### Code Inspection
- File: [path/to/file.ext]
- Function/Method: [name]
- Line: [X]
- Issue: [Description of problematic code]

### Root Cause
Detailed explanation of the underlying cause, not just symptoms.

**Why it happens**: [Technical explanation]
**When introduced**: [Commit or version if known]
**Related issues**: [Links to similar bugs]

## Impact Assessment

### User Impact
- Affected users: [All / Subset / Edge case]
- Frequency: [Always / Sometimes / Rare]
- Severity: [Blocks usage / Degrades experience / Minor annoyance]
- Workaround: [Available / None]

### Technical Impact
- Data integrity: [At risk / Safe]
- System stability: [Affected / Stable]
- Performance: [Degraded / Normal]
- Security: [Vulnerability / None]

## Fix Strategy

### Proposed Solution
Detailed description of the fix approach.

### Alternative Approaches
1. Alternative 1: [Pros and cons]
2. Alternative 2: [Pros and cons]

### Risks
- Risk 1: [Description and mitigation]
- Risk 2: [Description and mitigation]

### Dependencies
- [Any blocking issues or prerequisites]

### Testing Requirements
- Unit tests: [What to test]
- Integration tests: [What to test]
- Regression tests: [What to verify]
```

### Root Cause Analysis Framework

**5 Whys Technique**:

1. Why did the bug occur? [Answer 1]
   - Why [Answer 1]? [Answer 2]
     - Why [Answer 2]? [Answer 3]
       - Why [Answer 3]? [Answer 4]
         - Why [Answer 4]? [Root Cause]

**Categories to Investigate**:

- **Code Logic**: Incorrect algorithm or conditional
- **Data Handling**: Invalid data or state management
- **Integration**: API or module interaction issues
- **Configuration**: Environment or settings problems
- **Dependencies**: Third-party library issues
- **Timing**: Race conditions or async issues

### Session Log Update

```markdown
## Session [N]: Bug Investigation - [Brief Description]

**Agent**: Developer
**Duration**: [X] minutes
**Status**: Investigation Complete

### Completed

- Bug reproduced consistently
- Root cause identified
- Impact assessed: [severity]
- Fix strategy developed

### Root Cause

[One-sentence summary of underlying issue]

### Proposed Fix

[Brief description of fix approach]

### Risks

- [Risk 1]
- [Risk 2]

### Next Steps

- Begin Phase 2: Implementation
- Apply fix and create regression tests
```

### Quality Gate: Investigation Review

**Criteria**:

- [ ] Bug reliably reproducible
- [ ] Root cause identified (not symptoms)
- [ ] Impact fully assessed
- [ ] Fix strategy defined with alternatives
- [ ] Testing requirements specified
- [ ] Risks documented

**Exit Condition**: All criteria met, ready to implement fix.

---

## Phase 2: Fix (Developer Agent)

**Duration**: 30-120 minutes

**Objective**: Implement fix with regression tests following TDD approach.

### Tasks

- [ ] Create fix branch from main
- [ ] Write failing regression test (RED)
- [ ] Implement minimal fix (GREEN)
- [ ] Refactor for quality (REFACTOR)
- [ ] Add edge case tests
- [ ] Verify fix resolves original issue
- [ ] Test related functionality (regression)
- [ ] Update error messages if applicable
- [ ] Add defensive code if needed
- [ ] Update documentation if changed
- [ ] Run full test suite
- [ ] Perform self-code review

### TDD Regression Test Approach

**RED: Create Failing Test**

```markdown
1. Write test that reproduces the bug
2. Run test → should FAIL
3. Verify failure matches bug symptom
4. Commit: "test: add regression test for [bug]"
```

**GREEN: Fix the Bug**

```markdown
1. Implement minimal code to pass test
2. Run test → should PASS
3. Verify fix resolves original issue
4. Commit: "fix: [brief description]"
```

**REFACTOR: Improve Quality**

```markdown
1. Clean up implementation
2. Run tests → should still PASS
3. Check for code quality improvements
4. Commit: "refactor: improve [aspect]"
```

### Fix Implementation Checklist

**Code Changes**:

- [ ] Minimal change to fix root cause
- [ ] No unrelated modifications
- [ ] Handles edge cases identified
- [ ] Proper error handling added
- [ ] Input validation if applicable
- [ ] Null/undefined checks where needed

**Testing**:

- [ ] Regression test created
- [ ] Test reproduces original bug
- [ ] Test passes with fix applied
- [ ] Edge cases covered
- [ ] Related functionality tested
- [ ] Full test suite passing

**Quality**:

- [ ] Code follows project conventions
- [ ] No new linting errors
- [ ] No new type errors
- [ ] Comments explain "why" not "what"
- [ ] Error messages are helpful
- [ ] No console.log or debug code

### Fix Documentation Template

````markdown
# Bug Fix: [Brief Description]

**Bug ID**: [Tracking ID]
**Root Cause**: [One-sentence summary]

## Changes Made

### Files Modified

- `path/to/file1.ext`: [Description of changes]
- `path/to/file2.ext`: [Description of changes]

### Code Changes

**Before**:

```language
// Problematic code
```
````

**After**:

```language
// Fixed code
```

**Explanation**: [Why this fixes the root cause]

### Tests Added

- Regression test: [Description]
- Edge case tests: [List]

## Verification

- [x] Original bug no longer occurs
- [x] Regression test fails before fix, passes after
- [x] Related functionality still works
- [x] Full test suite passes

## Side Effects

- [Any other behavior changes]
- [Or "None identified"]

````

### Session Log Update
```markdown
## Session [N]: Bug Fix Implementation - [Brief Description]

**Agent**: Developer
**Duration**: [X] minutes
**Status**: Fix Complete

### Completed
- Regression test created (failing → passing)
- Root cause fix implemented
- Edge cases handled
- Full test suite passing
- Self-review performed

### Changes
- Files modified: [X]
- Lines changed: +[X] -[X]
- Tests added: [X]

### Verification
- [x] Original reproduction steps no longer trigger bug
- [x] Related features unaffected
- [x] No new issues introduced

### Next Steps
- Hand off to QA for validation
- Begin Phase 3: Verification
````

### Quality Gate: Fix Review

**Criteria**:

- [ ] Root cause addressed (not symptoms)
- [ ] Regression test created
- [ ] Test reproduces bug before fix
- [ ] Test passes with fix applied
- [ ] Full test suite passing
- [ ] No unrelated changes
- [ ] Code quality maintained
- [ ] Self-review completed

**Exit Condition**: All criteria met, fix ready for QA validation.

---

## Phase 3: Verify (QA Agent)

**Duration**: 20-60 minutes

**Objective**: Comprehensive validation that bug is fixed without regressions.

### Tasks

- [ ] Review fix implementation and approach
- [ ] Verify regression test quality
- [ ] Test original reproduction steps
- [ ] Test edge cases and variations
- [ ] Perform regression testing on related features
- [ ] Test in multiple environments (if applicable)
- [ ] Verify error messages and logging
- [ ] Check performance impact (if applicable)
- [ ] Review documentation updates
- [ ] Validate fix follows project conventions
- [ ] Create verification report
- [ ] Approve or request changes

### Verification Test Plan

**Bug Resolution**:

- [ ] Follow original reproduction steps → bug does not occur
- [ ] Test with same environment/data → bug does not occur
- [ ] Test variations of reproduction steps → bug does not occur
- [ ] Verify error messages improved (if applicable)

**Regression Testing**:

- [ ] Related Feature 1: Still works correctly
- [ ] Related Feature 2: Still works correctly
- [ ] Integration points: No new failures
- [ ] Existing tests: All still passing

**Edge Cases**:

- [ ] Boundary conditions handled
- [ ] Invalid input handled gracefully
- [ ] Null/undefined cases work
- [ ] Concurrent operations safe (if applicable)

**Quality Checks**:

- [ ] Regression test is comprehensive
- [ ] Code follows project standards
- [ ] No debugging code left behind
- [ ] Documentation updated if needed
- [ ] Performance not degraded

### Verification Report Template

```markdown
# Bug Fix Verification: [Brief Description]

**Bug ID**: [Tracking ID]
**Verifier**: QA Agent
**Date**: [Date]
**Status**: [Verified / Issues Found]

## Test Results

### Bug Resolution

**Original Reproduction**:

- [x] Step 1 → Works correctly
- [x] Step 2 → Works correctly
- [x] Step 3 → Works correctly
      **Result**: Bug no longer occurs ✅

**Variations Tested**:

1. Variation 1: [Result]
2. Variation 2: [Result]
3. Variation 3: [Result]

### Regression Testing

**Related Features**:

- Feature A: [Pass/Fail] - [Notes]
- Feature B: [Pass/Fail] - [Notes]
- Feature C: [Pass/Fail] - [Notes]

**Integration Points**:

- Integration 1: [Pass/Fail]
- Integration 2: [Pass/Fail]

### Test Suite

- Unit tests: [X/X] passing
- Integration tests: [X/X] passing
- Regression test: [Pass/Fail]

## Quality Assessment

### Regression Test Quality

- [x] Reproduces original bug
- [x] Fails without fix
- [x] Passes with fix
- [x] Covers edge cases
- [x] Will prevent future regressions

### Code Quality

- Fix approach: [Excellent / Good / Acceptable / Concerns]
- Code clarity: [Excellent / Good / Acceptable / Concerns]
- Follows conventions: [Yes / No - details]

## Issues Found

### Blocking Issues (Must Fix)

- [Issue 1: Description]

### Minor Issues (Should Fix)

- [Issue 1: Description]

### Observations (FYI)

- [Observation 1]

## Performance Impact

- Load time: [No change / +X% / -X%]
- Memory usage: [No change / +X% / -X%]
- Response time: [No change / +X% / -X%]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Decision

**[Verified and Approved / Request Changes]**

[If changes requested, list required fixes]
```

### Session Log Update

```markdown
## Session [N]: Bug Fix Verification - [Brief Description]

**Agent**: QA
**Duration**: [X] minutes
**Status**: [Verified / Issues Found]

### Test Results

- Original bug: [Resolved / Still occurs]
- Regression tests: [X/X] passing
- Related features: [No issues / Issues found]
- Edge cases: [All handled / Gaps found]

### Quality Assessment

- Regression test: [Excellent / Good / Needs improvement]
- Fix approach: [Optimal / Acceptable / Concerns]
- Code quality: [Meets standards / Issues]

### Issues Found

- Blocking: [X]
- Minor: [X]

### Decision

[Verified and approved / Request changes: list required fixes]
```

### Quality Gate: Final Verification

**Criteria**:

- [ ] Original bug completely resolved
- [ ] No regressions in related features
- [ ] Regression test comprehensive
- [ ] All test suites passing
- [ ] Code quality acceptable
- [ ] No performance degradation
- [ ] Documentation updated if needed

**Exit Condition**: All criteria met, fix verified for merge.

---

## Workflow Completion

### Merge Checklist

- [ ] All three phases completed successfully
- [ ] All quality gates passed
- [ ] QA verification approved
- [ ] Regression test included
- [ ] Git branch up-to-date with main
- [ ] Commit messages descriptive
- [ ] Pull request created with bug context
- [ ] CI/CD pipeline passing
- [ ] Bug tracking system updated

### Final Session Log

```markdown
## Bug Fix Complete: [Brief Description]

**Bug ID**: [Tracking ID]
**Total Duration**: [X] hours
**Phases**: Investigate → Fix → Verify
**Status**: Verified and Ready for Merge

### Summary

- Root cause: [Brief description]
- Fix approach: [Brief description]
- Regression test: [Added / Enhanced existing]

### Metrics

- Files changed: [X]
- Lines changed: +[X] -[X]
- Tests added: [X]
- Time to resolution: [X] hours

### Impact

- User impact: [Eliminated / Reduced]
- Regression risk: [Low / Medium / High]
- Performance: [Improved / No change / Acceptable degradation]

### Lessons Learned

- [Key insight 1]
- [Key insight 2]
```

---

## Bug Severity Guidelines

### Critical

- System crashes or data loss
- Security vulnerabilities
- Complete feature failure
- **Response**: Immediate fix, hot-fix deployment

### High

- Major feature broken
- Significant user impact
- No reasonable workaround
- **Response**: Fix within 24 hours

### Medium

- Feature partially broken
- Moderate user impact
- Workaround available
- **Response**: Fix in next release

### Low

- Minor inconvenience
- Cosmetic issues
- Rare edge cases
- **Response**: Fix when convenient

---

## Best Practices

### Investigation

- **Reproduce First**: Never start fixing without reproducing
- **Document Everything**: Capture all investigation details
- **Ask Why**: Use 5 Whys to find root cause
- **Check History**: Review recent changes with git log
- **Test Assumptions**: Verify what you think you know

### Implementation

- **Minimal Changes**: Fix only what's needed
- **Test-First**: Write failing test before fix
- **Defensive Code**: Add validation and error handling
- **Clear Commits**: Separate test, fix, and refactor commits
- **No Scope Creep**: Don't fix unrelated issues

### Verification

- **Follow Original Steps**: Use exact reproduction steps
- **Test Variations**: Try different data, environments
- **Regression Focus**: Ensure no new breakage
- **Performance Check**: Measure any impact
- **Future Prevention**: Ensure regression test is robust

### Communication

- **Clear Bug Reports**: Detailed reproduction steps
- **Explain Root Cause**: Help others learn
- **Document Decisions**: Why this approach over alternatives
- **Update Tracking**: Keep bug system current
- **Share Knowledge**: Document lessons learned

### Prevention

- **Add Regression Tests**: Prevent bug from returning
- **Review Related Code**: Find similar issues
- **Update Guidelines**: Prevent similar bugs
- **Tool Improvements**: Better linting, type checking
- **Knowledge Sharing**: Team learning from bugs
