# Feature Development Workflow

**Purpose**: Structured workflow for developing new features with design-first approach and quality gates.

**Duration**: 2-6 hours (depending on complexity)

**Agents**: Architect → Developer → QA

---

## Phase 1: Design (Architect Agent)

**Duration**: 30-60 minutes

**Objective**: Create comprehensive technical design and implementation plan.

### Tasks

- [ ] Analyze feature requirements and user stories
- [ ] Define acceptance criteria and success metrics
- [ ] Design system architecture and component structure
- [ ] Identify dependencies and integration points
- [ ] Document data models and interfaces
- [ ] Plan API contracts and communication patterns
- [ ] Assess technical risks and mitigation strategies
- [ ] Create implementation task breakdown
- [ ] Estimate complexity and resource requirements
- [ ] Review design with stakeholders (if applicable)

### Outputs

**Design Document** (`docs/design/FEATURE-NAME.md`):

````markdown
# Feature: [Name]

## Overview

Brief description and business value

## Requirements

- Functional requirement 1
- Functional requirement 2
- Non-functional requirements (performance, security, etc.)

## Architecture

### Components

- Component A: Responsibility and interfaces
- Component B: Responsibility and interfaces

### Data Models

```language
interface/class definitions
```
````

### API Contracts

Endpoints, methods, request/response formats

## Dependencies

- External libraries or services
- Internal modules or components

## Implementation Plan

1. Task 1 (estimate: Xh)
2. Task 2 (estimate: Xh)

## Risks & Mitigations

- Risk 1 → Mitigation strategy
- Risk 2 → Mitigation strategy

## Testing Strategy

- Unit test coverage targets
- Integration test scenarios
- E2E test critical paths

````

### Session Log Update
```markdown
## Session [N]: Feature Design - [Feature Name]

**Agent**: Architect
**Duration**: [X] minutes
**Status**: Design Complete

### Completed
- Technical design document created
- Architecture and interfaces defined
- Implementation plan with [X] tasks
- Risk assessment completed

### Decisions
- [Key architectural decision 1]
- [Key architectural decision 2]

### Next Steps
- Hand off to Developer for implementation
- Begin Phase 2: Implementation
````

### Quality Gate: Design Review

**Criteria**:

- [ ] Requirements clearly defined with acceptance criteria
- [ ] Architecture supports scalability and maintainability
- [ ] Data models and interfaces documented
- [ ] Implementation tasks broken into <4h chunks
- [ ] Risks identified with mitigation plans
- [ ] Testing strategy defined

**Exit Condition**: All criteria met, design approved.

---

## Phase 2: Implementation (Developer Agent)

**Duration**: 1-4 hours

**Objective**: Implement feature following TDD/BDD approach with quality gates.

### Tasks

- [ ] Set up development environment and dependencies
- [ ] Create feature branch from main
- [ ] Implement data models and interfaces
- [ ] Write failing tests (RED phase)
- [ ] Implement minimal code to pass tests (GREEN phase)
- [ ] Refactor for quality and maintainability (REFACTOR phase)
- [ ] Add integration tests for component interactions
- [ ] Implement error handling and edge cases
- [ ] Add logging and monitoring hooks
- [ ] Update relevant documentation
- [ ] Run full test suite
- [ ] Perform self-code review

### BDD Test-Driven Approach

**Red Phase**:

1. Write test describing expected behavior
2. Run test (should fail)
3. Verify failure message is correct

**Green Phase**:

1. Write minimal code to make test pass
2. Run test (should pass)
3. Verify implementation meets requirement

**Refactor Phase**:

1. Improve code quality without changing behavior
2. Run tests (should still pass)
3. Check for code smells and patterns

### Code Quality Checklist

- [ ] No hardcoded values (use configuration)
- [ ] Error handling for all failure scenarios
- [ ] Input validation and sanitization
- [ ] Consistent naming conventions
- [ ] Modular and reusable components
- [ ] No code duplication (DRY principle)
- [ ] Comments only for complex logic
- [ ] Accessibility considerations (if UI)
- [ ] Performance optimizations where needed
- [ ] Security best practices followed

### Session Log Update

```markdown
## Session [N]: Feature Implementation - [Feature Name]

**Agent**: Developer
**Duration**: [X] hours
**Status**: Implementation Complete

### Completed

- [x] components implemented
- [x] unit tests written (coverage: X%)
- [x] integration tests added
- All tests passing
- Code review self-performed

