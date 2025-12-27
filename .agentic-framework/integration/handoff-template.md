# Agent Handoff Documentation

**Project**: [PROJECT_NAME]
**Date**: [YYYY-MM-DD]
**Handoff ID**: [IDENTIFIER]

---

## Handoff Summary

**From**: [PERSONA_NAME] Persona
**To**: [PERSONA_NAME] Persona
**Transition**: [PHASE_FROM] → [PHASE_TO]
**Status**: [CLEAN_HANDOFF|WITH_BLOCKERS|INCOMPLETE]

---

## Context Transfer

### What Was Done

**Completed Work**:

- [Task or deliverable completed]
- [Task or deliverable completed]
- [Task or deliverable completed]

**Time Spent**: [Duration]

**Artifacts Created**:

- `[FILE_PATH]` - [Description]
- `[FILE_PATH]` - [Description]
- [Documentation reference] - [Location]

**Key Decisions**:

- [Decision made with rationale]
- [Decision made with rationale]

---

### What Needs to Happen Next

**Immediate Actions** (Priority: High):

1. [ACTION_ITEM] - [Expected duration]
2. [ACTION_ITEM] - [Expected duration]

**Follow-up Tasks** (Priority: Medium):

- [ ] [TASK_DESCRIPTION]
- [ ] [TASK_DESCRIPTION]

**Future Considerations** (Priority: Low):

- [Item for later phase]
- [Item for later phase]

---

### Blockers and Concerns

**Active Blockers**:

- **Blocker 1**: [DESCRIPTION]
  - Impact: [What is affected]
  - Status: [Unresolved|In Progress|Workaround Applied]
  - Resolution Path: [How to address]

**Concerns Raised**:

- **Concern 1**: [DESCRIPTION]
  - Type: [Technical|Process|Resource]
  - Severity: [Critical|High|Medium|Low]
  - Recommendation: [Suggested action]

---

### Quality Status

**Quality Gates Progress**: [X/8]

| Gate          | Status | Details |
| ------------- | ------ | ------- | --- | --- | ---------------- |
| Syntax        | [✅    | ❌      | ⏳  | ➖] | [Result or note] |
| Types         | [✅    | ❌      | ⏳  | ➖] | [Result or note] |
| Lint          | [✅    | ❌      | ⏳  | ➖] | [Result or note] |
| Security      | [✅    | ❌      | ⏳  | ➖] | [Result or note] |
| Tests         | [✅    | ❌      | ⏳  | ➖] | Coverage: [X%]   |
| Performance   | [✅    | ❌      | ⏳  | ➖] | [Metrics]        |
| Accessibility | [✅    | ❌      | ⏳  | ➖] | [Score]          |
| Integration   | [✅    | ❌      | ⏳  | ➖] | [Status]         |

**Outstanding Quality Issues**:

- [Issue description and remediation needed]

---

### Context Files

**Essential Reading**:

- `[FILE_PATH]` - [Why it matters]
- `[FILE_PATH]` - [Why it matters]

**Related Documentation**:

- [ADR-XXX: TITLE] - [Relevance]
- [Design doc] - [Relevance]

**Session Log**: [Path to session log]

---

## Persona-Specific Handoffs

### Template: Architect → Developer

**From**: Architect | **To**: Developer
**Artifact**: [Design document or ADR reference]

**Architecture Summary**:
[1-2 sentences describing the system design]

**Key Design Decisions**:

- [Decision 1 with rationale]
- [Decision 2 with rationale]
- [Decision 3 with rationale]

**Implementation Guidance**:

- [Specific technical direction]
- [Patterns to follow]
- [Pitfalls to avoid]

**Quality Criteria for "Done"**:

- [ ] [Acceptance criterion]
- [ ] [Acceptance criterion]
- [ ] [Acceptance criterion]

**MCP Server Recommendations**:

- Primary: [Server name] for [use case]
- Secondary: [Server name] for [use case]

---

### Template: Developer → QA

**From**: Developer | **To**: QA
**Artifact**: [Implementation reference]

**Implementation Summary**:
[1-2 sentences describing what was built]

**Changes Made**:

- **Files Modified**: [List]
- **Files Added**: [List]
- **Dependencies Changed**: [List or "None"]

**Testing Priorities**:

1. [Critical path or feature to validate]
2. [Edge cases to consider]
3. [Integration points to verify]

**Known Issues**:

- [Issue with workaround or plan]

**Quality Gates Passed**:

- ✅ Syntax, Types, Lint
- ⏳ Tests (coverage at [X%], needs improvement)
- ⏳ Security (needs audit)

**Test Coverage Gaps**:

- [Area needing test coverage]
- [Scenario not yet tested]

**MCP Server Recommendations**:

- Primary: Playwright for [E2E scenarios]
- Secondary: Sequential for [test strategy]

---

### Template: Developer → Developer (Parallel Work)

**From**: Developer Agent [X] | **To**: Developer Agent [Y]
**Coordination**: [Parallel|Sequential]

**Work Completed by Agent [X]**:

- [Component or feature completed]
- [Files modified]

**Integration Points**:

- **Shared Interface**: `[FILE_PATH]` - [Description]
- **API Contract**: [Specification]
- **Data Flow**: [How components interact]

**Merge Coordination**:

- Branch: [BRANCH_NAME]
- Conflicts Expected: [Yes/No - Details]
- Integration Testing: [Strategy]

**Quality Status**:

- Tests: [Status and coverage]
- Lint: [Status]

