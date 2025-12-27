# Quality Gates Documentation

## Overview

The quality gates system provides a comprehensive, language-agnostic framework for ensuring code quality, security, and reliability at every stage of development. This documentation covers the complete 8-step quality gate system with both generic patterns and language-specific implementations.

## Quick Navigation

- **[Generic Gates](generic-gates.md)** - Language-agnostic 8-step quality gate system
- **Language-Specific Examples**:
  - [JavaScript/TypeScript](examples/javascript.md) - npm/pnpm, ESLint, Vitest, Playwright
  - [Python](examples/python.md) - pip/poetry, ruff, mypy, pytest
  - [Go](examples/go.md) - go tooling, golangci-lint, govulncheck

## The 8 Quality Gates

### Gate 1: Syntax Validation

Verify code parses correctly without syntax errors.

- **Focus**: Language-specific syntax rules, import resolution, compilation
- **Tools**: Compilers, parsers, basic linters
- **Timing**: Pre-commit hook, instant feedback

### Gate 2: Type Safety

Ensure type consistency and catch type-related errors before runtime.

- **Focus**: Type annotations, type compatibility, null safety
- **Tools**: Type checkers (TypeScript, mypy, staticcheck)
- **Timing**: Pre-commit hook, CI/CD

### Gate 3: Code Quality (Lint)

Enforce coding standards and detect code smells.

- **Focus**: Style consistency, complexity, best practices
- **Tools**: Linters, formatters, complexity analyzers
- **Timing**: Pre-commit hook with auto-fix, CI/CD

### Gate 4: Security

Identify vulnerabilities and unsafe code patterns.

- **Focus**: CVEs, unsafe patterns, secrets, licenses
- **Tools**: Dependency audits, security scanners, secret detectors
- **Timing**: Pre-commit (secrets), CI/CD (full audit)

### Gate 5: Tests

Verify functionality through automated testing.

- **Focus**: Unit, integration, E2E tests with coverage thresholds
- **Tools**: Test runners, coverage tools, E2E frameworks
- **Timing**: Pre-commit (affected tests), CI/CD (full suite)

### Gate 6: Performance

Ensure application meets performance requirements.

- **Focus**: Benchmarks, memory usage, bundle size, response times
- **Tools**: Profilers, benchmark tools, load testers
- **Timing**: CI/CD, periodic monitoring

### Gate 7: Accessibility

Ensure application is usable by everyone.

- **Focus**: WCAG 2.1 AA compliance, semantic HTML, ARIA
- **Tools**: Accessibility scanners, automated testing
- **Timing**: CI/CD, manual testing

### Gate 8: Integration

Verify application works in production-like environment.

- **Focus**: Build success, deployment, health checks, smoke tests
- **Tools**: Docker, E2E tests, monitoring
- **Timing**: CI/CD, deployment pipeline

## Implementation Approaches

### Local Development Workflow

**Pre-commit Hooks** (Gates 1-4):

```bash
#!/bin/bash
# Fast feedback on common issues
# Auto-fix enabled where possible
# Blocks commit on critical failures
```

**Pre-push Hooks** (Gates 5-6, Quick):

```bash
#!/bin/bash
# Run affected tests only
# Quick performance benchmarks
# Longer-running validations
```

### CI/CD Pipeline Workflow

**Pull Request Checks** (All Gates):

```yaml
# Full validation suite
# Comprehensive reporting
# No auto-merge without passing all gates
```

**Deployment Pipeline** (Gates 6-8 Enhanced):

```yaml
# Production build verification
# Staging deployment with integration tests
# Performance regression detection
# Health check validation
```

## Language-Specific Quick Start

### JavaScript/TypeScript

```bash
# Setup
npm install --save-dev eslint prettier typescript vitest playwright

# Run all gates locally
npm run lint && npm run typecheck && npm test

# See: examples/javascript.md for full details
```

### Python

```bash
# Setup
pip install ruff mypy pytest pip-audit bandit

# Run all gates locally
ruff check . && mypy . && pytest

# See: examples/python.md for full details
```

### Go

```bash
# Setup
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run all gates locally
golangci-lint run && go test -race ./...

# See: examples/go.md for full details
```

## Integration Strategies

### Pre-commit Hooks

**Install pre-commit framework**:

```bash
# Python
pip install pre-commit

# Create .pre-commit-config.yaml
pre-commit install
```

**Example .pre-commit-config.yaml** (Python):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [--lf, --tb=short, --no-cov]
```

### GitHub Actions

**Complete Pipeline** (.github/workflows/quality-gates.yml):

```yaml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Gate 1-2: Syntax & Types
      - name: Syntax and Type Validation
        run: <language-specific-commands>

      # Gate 3: Code Quality
      - name: Lint and Format
        run: <linter-commands>

      # Gate 4: Security
      - name: Security Scan
        run: <security-tools>

      # Gate 5: Tests
      - name: Test Suite
        run: <test-commands>

      # Gate 6: Performance
      - name: Performance Tests
        run: <benchmark-commands>

      # Gate 7: Accessibility
      - name: Accessibility Tests
        run: <a11y-commands>

      # Gate 8: Integration
      - name: Integration Tests
        run: <integration-commands>
```

### GitLab CI

**Complete Pipeline** (.gitlab-ci.yml):

```yaml
stages:
  - validate
  - test
  - integrate

syntax:
  stage: validate
  script:
    - <syntax-validation>

security:
  stage: validate
  script:
    - <security-scan>

