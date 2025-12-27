# Multi-Agent Coordination Workflow

**Purpose**: Patterns for coordinating multiple agents working in parallel, sequentially, or hierarchically.

**Duration**: Variable (depends on coordination pattern)

**Patterns**: Parallel | Sequential | Hierarchical

---

## Pattern 1: Parallel Coordination

**Use When**: Independent tasks that can be executed simultaneously without conflicts.

**Duration**: Time of longest task (not sum of all tasks)

**Agents**: 2-5 agents working concurrently

### Architecture

```
Orchestrator
    ├── Agent A (Task 1) ─┐
    ├── Agent B (Task 2) ─┼─→ Merge & Validate
    ├── Agent C (Task 3) ─┤
    └── Agent D (Task 4) ─┘
```

### Ideal Use Cases

- Multiple independent features
- Component library development
- Multi-service API development
- Documentation for different modules
- Testing different platforms/browsers
- Performance optimization of separate modules

### Setup Phase (Orchestrator)

**Duration**: 15-30 minutes

**Tasks**:

- [ ] Analyze overall work scope
- [ ] Identify independent task units
- [ ] Ensure tasks have no shared dependencies
- [ ] Create work breakdown structure
- [ ] Define success criteria for each task
- [ ] Establish merge strategy
- [ ] Set up git worktrees for parallel work
- [ ] Assign agents to tasks
- [ ] Create coordination document

### Git Worktree Setup

```bash
# Main repository
cd /project/main

# Create worktrees for parallel work
git worktree add ../agent-a-workspace feature/agent-a-task
git worktree add ../agent-b-workspace feature/agent-b-task
git worktree add ../agent-c-workspace feature/agent-c-task
git worktree add ../agent-d-workspace feature/agent-d-task

# Each agent works in their own workspace
# No merge conflicts during development
```

### Coordination Document Template

```markdown
# Parallel Coordination: [Project Name]

**Orchestrator**: [Name/ID]
**Start Time**: [Timestamp]
**Estimated Completion**: [Time]

## Overall Objective

[High-level goal that parallel work achieves]

## Task Breakdown

### Agent A - [Task Name]

- **Workspace**: `../agent-a-workspace`
- **Branch**: `feature/agent-a-task`
- **Objective**: [Specific goal]
- **Duration Estimate**: [X] hours
- **Dependencies**: [None / List]
- **Output**: [Deliverable description]
- **Status**: [Not Started / In Progress / Complete]

### Agent B - [Task Name]

- **Workspace**: `../agent-b-workspace`
- **Branch**: `feature/agent-b-task`
- **Objective**: [Specific goal]
- **Duration Estimate**: [X] hours
- **Dependencies**: [None / List]
- **Output**: [Deliverable description]
- **Status**: [Not Started / In Progress / Complete]

[Repeat for each agent]

## Shared Constraints

- Code style: [Reference]
- Testing requirements: [Standards]
- Documentation format: [Template]

## Merge Strategy

1. [Order of merging if applicable]
2. [Integration testing approach]
3. [Conflict resolution protocol]

## Communication Protocol

- Status updates: [Frequency]
- Issue escalation: [Process]
- Coordination check-ins: [Schedule]
```

### Execution Phase

**Each Agent Independently**:

1. Work in assigned worktree/workspace
2. Follow standard workflow (design/implement/test)
3. Commit regularly to feature branch
4. Update status in coordination document
5. Signal completion to orchestrator

**Agent Session Log** (Individual):

```markdown
## Session [N]: Parallel Task - [Agent ID] - [Task Name]

**Agent**: [A/B/C/D]
**Workspace**: [Path]
**Duration**: [X] hours
**Status**: [Complete / Blocked / In Progress]

### Completed

- [Deliverable description]
- [Files changed: X]
- [Tests added: X]

### Issues Encountered

- [Issue 1 and resolution]
- [Issue 2 and resolution]

### Ready for Merge

- [x] All tests passing
- [x] Code review self-performed
- [x] Documentation updated
- [x] Branch ready for integration
```

### Merge & Integration Phase (Orchestrator)

**Duration**: 30-90 minutes

**Tasks**:

- [ ] Verify all agents completed their tasks
- [ ] Review each agent's deliverables
- [ ] Merge branches in planned order
- [ ] Resolve any merge conflicts
- [ ] Run integration tests
- [ ] Validate combined functionality
- [ ] Check for unintended interactions
- [ ] Perform final quality check
- [ ] Create merge commit
- [ ] Clean up worktrees

### Merge Strategy

