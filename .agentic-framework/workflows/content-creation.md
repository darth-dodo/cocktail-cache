# Content Creation Workflow

**Purpose**: Structured workflow for creating technical documentation and content with writer-driven approach.

**Duration**: 1-3 hours (depending on content scope)

**Agents**: Writer → Writer → QA

---

## Phase 1: Outline (Writer Agent)

**Duration**: 15-30 minutes

**Objective**: Create comprehensive content outline with structure and key points.

### Tasks

- [ ] Analyze content requirements and target audience
- [ ] Define content objectives and success criteria
- [ ] Research existing documentation and identify gaps
- [ ] Create hierarchical outline with sections
- [ ] Identify key concepts and terminology
- [ ] Plan examples, diagrams, and code samples
- [ ] Determine content format and style
- [ ] Estimate scope and word count
- [ ] Gather reference materials and sources
- [ ] Review outline for completeness

### Content Type Templates

**README Documentation**:

```markdown
# Project Name

## Overview

- What is it?
- Why does it exist?
- Who is it for?

## Quick Start

- Prerequisites
- Installation
- Basic usage

## Features

- Feature 1
- Feature 2

## Documentation

- Link to detailed docs
- Link to API reference

## Contributing

- Development setup
- Guidelines

## License
```

**API Documentation**:

```markdown
# API Reference

## Overview

- Base URL
- Authentication
- Rate limits

## Endpoints

### Endpoint 1

- Method and path
- Parameters
- Request body
- Response format
- Error codes
- Examples

### Endpoint 2

[Repeat structure]

## Error Handling

- Error format
- Common errors

## Examples

- Common workflows
- Code samples
```

**Tutorial/Guide**:

```markdown
# Tutorial: [Topic]

## Introduction

- What you'll learn
- Prerequisites
- Estimated time

## Step 1: [Action]

- Explanation
- Code/commands
- Expected output
- Common issues

## Step 2: [Action]

[Repeat structure]

## Conclusion

- What you accomplished
- Next steps
- Additional resources
```

**Technical Specification**:

```markdown
# Specification: [Feature]

## Purpose

- Problem statement
- Goals and objectives

## Requirements

- Functional requirements
- Non-functional requirements
- Constraints

## Architecture

- System design
- Component diagram
- Data flow

## Implementation Details

- Technical approach
- API contracts
- Data models

## Testing Strategy

- Test scenarios
- Acceptance criteria

## References

- Related documents
- External resources
```

### Outline Template

```markdown
# Content Outline: [Title]

**Type**: [README / API Docs / Tutorial / Guide / Specification]
**Audience**: [Target reader profile]
**Objective**: [What reader should accomplish/understand]
**Estimated Length**: [X] words

## Structure

### Section 1: [Title]

- Key point 1
- Key point 2
- Example: [brief description]

### Section 2: [Title]

- Key point 1
- Key point 2
- Code sample: [brief description]

### Section 3: [Title]

[Continue structure]

## Examples & Visuals

- Example 1: [description]
- Diagram 1: [description]
- Code sample 1: [language, purpose]

## Terminology

- Term 1: Definition
- Term 2: Definition

## References

- Source 1
- Source 2
```

### Session Log Update

```markdown
## Session [N]: Content Outline - [Title]

**Agent**: Writer
**Duration**: [X] minutes
**Status**: Outline Complete

### Completed

- Content outline created
- [x] sections planned
- Examples and visuals identified
- Target audience defined

### Decisions

- Content type: [type]
- Style guide: [reference]
- Estimated scope: [X] words

### Next Steps

- Begin Phase 2: Writing
- Expand outline into full content
```

### Quality Gate: Outline Review

**Criteria**:

- [ ] Target audience clearly defined
- [ ] Content objectives measurable
- [ ] Logical section hierarchy
- [ ] Key concepts identified
- [ ] Examples planned for clarity
- [ ] Terminology defined
- [ ] Scope appropriate for topic

**Exit Condition**: All criteria met, outline approved for writing.

---

## Phase 2: Write (Writer Agent)

**Duration**: 45-150 minutes