test:
  stage: test
  script:
    - <test-suite>
  coverage: '/TOTAL.*\s+(\d+%)$/'

integration:
  stage: integrate
  script:
    - <integration-tests>
```

## Customization Guide

### Adjusting Quality Thresholds

**Coverage Thresholds**:

- **Critical Code**: 90%+ (authentication, payments, data processing)
- **Business Logic**: 80%+ (standard requirement)
- **Utilities**: 70%+ (acceptable for helpers)
- **UI Components**: 60%+ (often harder to test)

**Performance Thresholds**:

- **API Response Time**: p95 < 200ms
- **Web Load Time**: < 3s on 3G, < 1s on WiFi
- **Bundle Size**: < 500KB initial, < 2MB total
- **Memory Usage**: No leaks, stable over time

**Complexity Thresholds**:

- **Cyclomatic Complexity**: < 10 (warning), < 15 (error)
- **Cognitive Complexity**: < 15 (warning), < 20 (error)
- **Lines per Function**: < 50 (warning), < 100 (error)

### Skipping Gates (Use Sparingly)

**Temporary Skips**:

```bash
# Git commit with skip
git commit --no-verify  # Skip pre-commit hooks

# CI skip
git commit -m "feat: new feature [skip ci]"
```

**Permanent Exceptions**:

```javascript
// ESLint ignore
/* eslint-disable security/detect-object-injection */
const value = obj[key]; // Justified exception
/* eslint-enable security/detect-object-injection */
```

```python
# mypy ignore
def legacy_function() -> None:
    data = load_data()  # type: ignore[no-untyped-call]
```

```go
// nolint:gosec
password := os.Getenv("PASSWORD")  // Justified: config loading
```

### Progressive Adoption

**Phase 1: Essential Gates** (Week 1-2)

- Gate 1: Syntax Validation
- Gate 5: Tests (basic coverage)
- Gate 4: Security (critical issues only)

**Phase 2: Quality Gates** (Week 3-4)

- Gate 2: Type Safety
- Gate 3: Code Quality
- Gate 5: Tests (increase coverage threshold)

**Phase 3: Advanced Gates** (Month 2)

- Gate 6: Performance
- Gate 7: Accessibility
- Gate 8: Integration

**Phase 4: Optimization** (Month 3+)

- Fine-tune thresholds
- Add custom rules
- Optimize CI/CD pipeline

## Best Practices

### 1. Fail Fast

- Run cheapest gates first (syntax before tests)
- Parallelize independent gates
- Cache dependencies and results

### 2. Clear Feedback

- Provide actionable error messages
- Include fix suggestions where possible
- Link to documentation

### 3. Developer Experience

- Keep pre-commit hooks fast (< 30s)
- Auto-fix issues where safe
- Don't block on warnings, only errors

### 4. Continuous Improvement

- Track gate failure rates
- Monitor execution times
- Gather developer feedback
- Update thresholds based on data

### 5. Documentation

- Document all custom rules
- Explain why gates exist
- Provide examples of fixes
- Keep documentation updated

## Troubleshooting

### Common Issues

**Pre-commit hooks too slow**:

```bash
# Solution: Run only affected files
git diff --cached --name-only | xargs <tool>

# Or: Use incremental tools
vitest --changed HEAD
mypy --incremental
```

**CI/CD timeouts**:

```yaml
# Solution: Parallelize and cache
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - run: npm test -- --shard=${{ matrix.shard }}/4
```

**False positives**:

```bash
# Solution: Configure exceptions in tool config
# .eslintrc.js, mypy.ini, .golangci.yml
# Document why exception is needed
```

## Metrics and Reporting

### Track These Metrics

**Quality Trends**:

- Test coverage over time
- Linting error count
- Security vulnerability count
- Performance regression frequency

**Process Metrics**:

- Gate failure rate by type
- Time to fix gate failures
- Developer feedback scores
- CI/CD execution time

**Business Impact**:

- Production bugs per release
- Time to detect issues
- Cost of quality issues
- Developer productivity

### Reporting Tools

**Coverage Reports**:

- Codecov, Coveralls (multi-language)
- SonarQube (comprehensive analysis)

**Security Reports**:

- Snyk, GitHub Dependabot
- Custom dashboard with aggregated scans

**Performance Reports**:

- Lighthouse CI for web
- Custom benchmark dashboards
- APM tools (New Relic, DataDog)

## Additional Resources

### Official Documentation

- [Generic Gates Reference](generic-gates.md) - Complete 8-gate system
- [JavaScript/TypeScript Guide](examples/javascript.md) - Web development stack
- [Python Guide](examples/python.md) - Backend and data science
- [Go Guide](examples/go.md) - High-performance services

### External Resources

- [Pre-commit Framework](https://pre-commit.com/) - Multi-language hook framework
- [GitHub Actions](https://github.com/features/actions) - CI/CD automation
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/) - Accessibility standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Security best practices

## Contributing

To add a new language-specific implementation:

1. Copy `examples/template.md` (if available) or use an existing example
2. Follow the 8-gate structure
3. Include practical, copy-paste commands
4. Add pre-commit hook examples
5. Include CI/CD integration
6. Test all commands in a real project
7. Submit pull request with examples

## Support

For questions, issues, or suggestions:

- Create an issue in the repository
- Review existing language examples
- Check the troubleshooting section
- Consult official tool documentation

---

**Remember**: Quality gates are tools to help developers, not barriers. They should provide value through fast feedback, clear guidance, and actionable insights. Adjust thresholds and gates to match your team's needs and project requirements.
