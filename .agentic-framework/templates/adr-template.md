# ADR-[NUMBER]: [Architectural Decision Title]

**Date**: [YYYY-MM-DD]
**Status**: [Proposed|Accepted|Deprecated|Superseded]
**Context**: [Project phase, feature, or component]
**Decider(s)**: [Persona or team member]

---

## Summary

[One paragraph executive summary of the decision and its rationale]

---

## Problem Statement

### The Challenge

[Clear description of the architectural problem that needs to be solved]

### Why This Matters

[Impact and importance of making this decision now]

### Success Criteria

[What a successful solution must achieve]

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

---

## Context

### Current State

**Existing Architecture**:
[Description of current system or component architecture]

**Pain Points**:

- [Current limitation or issue]
- [Current limitation or issue]

**Technical Constraints**:

- [Technology limitation]
- [Resource constraint]
- [Time constraint]

### Requirements

**Functional Requirements**:

- [What the system must do]
- [What the system must do]

**Non-Functional Requirements**:

- **Performance**: [Targets]
- **Scalability**: [Growth expectations]
- **Maintainability**: [Developer experience goals]
- **Security**: [Security requirements]
- **Reliability**: [Uptime/availability targets]

**Stakeholder Concerns**:

- [User need or constraint]
- [Business requirement]
- [Team capability]

---

## Options Considered

### Option A: [OPTION_NAME]

**Description**:
[Detailed explanation of this approach]

**Implementation**:
[How this would be implemented]

**Pros**:

- [Advantage]
- [Advantage]

**Cons**:

- [Disadvantage]
- [Disadvantage]

**Risks**:

- [Risk and mitigation]

**Estimated Effort**: [Person-days or hours]

---

### Option B: [OPTION_NAME]

**Description**:
[Detailed explanation of this approach]

**Implementation**:
[How this would be implemented]

**Pros**:

- [Advantage]
- [Advantage]

**Cons**:

- [Disadvantage]
- [Disadvantage]

**Risks**:

- [Risk and mitigation]

**Estimated Effort**: [Person-days or hours]

---

### Option C: [OPTION_NAME]

**Description**:
[Detailed explanation of this approach]

**Implementation**:
[How this would be implemented]

**Pros**:

- [Advantage]
- [Advantage]

**Cons**:

- [Disadvantage]
- [Disadvantage]

**Risks**:

- [Risk and mitigation]

**Estimated Effort**: [Person-days or hours]

---

## Comparison Matrix

| Criteria                  | Weight | Option A | Option B | Option C |
| ------------------------- | ------ | -------- | -------- | -------- |
| **Maintainability**       | High   | [1-5]    | [1-5]    | [1-5]    |
| **Scalability**           | High   | [1-5]    | [1-5]    | [1-5]    |
| **Performance**           | Medium | [1-5]    | [1-5]    | [1-5]    |
| **Security**              | High   | [1-5]    | [1-5]    | [1-5]    |
| **Complexity**            | Medium | [1-5]    | [1-5]    | [1-5]    |
| **Implementation Effort** | Medium | [1-5]    | [1-5]    | [1-5]    |
| **Testing Difficulty**    | Low    | [1-5]    | [1-5]    | [1-5]    |
| **Documentation Needs**   | Low    | [1-5]    | [1-5]    | [1-5]    |
| **Total Score**           | -      | [SUM]    | [SUM]    | [SUM]    |

**Scoring**: 1 = Poor, 2 = Below Average, 3 = Acceptable, 4 = Good, 5 = Excellent
**Note**: For negative criteria (Complexity, Effort), higher score = lower complexity/effort

---

## Decision

### Chosen Option

**Selected**: [Option X: NAME]

**Rationale**:
[Detailed explanation of why this option was chosen over the alternatives]

**Key Factors**:

- [Factor that made this option best]
- [Factor that made this option best]
- [Factor that made this option best]