**Objective**: Expand outline into complete, high-quality documentation.

### Tasks

- [ ] Set up documentation structure/files
- [ ] Write introduction and overview sections
- [ ] Expand each outline section with detail
- [ ] Create code examples and samples
- [ ] Add diagrams or visual aids
- [ ] Write clear, concise explanations
- [ ] Include practical examples
- [ ] Add cross-references and links
- [ ] Apply consistent formatting and style
- [ ] Proofread for grammar and clarity
- [ ] Self-review against outline objectives
- [ ] Check all links and references

### Writing Guidelines

**Clarity**:

- Use simple, direct language
- Define technical terms on first use
- One concept per paragraph
- Active voice preferred
- Short sentences (15-20 words average)

**Structure**:

- Clear headings and hierarchy
- Consistent formatting
- Logical flow and progression
- Visual breaks (lists, code blocks)
- Scannable content

**Examples**:

- Practical, real-world scenarios
- Complete, runnable code samples
- Commented for understanding
- Multiple complexity levels
- Common use cases covered

**Accessibility**:

- Descriptive link text (not "click here")
- Alt text for images
- Clear heading structure
- Consistent terminology
- Inclusive language

### Content Quality Checklist

- [ ] Meets outline objectives
- [ ] Appropriate detail level for audience
- [ ] All code examples tested and working
- [ ] Grammar and spelling checked
- [ ] Consistent terminology throughout
- [ ] No broken links or references
- [ ] Proper formatting and syntax
- [ ] Clear headings and navigation
- [ ] Examples illustrate key concepts
- [ ] Conclusion or next steps provided

### Session Log Update

```markdown
## Session [N]: Content Writing - [Title]

**Agent**: Writer
**Duration**: [X] minutes
**Status**: Draft Complete

### Completed

- Full content written ([X] words)
- [x] code examples created
- [x] diagrams/visuals added
- All sections from outline covered
- Self-review performed

### Content Statistics

- Word count: [X]
- Code samples: [X]
- Sections: [X]
- External links: [X]

### Notes

- [Any deviations from outline]
- [Additional sections added]
- [Sections removed/merged]

### Next Steps

- Hand off to QA for validation
- Begin Phase 3: Review
```

### Quality Gate: Writing Review

**Criteria**:

- [ ] All outline sections completed
- [ ] Code examples tested and functional
- [ ] Clear and concise writing
- [ ] Consistent formatting and style
- [ ] No grammar or spelling errors
- [ ] Appropriate depth for audience
- [ ] Visual aids enhance understanding
- [ ] Self-review completed

**Exit Condition**: All criteria met, content ready for QA review.

---

## Phase 3: Review (QA Agent)

**Duration**: 20-45 minutes

**Objective**: Validate content accuracy, completeness, and quality.

### Tasks

- [ ] Verify against outline objectives
- [ ] Check technical accuracy
- [ ] Test all code examples
- [ ] Validate all links and references
- [ ] Review for clarity and readability
- [ ] Check grammar and spelling
- [ ] Verify consistent terminology
- [ ] Test instructions step-by-step
- [ ] Review formatting and structure
- [ ] Check accessibility compliance
- [ ] Validate examples work as described
- [ ] Create review report

### Validation Checklist

**Technical Accuracy**:

- [ ] Code examples run without errors
- [ ] Commands produce expected output
- [ ] API examples match actual behavior
- [ ] Version numbers and dates current
- [ ] Technical details factually correct

**Completeness**:

- [ ] All outline objectives addressed
- [ ] No missing sections or placeholders
- [ ] Prerequisites clearly stated
- [ ] All terms defined
- [ ] Sufficient examples provided

**Quality**:

- [ ] Clear and understandable language
- [ ] Logical flow and organization
- [ ] Consistent style and formatting
- [ ] No grammatical errors
- [ ] Professional tone appropriate

**Usability**:

- [ ] Target audience can follow content
- [ ] Examples are practical and relevant
- [ ] Navigation is clear
- [ ] Visual aids helpful
- [ ] Next steps clearly stated

**Accessibility**:

- [ ] Proper heading hierarchy (H1 → H2 → H3)
- [ ] Descriptive link text
- [ ] Alt text for images
- [ ] Code blocks properly marked
- [ ] Consistent formatting

### Review Report Template

```markdown
# Content Review: [Title]

**Reviewer**: QA Agent
**Date**: [Date]
**Status**: [Approved / Minor Changes / Major Revision]

## Technical Accuracy

- Code examples: [All tested / Issues found]
- Facts verified: [Yes / Corrections needed]
- Links checked: [X/X] working

## Quality Assessment

### Strengths

- [Strength 1]
- [Strength 2]

### Issues Found

#### Critical (Must Fix)

- Issue 1: [Description and location]

#### Minor (Should Fix)

- Issue 1: [Description and location]

#### Suggestions (Optional)

- Suggestion 1: [Enhancement idea]

## Readability

- Clarity: [Excellent / Good / Needs Work]
- Organization: [Excellent / Good / Needs Work]
- Examples: [Excellent / Good / Needs Work]

## Accessibility

- [Pass / Fail] with notes

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Decision

[Approved / Request changes before publication]
```

### Session Log Update

```markdown
## Session [N]: Content Review - [Title]

**Agent**: QA
**Duration**: [X] minutes
**Status**: [Approved / Changes Requested]

### Review Results

- Technical accuracy: [Pass/Issues]
- Code examples: [X/X] tested and working
- Links validated: [X/X] functional
- Grammar check: [Pass/Issues]

### Issues Found

- Critical: [X]
- Minor: [X]
- Suggestions: [X]

### Overall Assessment

[Brief summary of content quality]

### Decision

[Approved for publication / Request revisions: list changes needed]
```

### Quality Gate: Final Review

**Criteria**:

- [ ] Technical accuracy verified
- [ ] All code examples tested successfully
- [ ] All links functional
- [ ] No critical issues remaining
- [ ] Grammar and spelling correct
- [ ] Accessibility compliant
- [ ] Meets outline objectives
- [ ] Ready for publication

**Exit Condition**: All criteria met, content approved for publication.

---

## Workflow Completion

### Publication Checklist

- [ ] All three phases completed successfully
- [ ] All quality gates passed
- [ ] Final review approved
- [ ] Formatting validated
- [ ] Version control updated
- [ ] Cross-references updated
- [ ] Index/TOC updated (if applicable)
- [ ] Published to target location

### Final Session Log

```markdown
## Content Creation Complete: [Title]

**Total Duration**: [X] hours
**Phases**: Outline → Write → Review
**Status**: Published

### Summary

- Content type: [type]
- Word count: [X]
- Code examples: [X]
- Sections: [X]

### Metrics

- Readability score: [if measured]
- Review iterations: [X]
- Issues resolved: [X]

### Publication Details

- Location: [URL or file path]
- Format: [Markdown / HTML / PDF]
- Target audience: [description]
```

---

## Documentation Type Guides

### README Best Practices

- Keep it concise (under 1000 words)
- Quick start in first 200 words
- Clear installation instructions
- Basic usage example
- Links to detailed docs

### API Documentation

- Consistent endpoint format
- Complete parameter descriptions
- Request/response examples
- Error code reference
- Authentication clearly explained

### Tutorials

- Step-by-step instructions
- Expected outcomes at each step
- Troubleshooting common issues
- Prerequisite knowledge stated
- Estimated completion time

### User Guides

- Task-oriented organization
- Progressive complexity
- Screenshots where helpful
- Search-friendly headings
- FAQ section for common questions

---

## Best Practices

### Writing Process

- Start with outline, don't skip it
- Write first, edit later
- Test all code examples
- Read content aloud for flow
- Take breaks for fresh perspective

### Collaboration

- Writer owns outline and draft
- QA provides constructive feedback
- Iterate based on review comments
- Maintain professional tone in feedback

### Maintenance

- Review content quarterly
- Update version-specific information
- Fix broken links promptly
- Archive outdated documentation
- Track documentation requests

### Version Control

- Branch naming: `docs/descriptive-name`
- Commit messages: `docs: description`
- Small, focused commits
- Preserve content history