### Technical Details

- Files modified: [list]
- New dependencies: [list or "none"]
- Known limitations: [list or "none"]

### Next Steps

- Hand off to QA for validation
- Begin Phase 3: Validation
```

### Quality Gate: Implementation Review

**Criteria**:

- [ ] All planned functionality implemented
- [ ] Unit test coverage ≥80%
- [ ] Integration tests for critical paths
- [ ] All tests passing
- [ ] Code follows project conventions
- [ ] No linting or type errors
- [ ] Documentation updated
- [ ] Self-review completed

**Exit Condition**: All criteria met, code ready for QA.

---

## Phase 3: Validation (QA Agent)

**Duration**: 30-90 minutes

**Objective**: Comprehensive testing and quality validation before merge.

### Tasks

- [ ] Review implementation against design document
- [ ] Verify all acceptance criteria met
- [ ] Run full test suite (unit + integration)
- [ ] Perform manual exploratory testing
- [ ] Test edge cases and error scenarios
- [ ] Validate accessibility compliance (if UI)
- [ ] Check performance benchmarks
- [ ] Review security considerations
- [ ] Test cross-browser/platform compatibility (if applicable)
- [ ] Verify documentation accuracy and completeness
- [ ] Create test report with findings
- [ ] Approve or request changes

### Test Scenarios

**Functional Testing**:

- [ ] Happy path: Feature works as designed
- [ ] Edge cases: Boundary conditions handled
- [ ] Error scenarios: Failures handled gracefully
- [ ] Integration: Works with existing features

**Non-Functional Testing**:

- [ ] Performance: Meets response time requirements
- [ ] Security: No vulnerabilities introduced
- [ ] Accessibility: WCAG compliance (if UI)
- [ ] Usability: Intuitive and user-friendly (if UI)

### Session Log Update

```markdown
## Session [N]: Feature Validation - [Feature Name]

**Agent**: QA
**Duration**: [X] minutes
**Status**: [Approved / Changes Requested]

### Test Results

- Unit tests: [X/X] passing
- Integration tests: [X/X] passing
- Manual testing: [Pass/Fail]
- Performance: [Within/Outside] benchmarks

### Issues Found

- [Issue 1: severity, description]
- [Issue 2: severity, description]

### Recommendations

- [Recommendation 1]
- [Recommendation 2]

### Decision

[Approved for merge / Request changes: list required fixes]
```

### Quality Gate: Final Validation

**Criteria**:

- [ ] All acceptance criteria verified
- [ ] Test suite passing (100%)
- [ ] No critical or high-severity issues
- [ ] Performance within acceptable range
- [ ] Security review passed
- [ ] Documentation accurate and complete
- [ ] Ready for production deployment

**Exit Condition**: All criteria met, feature approved for merge.

---

## Workflow Completion

### Merge Checklist

- [ ] All three phases completed successfully
- [ ] All quality gates passed
- [ ] Git branch up-to-date with main
- [ ] Commit messages follow conventions
- [ ] Pull request created with description
- [ ] CI/CD pipeline passing
- [ ] Code review requested (if required)

### Final Session Log

```markdown
## Feature Development Complete: [Feature Name]

**Total Duration**: [X] hours
**Phases**: Design → Implementation → Validation
**Status**: Ready for Merge

### Summary

- Design: [Brief summary of architecture]
- Implementation: [Brief summary of changes]
- Validation: [Test results summary]

### Metrics

- Files changed: [X]
- Lines of code: +[X] -[X]
- Test coverage: [X]%
- Performance impact: [measurement]

### Deployment Notes

- Dependencies: [list or "none"]
- Configuration changes: [list or "none"]
- Migration required: [yes/no]
```

---

## Best Practices

### Communication Between Agents

- **Architect → Developer**: Clear design document with implementation guidance
- **Developer → QA**: Detailed change description and testing instructions
- **QA → Developer**: Specific, actionable feedback on issues

### Version Control

- Branch naming: `feature/descriptive-name`
- Commit messages: Conventional format (`feat:`, `fix:`, etc.)
- Frequent commits: Checkpoint progress regularly

### Documentation

- Update README if user-facing changes
- Add inline comments for complex logic only
- Keep design documents current with implementation
- Document breaking changes prominently

### Iteration

- If QA requests changes: Developer fixes → QA re-validates
- If design issues found during implementation: Architect revises → Developer adjusts
- Continuous feedback loop until quality gates pass