**Trade-offs Accepted**:
[What we're giving up by choosing this option]

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:

- [Benefit 1]
- [Benefit 2]

**Long-term Benefits**:

- [Benefit 1]
- [Benefit 2]

### Negative Outcomes

**Immediate Costs**:

- [Cost or limitation]
- [Cost or limitation]

**Technical Debt Created**:

- [Debt item with plan to address]

**Trade-offs**:

- [What we're sacrificing]
- [Limitation we're accepting]

### Risks and Mitigation

**Risk 1**: [RISK_DESCRIPTION]

- **Probability**: [High|Medium|Low]
- **Impact**: [Consequence if occurs]
- **Mitigation**: [How we'll address this]

**Risk 2**: [RISK_DESCRIPTION]

- **Probability**: [High|Medium|Low]
- **Impact**: [Consequence if occurs]
- **Mitigation**: [How we'll address this]

---

## Implementation Plan

### Phases

**Phase 1**: [PHASE_NAME]

- **Duration**: [Time estimate]
- **Tasks**:
  - [ ] [Task]
  - [ ] [Task]
- **Deliverable**: [What's produced]

**Phase 2**: [PHASE_NAME]

- **Duration**: [Time estimate]
- **Tasks**:
  - [ ] [Task]
  - [ ] [Task]
- **Deliverable**: [What's produced]

**Phase 3**: [PHASE_NAME]

- **Duration**: [Time estimate]
- **Tasks**:
  - [ ] [Task]
  - [ ] [Task]
- **Deliverable**: [What's produced]

### Dependencies

**Prerequisites**:

- [What must be done first]
- [What must be done first]

**Parallel Work**:

- [What can be done simultaneously]

**Blocked By**:

- [External dependencies or "None"]

### Rollback Plan

**Trigger Conditions**:
[Under what circumstances we would rollback]

**Rollback Steps**:

1. [Step to reverse changes]
2. [Step to reverse changes]

**Fallback Option**:
[Alternative approach if this fails]

---

## Validation

### Pre-Implementation Checklist

- [ ] Decision addresses the original problem
- [ ] Success criteria are achievable
- [ ] Risks are identified and mitigated
- [ ] Implementation plan is realistic
- [ ] Dependencies are understood
- [ ] Rollback plan exists

### Architect Quality Standards

- [ ] **Scalability**: Design accommodates expected growth (10x usage)
- [ ] **Maintainability**: Future developers can understand and modify
- [ ] **Best Practices**: Follows framework and community standards
- [ ] **Simplicity**: Simplest solution that meets requirements
- [ ] **Trade-offs**: Trade-offs are explicit and acceptable

### Post-Implementation Validation

**Success Metrics**:

- [Metric to measure]: Target [VALUE]
- [Metric to measure]: Target [VALUE]
- [Metric to measure]: Target [VALUE]

**Validation Tests**:

- [ ] [Test to confirm decision works as expected]
- [ ] [Test to confirm decision works as expected]

**Review Date**: [DATE]
[When we'll review if this decision is still appropriate]

---

## Related Decisions

**Supersedes**:

- [ADR-XXX: Title] - [Why this replaces that decision]

**Related To**:

- [ADR-XXX: Title] - [How they're connected]

**Depends On**:

- [ADR-XXX: Title] - [Prerequisite decision]

**Informs**:

- [Future decision area this will impact]

---

## References

### Documentation

- [Design document] - [Location]
- [Technical specification] - [Location]
- [API documentation] - [Location]

### External Resources

- [Article or blog post] - [URL]
- [Framework documentation] - [URL]
- [Community discussion] - [URL]

### Code References

- `[FILE_PATH]` - [Relevant implementation]
- `[FILE_PATH]` - [Related component]

---

## Discussion and Updates

### Decision History

**[YYYY-MM-DD]**: Proposed

- [Initial proposal details]

**[YYYY-MM-DD]**: Accepted

- [Final decision and any modifications]

**[YYYY-MM-DD]**: [Status change if applicable]

- [Reason for change]

### Questions Raised

**Q1**: [Question about the decision]

- **A**: [Answer or resolution]

**Q2**: [Question about the decision]

- **A**: [Answer or resolution]

### Feedback Incorporated

- [Feedback from team member] - [How it influenced decision]
- [Test results or prototype findings] - [Impact on decision]

---

## Metadata

**ADR Number**: [NUMBER]
**Created**: [YYYY-MM-DD]
**Last Updated**: [YYYY-MM-DD]
**Version**: [X.Y]

**Authors**: [Name or Persona]
**Reviewers**: [Name or Persona]

**Tags**: [architecture, performance, security, etc.]

**Project Phase**: [Inception|Development|Maintenance]

---

## Notes

[Additional context, observations, or considerations that don't fit elsewhere]

---

**Status**: [PROPOSED|ACCEPTED|DEPRECATED|SUPERSEDED]
**Next Review**: [DATE or "N/A"]