---

### Template: Writer → Developer

**From**: Writer | **To**: Developer
**Artifact**: [Documentation reference]

**Documentation Created**:

- [Document name and location]
- [Purpose and audience]

**Technical Gaps Identified**:

- [Feature needing implementation for doc accuracy]
- [API endpoint documented but not yet built]

**Code Examples Needed**:

- [Example scenario requiring real code]
- [Integration example needing validation]

**Validation Requests**:

- [ ] Verify technical accuracy of [SECTION]
- [ ] Review code examples in [SECTION]
- [ ] Confirm API signatures match documentation

---

### Template: QA → Architect

**From**: QA | **To**: Architect
**Artifact**: [Test results or quality report]

**Quality Assessment**:

- Overall Quality: [Excellent|Good|Needs Improvement|Poor]
- Quality Gates: [X/8 passed]

**Issues Found**:

- **Critical**: [List]
- **High**: [List]
- **Medium**: [List]

**Architecture Concerns**:

- [Systemic issue requiring design review]
- [Scalability or maintainability concern]

**Recommendations**:

- [Suggested architectural improvement]
- [Pattern or refactor recommendation]

**Risk Assessment**:

- [Risk description and mitigation needed]

---

### Template: QA → Developer

**From**: QA | **To**: Developer
**Artifact**: [Test report or bug list]

**Validation Results**:

- **Passed**: [Features or criteria that passed]
- **Failed**: [Features or criteria that failed]

**Bugs Found**:

1. **[BUG_TITLE]**
   - Severity: [Critical|High|Medium|Low]
   - Location: `[FILE:LINE]`
   - Reproduction: [Steps]
   - Expected vs Actual: [Description]

**Regression Issues**:

- [Previously working feature now broken]

**Quality Gate Failures**:

- [Gate name]: [Reason for failure]
- [Remediation required]

**Approval Status**:

- **Ready for Production**: [Yes|No|Conditional]
- **Conditions**: [Requirements if conditional]

---

### Template: Architect → Architect (Review)

**From**: Design Architect | **To**: Review Architect
**Artifact**: [Design document or ADR]

**Design Proposal**:
[Brief summary of architectural design]

**Review Focus**:

- [ ] Scalability assessment
- [ ] Maintainability review
- [ ] Security considerations
- [ ] Performance implications
- [ ] Alternative approaches

**Specific Questions**:

1. [Question about design choice]
2. [Question about trade-off]

**Risk Areas**:

- [Area needing particular scrutiny]

---

### Template: Multi-Agent Coordinator → Agents

**From**: Coordinator | **To**: [Agent 1, Agent 2, Agent 3, ...]
**Pattern**: [Parallel|Sequential|Hierarchical]

**Overall Objective**:
[High-level goal for multi-agent collaboration]

**Agent Assignments**:

- **Agent 1 ([Persona])**: [Responsibility]
  - Deliverables: [Expected output]
  - Dependencies: [What's needed from others]

- **Agent 2 ([Persona])**: [Responsibility]
  - Deliverables: [Expected output]
  - Dependencies: [What's needed from others]

**Coordination Points**:

- **Checkpoint 1** ([TIME]): [What to synchronize]
- **Checkpoint 2** ([TIME]): [What to synchronize]

**Integration Strategy**:

- [How agent outputs will be merged]

**Communication Protocol**:

- Updates: [Frequency and method]
- Blockers: [How to escalate]

---

### Template: Agents → Coordinator (Merge)

**From**: [Agent 1, Agent 2, Agent 3, ...] | **To**: Coordinator

**Completion Status**:

- Agent 1: [✅ Complete|⏳ In Progress|🚫 Blocked]
- Agent 2: [✅ Complete|⏳ In Progress|🚫 Blocked]
- Agent 3: [✅ Complete|⏳ In Progress|🚫 Blocked]

**Deliverables**:

- **Agent 1**: [Artifact location]
- **Agent 2**: [Artifact location]
- **Agent 3**: [Artifact location]

**Integration Notes**:

- **Conflicts**: [Any conflicts found]
- **Dependencies**: [How components interact]
- **Quality**: [Individual quality status]

**Merge Readiness**: [Ready|Needs Work|Blocked]

**Final Validation Needed**:

- [ ] [Integration test]
- [ ] [System-level validation]

---

## Handoff Checklist

**Outgoing Persona Responsibilities**:

- [ ] Documented all completed work
- [ ] Listed all artifacts with locations
- [ ] Identified blockers and concerns
- [ ] Updated quality gate status
- [ ] Saved session context: `/sc:save`
- [ ] Provided clear next actions
- [ ] Included relevant file references

**Incoming Persona Responsibilities**:

- [ ] Load session context: `/sc:load`
- [ ] Review all handoff documentation
- [ ] Read essential context files
- [ ] Understand quality status
- [ ] Acknowledge blockers
- [ ] Confirm acceptance of handoff
- [ ] Begin with appropriate persona configuration

---

## Metadata

**Session References**:

- Previous session: [SESSION_ID or log path]
- Current session: [SESSION_ID or log path]

**Time Tracking**:

- Handoff time: [TIMESTAMP]
- Expected next phase duration: [ESTIMATE]

**Context Preservation**:

- Saved state: [LOCATION]
- Load command: `/sc:load`

---

**Handoff Status**: [PENDING|ACCEPTED|IN_PROGRESS|COMPLETED]
**Last Updated**: [TIMESTAMP]