```bash
# Switch to main repository
cd /project/main

# Merge in planned order
git checkout main
git merge feature/agent-a-task
git merge feature/agent-b-task
git merge feature/agent-c-task
git merge feature/agent-d-task

# Run integration tests
[test command]

# Clean up worktrees
git worktree remove ../agent-a-workspace
git worktree remove ../agent-b-workspace
git worktree remove ../agent-c-workspace
git worktree remove ../agent-d-workspace
```

### Integration Validation Checklist

- [ ] All feature branches merged successfully
- [ ] No merge conflicts remaining
- [ ] Combined code compiles/runs
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] No unexpected interactions
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Ready for production

### Final Coordination Log

```markdown
# Parallel Coordination Complete: [Project Name]

**Total Duration**: [X] hours
**Agents**: [Count]
**Tasks Completed**: [Count]

## Task Summary

- Agent A: [Task] - [Duration] - ✅
- Agent B: [Task] - [Duration] - ✅
- Agent C: [Task] - [Duration] - ✅
- Agent D: [Task] - [Duration] - ✅

## Integration

- Merge conflicts: [X]
- Integration issues: [X]
- Combined test results: [Pass/Fail]

## Efficiency Gains

- Sequential time would be: [X] hours
- Parallel time actual: [X] hours
- Time saved: [X] hours ([X]%)

## Lessons Learned

- [Key insight 1]
- [Key insight 2]
```

---

## Pattern 2: Sequential Coordination

**Use When**: Tasks have dependencies and must be executed in specific order.

**Duration**: Sum of all task durations

**Agents**: 2-5 agents working in sequence

### Architecture

```
Orchestrator
    │
    ├─→ Agent A (Task 1)
    │       │
    │       ├─→ Agent B (Task 2)
    │       │       │
    │       │       ├─→ Agent C (Task 3)
    │       │       │       │
    │       │       │       └─→ Final Validation
```

### Ideal Use Cases

- Feature requiring multiple specializations
- Progressive refinement workflows
- Pipeline processing (design → implement → test)
- Dependent module development
- Multi-stage migrations
- Iterative improvement cycles

### Setup Phase (Orchestrator)

**Duration**: 15-30 minutes

**Tasks**:

- [ ] Map complete workflow
- [ ] Identify task dependencies
- [ ] Determine optimal sequence
- [ ] Define handoff criteria between stages
- [ ] Establish quality gates
- [ ] Create pipeline document
- [ ] Assign agents to stages
- [ ] Set up shared workspace

### Pipeline Document Template

```markdown
# Sequential Coordination: [Project Name]

**Orchestrator**: [Name/ID]
**Start Time**: [Timestamp]
**Estimated Completion**: [Sum of stages]

## Workflow Pipeline

### Stage 1: [Task Name]

- **Agent**: [Agent A]
- **Duration**: [X] hours
- **Input**: [Starting point]
- **Output**: [Deliverable]
- **Success Criteria**: [Checklist]
- **Handoff to**: Stage 2

### Stage 2: [Task Name]

- **Agent**: [Agent B]
- **Duration**: [X] hours
- **Input**: [Output from Stage 1]
- **Output**: [Deliverable]
- **Success Criteria**: [Checklist]
- **Handoff to**: Stage 3

[Repeat for each stage]

## Dependencies

- Stage 2 depends on: Stage 1 output
- Stage 3 depends on: Stage 2 output

## Quality Gates

- After Stage 1: [Validation criteria]
- After Stage 2: [Validation criteria]
- Final: [Overall validation]

## Rollback Strategy

If Stage N fails:

1. [Rollback procedure]
2. [Retry or escalate]
```

### Execution Pattern

**For Each Stage**:

1. Previous agent completes and signals ready
2. Orchestrator validates handoff criteria
3. Next agent receives context and begins
4. Agent executes their stage
5. Agent validates their output
6. Agent signals completion
7. Repeat until final stage

### Handoff Protocol

**Completing Agent**:

```markdown
## Stage [N] Complete - Handoff to Stage [N+1]

**Agent**: [ID]
**Stage**: [Name]
**Status**: Complete and Validated

### Deliverables

- [Deliverable 1]: [Location/description]
- [Deliverable 2]: [Location/description]

### Validation Results

- [x] Success criterion 1
- [x] Success criterion 2
- [x] All tests passing

### Context for Next Stage

- [Important note 1]
- [Important note 2]
- [Known issues or considerations]

### Handoff

Ready for Stage [N+1] - [Agent ID]
```

**Receiving Agent**:

```markdown
## Stage [N+1] Starting - Received from Stage [N]

**Agent**: [ID]
**Stage**: [Name]
**Status**: Starting

### Received

- [Deliverable 1]: Verified ✅
- [Deliverable 2]: Verified ✅

### Understanding

- [Confirmed understanding of context]
- [Confirmed understanding of requirements]

### Questions/Clarifications

- [Any questions for previous agent]
- [Or "None - ready to proceed"]

### Beginning Work

[Brief description of approach]
```

