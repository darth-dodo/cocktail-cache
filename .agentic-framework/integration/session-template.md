# Session Log Template

**Project**: [PROJECT_NAME]
**Date**: [YYYY-MM-DD]
**Session**: [SESSION_NUMBER or SESSION_IDENTIFIER]

---

## Session Context

📋 **CURRENT STATUS** - [TIME]
├── 🎯 **Active Persona**: [Architect|Developer|Writer|QA|Custom]
├── 🔧 **MCP Servers**: [Context7|Sequential|Playwright|Magic|Serena|None]
├── 📝 **Current Task**: [Brief task description]
├── ⏰ **Time Budget**: [Estimated duration]
└── 🚦 **Status**: [Planning|In Progress|Blocked|Completed]

---

## Persona Quick Reference

| Emoji | Persona   | Use When                              | MCP Primary |
| ----- | --------- | ------------------------------------- | ----------- |
| 🏗️    | Architect | System design, architecture decisions | Sequential  |
| 💻    | Developer | Implementation, coding, debugging     | Context7    |
| 📝    | Writer    | Documentation, content, guides        | Context7    |
| ✅    | QA        | Testing, validation, quality gates    | Playwright  |

**Switch Persona**: Update "Active Persona" above and reference persona config in `.agentic/personas/`

---

## Workflow Progress

**Current Workflow**: [feature-development|content-creation|bug-fix|custom]

### Phase Tracking

- [ ] **Phase 1**: [PHASE_NAME] - [Persona] - [Duration]
  - Status: [Not Started|In Progress|Completed]
  - Notes: [Key decisions or blockers]

- [ ] **Phase 2**: [PHASE_NAME] - [Persona] - [Duration]
  - Status: [Not Started|In Progress|Completed]
  - Notes: [Key decisions or blockers]

- [ ] **Phase 3**: [PHASE_NAME] - [Persona] - [Duration]
  - Status: [Not Started|In Progress|Completed]
  - Notes: [Key decisions or blockers]

---

## Task Tracking

### Active Tasks

**Task 1**: [TASK_DESCRIPTION]

- Status: 🔄 In Progress
- Owner: [Persona]
- MCP: [Server if applicable]
- Time: [Actual time spent]
- Outcome: [Result or "In progress"]

**Task 2**: [TASK_DESCRIPTION]

- Status: ⏳ Pending
- Owner: [Persona]
- Dependencies: [Task IDs or "None"]

### Completed Tasks

- ✅ [TASK_DESCRIPTION] - [Persona] - [Duration]
- ✅ [TASK_DESCRIPTION] - [Persona] - [Duration]

### Blocked Tasks

- 🚫 [TASK_DESCRIPTION] - **Blocker**: [Reason]

---

## Quality Gate Status

**Target**: 8/8 gates passed before completion

| Gate             | Status     | Notes               |
| ---------------- | ---------- | ------------------- |
| 1. Syntax        | ⏳ Pending | [Command or result] |
| 2. Types         | ⏳ Pending | [Command or result] |
| 3. Lint          | ⏳ Pending | [Command or result] |
| 4. Security      | ⏳ Pending | [Command or result] |
| 5. Tests         | ⏳ Pending | Coverage: [X%]      |
| 6. Performance   | ⏳ Pending | [Metrics or "N/A"]  |
| 7. Accessibility | ⏳ Pending | [Score or "N/A"]    |
| 8. Integration   | ⏳ Pending | [Build status]      |

**Legend**: ✅ Passed | ❌ Failed | ⚠️ Warning | ⏳ Pending | ➖ N/A

---

## Decisions Made

**Decision 1**: [DECISION_TITLE]

- Context: [Why this decision was needed]
- Choice: [What was decided]
- Rationale: [Reasoning]
- ADR: [Link to ADR or "None"]

**Decision 2**: [DECISION_TITLE]

- Context: [Why this decision was needed]
- Choice: [What was decided]
- Rationale: [Reasoning]

---

## Session Timeline

**[HH:MM]** - Session start - [Persona]

- [Activity description]

**[HH:MM]** - [EVENT or MILESTONE]

- [Details]

**[HH:MM]** - Persona switch: [From] → [To]

- Reason: [Why the switch occurred]

**[HH:MM]** - [EVENT or MILESTONE]

- [Details]

**[HH:MM]** - Session checkpoint

- Context saved: `/sc:save`
- Progress: [X% complete]

**[HH:MM]** - Session end

- Final status: [Completed|Partial|Blocked]

---

## Blockers and Risks

### Active Blockers

**Blocker 1**: [ISSUE_DESCRIPTION]

- Severity: [Critical|High|Medium|Low]
- Impact: [What is affected]
- Resolution: [Next steps or "TBD"]

### Risks Identified

**Risk 1**: [RISK_DESCRIPTION]

- Probability: [High|Medium|Low]
- Impact: [Consequence if occurs]
- Mitigation: [Plan to address]

---

## Handoff Notes

**Next Session Preparation**

- **Resume Point**: [Where to pick up]
- **Required Persona**: [Recommended persona for next phase]
- **Context Files**: [Files or docs to review]
- **Pending Actions**: [What needs to happen next]

**To Next Agent/Persona**

- **Summary**: [Brief overview of current state]
- **Key Artifacts**: [Files, ADRs, docs created]
- **Open Questions**: [Unresolved items]
- **Quality Status**: [Current gate progress]

**Context Preservation**

- Saved: `/sc:save` at [TIME]
- Load command: `/sc:load`
- Session ID: [IDENTIFIER]

---

## Artifacts Created

### Files Modified

- `[FILE_PATH]` - [Description of changes]
- `[FILE_PATH]` - [Description of changes]

### Files Created

- `[FILE_PATH]` - [Purpose]
- `[FILE_PATH]` - [Purpose]

### Documentation

- [ADR-XXX: TITLE] - [Location]
- [Design doc: TITLE] - [Location]
- [Other documentation] - [Location]

---

## Session Metrics

- **Duration**: [Total time]
- **Personas Used**: [List]
- **MCP Calls**: [Number and types]
- **Quality Gates**: [X/8 passed]
- **Tasks Completed**: [X/Y]
- **Efficiency**: [On track|Ahead|Behind]

---

## Notes and Observations

### What Went Well

- [Positive observation]
- [Effective technique]

### Challenges

- [Challenge encountered]
- [How it was addressed or still open]

### Learning

- [Insight gained]
- [Process improvement for next session]

---

## Session Checklist

**Before Starting**

- [ ] Loaded project context: `/sc:load`
- [ ] Reviewed previous session log
- [ ] Selected appropriate persona
- [ ] Identified workflow pattern

**During Work**

- [ ] Updated task status in real-time
- [ ] Documented key decisions
- [ ] Ran quality gates at checkpoints
- [ ] Tracked time and progress

**Before Ending**

- [ ] Updated handoff notes
- [ ] Documented all artifacts
- [ ] Saved session context: `/sc:save`
- [ ] Final quality validation
- [ ] Prepared next session resume point

---

**Session Status**: [ACTIVE|PAUSED|COMPLETED]
**Last Updated**: [TIMESTAMP]