### Session Logs (Sequential)

```markdown
## Session [N]: Sequential Pipeline - Stage [X] - [Task Name]

**Agent**: [ID]
**Stage**: [X of Y]
**Duration**: [X] hours
**Status**: Complete

### Input Received

- From Stage [X-1]
- [Description of input]
- Validation: ✅

### Work Completed

- [Achievement 1]
- [Achievement 2]
- [Achievement 3]

### Output Delivered

- [Deliverable 1]
- [Deliverable 2]

### Handoff

- To Stage [X+1]
- Context provided: [Summary]
- Ready for next agent: ✅
```

---

## Pattern 3: Hierarchical Coordination

**Use When**: Complex work requiring orchestration across multiple levels and specializations.

**Duration**: Variable (parallel + sequential combination)

**Agents**: 3-10 agents in tree structure

### Architecture

```
Orchestrator (Level 0)
    │
    ├─→ Lead A (Level 1)
    │     ├─→ Worker A1 (Level 2)
    │     ├─→ Worker A2 (Level 2)
    │     └─→ Worker A3 (Level 2)
    │
    ├─→ Lead B (Level 1)
    │     ├─→ Worker B1 (Level 2)
    │     └─→ Worker B2 (Level 2)
    │
    └─→ Lead C (Level 1)
          ├─→ Worker C1 (Level 2)
          └─→ Worker C2 (Level 2)
```

### Ideal Use Cases

- Large-scale system development
- Multi-module applications
- Enterprise migrations
- Platform rebuilds
- Complex testing campaigns
- Organization-wide documentation

### Setup Phase (Orchestrator)

**Duration**: 30-60 minutes

**Tasks**:

- [ ] Decompose work into major domains
- [ ] Identify lead responsibilities
- [ ] Break domains into worker tasks
- [ ] Map dependencies across domains
- [ ] Define communication channels
- [ ] Establish reporting structure
- [ ] Create hierarchy document
- [ ] Assign leads and workers
- [ ] Set up workspace structure

### Hierarchy Document Template

```markdown
# Hierarchical Coordination: [Project Name]

**Orchestrator**: [Name/ID]
**Start Time**: [Timestamp]
**Total Agents**: [Count]

## Work Breakdown

### Domain A - [Name]

**Lead**: [Agent ID]
**Objective**: [High-level goal]

#### Workers under Lead A

- **Worker A1**: [Specific task]
  - Duration: [X] hours
  - Output: [Deliverable]

- **Worker A2**: [Specific task]
  - Duration: [X] hours
  - Output: [Deliverable]

- **Worker A3**: [Specific task]
  - Duration: [X] hours
  - Output: [Deliverable]

### Domain B - [Name]

**Lead**: [Agent ID]
**Objective**: [High-level goal]

[Repeat structure]

## Cross-Domain Dependencies

- Domain A → Domain B: [Dependency]
- Domain B → Domain C: [Dependency]

## Reporting Structure

- Workers report to: Lead
- Leads report to: Orchestrator
- Frequency: [Schedule]

## Integration Plan

1. Workers complete → Leads integrate
2. Leads complete → Orchestrator integrates
3. Final validation
```

### Lead Agent Responsibilities

**Domain Leadership**:

- [ ] Coordinate workers in domain
- [ ] Review worker deliverables
- [ ] Resolve domain-specific issues
- [ ] Integrate worker contributions
- [ ] Report status to orchestrator
- [ ] Manage domain timeline
- [ ] Ensure domain quality standards

**Lead Session Log**:

```markdown
## Session [N]: Domain Lead - [Domain Name]

**Lead**: [Agent ID]
**Domain**: [Name]
**Workers**: [Count]
**Status**: [In Progress / Complete]

### Worker Status

- Worker A1: [Status] - [Progress %]
- Worker A2: [Status] - [Progress %]
- Worker A3: [Status] - [Progress %]

### Domain Progress

- Overall completion: [X]%
- Blockers: [List or "None"]
- Integration status: [Status]

### Issues & Resolutions

- [Issue 1]: [Resolution]
- [Issue 2]: [Resolution]

### Report to Orchestrator

- On track: [Yes/No]
- ETA: [Timestamp]
- Support needed: [List or "None"]
```

### Worker Agent Responsibilities

**Task Execution**:

- [ ] Execute assigned task
- [ ] Follow domain standards
- [ ] Report to lead agent
- [ ] Coordinate with peer workers if needed
- [ ] Deliver to lead for integration

**Worker Session Log**:

```markdown
## Session [N]: Worker Task - [Task Name]

**Worker**: [Agent ID]
**Domain**: [Name]
**Lead**: [Agent ID]
**Status**: Complete

### Task Completed

- [Deliverable description]
- Duration: [X] hours
- Tests: [X] added, all passing

### Delivered to Lead

- Location: [Path or reference]
- Status: Ready for integration

### Notes

- [Any important context for lead]
```

### Integration Levels

**Level 2 → Level 1** (Workers to Lead):

1. Workers complete individual tasks
2. Lead reviews each worker's output
3. Lead integrates worker contributions
4. Lead validates domain functionality
5. Lead packages domain deliverable

**Level 1 → Level 0** (Leads to Orchestrator):

1. Leads complete domain integration
2. Orchestrator reviews domain deliverables
3. Orchestrator integrates domains
4. Orchestrator validates overall system
5. Orchestrator creates final deliverable

### Final Coordination Log

```markdown
# Hierarchical Coordination Complete: [Project Name]

**Total Duration**: [X] hours
**Total Agents**: [Count]
**Levels**: 3 (Orchestrator, Leads, Workers)

## Domain Summary

### Domain A - [Name]

- Lead: [Agent ID]
- Workers: [Count]
- Duration: [X] hours
- Status: ✅

### Domain B - [Name]

- Lead: [Agent ID]
- Workers: [Count]
- Duration: [X] hours
- Status: ✅

[Repeat for each domain]

## Integration Results

- Domain integrations: [X/X] successful
- Cross-domain tests: [Pass/Fail]
- Overall system validation: [Pass/Fail]

## Metrics

- Total work hours: [X] (if sequential)
- Actual duration: [X] (with parallelization)
- Efficiency gain: [X]%
- Issues resolved: [X]

## Lessons Learned

- [Key insight 1]
- [Key insight 2]
- [Improvement for next time]
```

---

## Best Practices: All Patterns

### Planning

- **Clear Boundaries**: Define task boundaries explicitly
- **Minimal Dependencies**: Reduce cross-task dependencies
- **Quality Gates**: Validate at each handoff/merge point
- **Communication Protocol**: Establish clear reporting
- **Rollback Strategy**: Plan for failures

### Git Worktree Usage

**Advantages**:

- Parallel work without conflicts
- Isolated testing environments
- Easy context switching
- Clean merge history

**Setup**:

```bash
# Create worktrees
git worktree add <path> <branch>

# List worktrees
git worktree list

# Remove when done
git worktree remove <path>
```

### Communication

- **Status Updates**: Regular, structured updates
- **Issue Escalation**: Clear path to orchestrator
- **Context Sharing**: Complete handoff information
- **Documentation**: Record decisions and rationale

### Quality Assurance

- **Individual Validation**: Each agent tests their work
- **Integration Testing**: Test combinations
- **Final Validation**: Orchestrator comprehensive check
- **Regression Prevention**: Test for unintended interactions

### Efficiency

- **Maximize Parallelization**: Use parallel pattern when possible
- **Minimize Wait Time**: Quick handoffs in sequential
- **Clear Dependencies**: Prevent blocking
- **Resource Allocation**: Right agent for right task

---

## Pattern Selection Guide

| Scenario               | Best Pattern | Why                                   |
| ---------------------- | ------------ | ------------------------------------- |
| Independent features   | Parallel     | No dependencies, max speed            |
| Feature pipeline       | Sequential   | Clear dependencies, staged approach   |
| Large system           | Hierarchical | Manage complexity, specialized leads  |
| Quick refactoring      | Sequential   | Simple handoff, focused work          |
| Multi-platform testing | Parallel     | Independent test environments         |
| Migration project      | Hierarchical | Multiple domains, coordination needed |
| Documentation suite    | Parallel     | Independent documents                 |
| API + UI + Tests       | Sequential   | Each builds on previous               |

---

## Troubleshooting

### Parallel Pattern Issues

**Problem**: Merge conflicts

- **Solution**: Better task boundary definition, earlier integration checks

**Problem**: Duplicated work

- **Solution**: Clearer coordination document, better communication

**Problem**: Incompatible approaches

- **Solution**: Shared standards, early design review

### Sequential Pattern Issues

**Problem**: Blocking delays

- **Solution**: Time box stages, parallel backup paths

**Problem**: Handoff confusion

- **Solution**: Better handoff templates, clearer acceptance criteria

**Problem**: Quality degradation

- **Solution**: Stronger quality gates between stages

### Hierarchical Pattern Issues

**Problem**: Communication overhead

- **Solution**: Structured reporting, scheduled check-ins

**Problem**: Integration complexity

- **Solution**: Phased integration, better testing

**Problem**: Lead bottleneck

- **Solution**: Clearer delegation, worker autonomy
