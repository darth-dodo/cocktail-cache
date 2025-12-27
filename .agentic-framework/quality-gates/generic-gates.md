# Generic Quality Gates

## Overview

The 8-step quality gate system ensures code quality, security, and reliability across all projects regardless of programming language. Each gate represents a critical checkpoint that code must pass before being considered production-ready.

**Gate Execution Order**: Sequential execution recommended, though gates 1-4 can run in parallel with proper tooling.

**Automation Strategy**: Integrate into pre-commit hooks (gates 1-4) and CI/CD pipelines (all gates).

---

## Gate 1: Syntax Validation

### Purpose

Verify code parses correctly without syntax errors. This is the foundational gate that must pass before any other validation.

### What It Checks

- Language-specific syntax rules
- File encoding and format issues
- Import/module resolution
- Basic compilation/parsing errors

### Generic Commands

```bash
# Language-specific parser/compiler
<COMPILER> --syntax-check <FILES>
<PARSER> --validate <FILES>

# Check all files in project
find src -name "*.<ext>" -exec <PARSER> {} \;
```

### Pass Criteria

- Zero syntax errors
- All files parse successfully
- All imports/modules resolve correctly
- No encoding issues

### Common Issues and Fixes

**Issue**: Syntax errors in multiple files

```bash
# Solution: Fix syntax errors one file at a time
<PARSER> --verbose <FILE> 2>&1 | grep "error"
```

**Issue**: Import/module not found

```bash
# Solution: Check dependency installation
<PACKAGE_MANAGER> list | grep <DEPENDENCY>
<PACKAGE_MANAGER> install <DEPENDENCY>
```

**Issue**: File encoding problems

```bash
# Solution: Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 <FILE> > <FILE>.utf8
mv <FILE>.utf8 <FILE>
```

### Automation Tips

**Pre-commit Hook**:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Gate 1: Syntax Validation"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.<ext>$')

for FILE in $STAGED_FILES; do
    <PARSER> --syntax-check "$FILE"
    if [ $? -ne 0 ]; then
        echo "Syntax validation failed: $FILE"
        exit 1
    fi
done
```

**CI/CD Integration**:

```yaml
# .github/workflows/quality-gates.yml
- name: Gate 1 - Syntax Validation
  run: |
    <COMPILER> --syntax-check src/**/*.<ext>
```

---

## Gate 2: Type Safety

### Purpose

Ensure type consistency and catch type-related errors before runtime. Critical for statically-typed languages and optional type systems.

### What It Checks

- Type annotations correctness
- Type compatibility in assignments
- Function signature compliance
- Generic type constraints
- Null/undefined safety

### Generic Commands

```bash
# Type checker
<TYPE_CHECKER> --strict <FILES>
<TYPE_CHECKER> --no-implicit-any <FILES>

# Project-wide type check
<TYPE_CHECKER> --project <CONFIG_FILE>
```

### Pass Criteria

- Zero type errors
- All type annotations valid
- No implicit any/dynamic types (strict mode)
- Type inference working correctly
- All generics properly constrained

### Common Issues and Fixes

**Issue**: Missing type annotations

```bash
# Solution: Add explicit types
<TYPE_CHECKER> --show-missing-types <FILE>
```

**Issue**: Incompatible types

```bash
# Solution: Review type definitions and conversions
<TYPE_CHECKER> --verbose <FILE> | grep "Type.*is not assignable"
```

**Issue**: Null/undefined errors

```bash
# Solution: Add null checks or use optional chaining
# Use strict null checks mode
<TYPE_CHECKER> --strict-null-checks <FILES>
```

### Automation Tips

**Pre-commit Hook**:

```bash
#!/bin/bash
echo "Gate 2: Type Safety"
<TYPE_CHECKER> --no-emit --project tsconfig.json
if [ $? -ne 0 ]; then
    echo "Type checking failed"
    exit 1
fi
```

**CI/CD Integration**:

```yaml
- name: Gate 2 - Type Safety
  run: |
    <TYPE_CHECKER> --strict --project <CONFIG>
```

**Configuration Best Practices**:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

---

## Gate 3: Code Quality (Lint)

### Purpose

Enforce coding standards, detect code smells, and maintain consistent style across the codebase.

### What It Checks

- Code style consistency
- Best practice violations
- Code complexity metrics
- Unused code detection
- Import organization
- Naming conventions
- Code duplication

### Generic Commands

```bash
# Linter
<LINTER> <FILES>
<LINTER> --fix <FILES>  # Auto-fix issues

# Check entire project
<LINTER> src/

# Complexity analysis
<COMPLEXITY_TOOL> --threshold <MAX_COMPLEXITY> <FILES>
```

### Pass Criteria

- Zero linting errors
- All warnings addressed or explicitly ignored
- Cyclomatic complexity below threshold (typically 10-15)
- Code duplication below 5%
- All imports organized and used

### Common Issues and Fixes

**Issue**: Code style violations

```bash
# Solution: Auto-format code
<FORMATTER> --write <FILES>
<LINTER> --fix <FILES>
```

**Issue**: High complexity

```bash
# Solution: Refactor complex functions
<COMPLEXITY_TOOL> --show-complexity <FILE>
# Break down functions with complexity > 15
```

**Issue**: Unused imports/variables

```bash
# Solution: Remove unused code
<LINTER> --fix-unused <FILES>
```

**Issue**: Code duplication

```bash
# Solution: Extract common logic
<DUPLICATION_DETECTOR> --threshold 5 src/
# Refactor duplicate code into shared functions/modules
```

### Automation Tips

**Pre-commit Hook**:

```bash
#!/bin/bash
echo "Gate 3: Code Quality"

# Auto-fix formatting
<FORMATTER> --write $(git diff --cached --name-only)

# Run linter
<LINTER> $(git diff --cached --name-only | grep '\.<ext>$')
if [ $? -ne 0 ]; then
    echo "Linting failed. Run '<LINTER> --fix' to auto-fix issues."
    exit 1
fi

# Add fixed files
git add -u
```

**CI/CD Integration**:

```yaml
- name: Gate 3 - Code Quality
  run: |
    <LINTER> --max-warnings 0 src/
    <COMPLEXITY_TOOL> --threshold 15 src/
```

**Quality Configuration**:

```json
{
  "rules": {
    "max-complexity": ["error", 15],
    "max-lines-per-function": ["warn", 50],
    "no-duplicate-code": ["error", { "threshold": 5 }]
  }
}
```

---

## Gate 4: Security

### Purpose

Identify security vulnerabilities, unsafe dependencies, and potential security risks before deployment.

### What It Checks

- Known CVEs in dependencies
- Outdated packages with security issues
- Unsafe code patterns (SQL injection, XSS, etc.)
- Hardcoded secrets/credentials
- Insecure cryptography usage
- License compliance

### Generic Commands

```bash
# Dependency audit
<PACKAGE_MANAGER> audit
<PACKAGE_MANAGER> audit --fix

# Security scanner
<SECURITY_SCANNER> <FILES>
<SECURITY_SCANNER> --severity high --severity critical

# Secret detection
<SECRET_SCANNER> scan <FILES>

# License check
<LICENSE_CHECKER> check
```

### Pass Criteria

- Zero critical/high vulnerabilities
- All medium vulnerabilities assessed and documented
- No hardcoded secrets detected
- All dependencies have compatible licenses
- Secure coding patterns followed

### Common Issues and Fixes

**Issue**: Vulnerable dependencies

```bash
# Solution: Update dependencies
<PACKAGE_MANAGER> audit
<PACKAGE_MANAGER> update <VULNERABLE_PACKAGE>
# If no fix available, document risk and mitigation
```

**Issue**: Hardcoded secrets

```bash
# Solution: Use environment variables
<SECRET_SCANNER> scan .
# Move secrets to .env or secret manager
# Add .env to .gitignore
```

**Issue**: SQL injection vulnerabilities

```bash
# Solution: Use parameterized queries
# Bad:  query = "SELECT * FROM users WHERE id = " + user_input
# Good: query = "SELECT * FROM users WHERE id = ?"
```

**Issue**: Insecure dependencies

```bash
# Solution: Pin secure versions
<PACKAGE_MANAGER> list --outdated
<PACKAGE_MANAGER> install <PACKAGE>@<SECURE_VERSION>
```

### Automation Tips

**Pre-commit Hook**:

```bash
#!/bin/bash
echo "Gate 4: Security"

# Secret detection
<SECRET_SCANNER> scan --staged
if [ $? -ne 0 ]; then
    echo "Secrets detected in staged files!"
    exit 1
fi

# Quick dependency check (full audit in CI)
<PACKAGE_MANAGER> audit --audit-level=high
```

**CI/CD Integration**:

```yaml
- name: Gate 4 - Security
  run: |
    <PACKAGE_MANAGER> audit --audit-level=moderate
    <SECURITY_SCANNER> --severity high .
    <SECRET_SCANNER> scan .
  continue-on-error: false
```

**Security Best Practices**:

- Run full security scan daily in CI
- Use dependency lock files
- Enable automated dependency updates
- Maintain security.md with vulnerability disclosure policy
- Use secret management service in production

---

## Gate 5: Tests

### Purpose

Verify functionality through automated testing, ensuring code works as intended and regressions are caught early.

### What It Checks

- Unit test coverage (≥80% for critical code)
- Integration test coverage (≥70%)
- End-to-end test coverage for critical paths
- Test suite execution time
- Test reliability (no flaky tests)

### Generic Commands

```bash
# Run all tests
<TEST_RUNNER> <TEST_DIR>

# Run with coverage
<TEST_RUNNER> --coverage --coverage-threshold=80

# Run specific test types
<TEST_RUNNER> --unit
<TEST_RUNNER> --integration
<TEST_RUNNER> --e2e

# Watch mode for development
<TEST_RUNNER> --watch
```

### Pass Criteria

- All tests pass
- Unit test coverage ≥80% for src/
- Integration test coverage ≥70%
- Critical user paths have E2E tests
- No flaky tests (100% pass rate over 10 runs)
- Test execution time <5 minutes (unit/integration)

### Common Issues and Fixes

**Issue**: Low test coverage

```bash
# Solution: Generate coverage report and add tests
<TEST_RUNNER> --coverage --coverage-report=html
# Open coverage report and add tests for uncovered code
```

**Issue**: Flaky tests

```bash
# Solution: Run tests multiple times to identify flakiness
for i in {1..10}; do
    <TEST_RUNNER> <TEST_FILE> || echo "Failed on run $i"
done
# Fix timing issues, race conditions, or external dependencies
```

**Issue**: Slow tests

```bash
# Solution: Profile test execution
<TEST_RUNNER> --profile
# Parallelize tests or optimize slow tests
<TEST_RUNNER> --parallel
```

**Issue**: Tests not running in CI

```bash
# Solution: Check test environment
<TEST_RUNNER> --verbose --debug
# Ensure dependencies installed and environment variables set
```

### Automation Tips

**Pre-commit Hook** (Quick smoke tests):

```bash
#!/bin/bash
echo "Gate 5: Tests (Quick)"

# Run affected tests only (if tool available)
<TEST_RUNNER> --changed --coverage=false
if [ $? -ne 0 ]; then
    echo "Tests failed. Fix before committing."
    exit 1
fi
```

**CI/CD Integration** (Full test suite):

```yaml
- name: Gate 5 - Tests
  run: |
    <TEST_RUNNER> --coverage --coverage-threshold=80
    <TEST_RUNNER> --e2e --headed=false
  env:
    CI: true
```

**Test Organization**:

```
tests/
├── unit/          # Fast, isolated tests
├── integration/   # Multi-component tests
├── e2e/          # Full user flow tests
└── fixtures/     # Test data
```

---

## Gate 6: Performance

### Purpose

Ensure application meets performance requirements and identify optimization opportunities before degradation affects users.

### What It Checks

- Response time benchmarks
- Memory usage patterns
- CPU utilization
- Bundle size limits (web)
- Database query performance
- API endpoint latency
- Lighthouse scores (web: ≥90)

### Generic Commands

```bash
# Benchmark tests
<BENCHMARK_TOOL> run <BENCHMARK_SUITE>

# Memory profiling
<PROFILER> --memory <APP_COMMAND>

# Performance tests
<PERF_TOOL> test --threshold <MAX_TIME>

# Bundle analysis (web)
<BUNDLER> analyze --max-size <LIMIT>

# Load testing
<LOAD_TESTER> --users 100 --duration 60s <URL>
```

### Pass Criteria

- All benchmarks within acceptable thresholds
- Memory usage stable (no leaks)
- API response time p95 <200ms
- Web bundle size <500KB initial
- Lighthouse performance score ≥90
- Database queries <100ms p95
- Load test passes at expected scale

### Common Issues and Fixes

**Issue**: Slow API responses

```bash
# Solution: Profile and optimize
<PROFILER> --trace <ENDPOINT>
# Add caching, optimize queries, or add indexes
```

**Issue**: Large bundle size

```bash
# Solution: Analyze and optimize
<BUNDLER> analyze
# Lazy load components, remove unused dependencies
<DEPENDENCY_ANALYZER> --unused
```

**Issue**: Memory leaks

```bash
# Solution: Profile memory usage
<PROFILER> --memory --duration=600s
# Identify and fix leak sources (listeners, closures, caches)
```

**Issue**: Poor Lighthouse scores

```bash
# Solution: Run Lighthouse and follow recommendations
<LIGHTHOUSE> <URL> --output=html
# Optimize images, lazy load, reduce JavaScript
```

### Automation Tips

**Pre-push Hook**:

```bash
#!/bin/bash
echo "Gate 6: Performance (Quick check)"

# Run critical benchmarks only
<BENCHMARK_TOOL> run --quick
if [ $? -ne 0 ]; then
    echo "Performance regression detected!"
    exit 1
fi
```

**CI/CD Integration**:

```yaml
- name: Gate 6 - Performance
  run: |
    <BENCHMARK_TOOL> run --compare baseline.json
    <BUNDLER> analyze --max-initial 500kb
    <LIGHTHOUSE> --preset=ci <PREVIEW_URL>
  continue-on-error: false

- name: Upload Performance Report
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: performance-results/
```

**Performance Monitoring**:

```bash
# Track performance over time
<BENCHMARK_TOOL> run --export results/benchmark-$(date +%Y%m%d).json

# Compare against baseline
<BENCHMARK_TOOL> compare --baseline main --current HEAD
```

---

## Gate 7: Accessibility

### Purpose

Ensure application is usable by everyone, including people with disabilities, meeting WCAG 2.1 AA standards.

### What It Checks

- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios (4.5:1 minimum)
- Focus management
- Alternative text for images
- Form labels and error messages

### Generic Commands

```bash
# Accessibility scanner
<A11Y_SCANNER> <URL_OR_FILES>
<A11Y_SCANNER> --standard WCAG2AA

# Automated testing
<TEST_RUNNER> --a11y

# Lighthouse accessibility audit
<LIGHTHOUSE> <URL> --only-categories=accessibility

# Color contrast checker
<CONTRAST_CHECKER> <COLOR1> <COLOR2>
```

### Pass Criteria

- WCAG 2.1 AA compliance (score ≥90)
- Zero critical accessibility violations
- All interactive elements keyboard accessible
- All images have alt text
- Color contrast ratios meet standards
- Screen reader test passes
- Focus indicators visible

### Common Issues and Fixes

**Issue**: Missing alt text

```bash
# Solution: Find images without alt text
<A11Y_SCANNER> --check-images <FILES>
# Add descriptive alt text to all images
```

**Issue**: Poor color contrast

```bash
# Solution: Check and fix contrast
<CONTRAST_CHECKER> --scan <CSS_FILES>
# Update colors to meet 4.5:1 ratio minimum
```

**Issue**: Keyboard navigation broken

```bash
# Solution: Test and fix tab order
# Add tabindex where needed
# Ensure all interactive elements accessible via keyboard
```

**Issue**: Missing ARIA labels

```bash
# Solution: Add ARIA attributes
<A11Y_SCANNER> --check-aria <FILES>
# Add aria-label, aria-labelledby, or aria-describedby
```

### Automation Tips

**Pre-commit Hook**:

```bash
#!/bin/bash
echo "Gate 7: Accessibility (Static analysis)"

# Run static accessibility checks
<A11Y_LINTER> $(git diff --cached --name-only | grep '\.(html|jsx|tsx|vue)$')
if [ $? -ne 0 ]; then
    echo "Accessibility violations found!"
    exit 1
fi
```

**CI/CD Integration**:

```yaml
- name: Gate 7 - Accessibility
  run: |
    <A11Y_SCANNER> --standard WCAG2AA src/
    <LIGHTHOUSE> --only-categories=accessibility <PREVIEW_URL>
    <TEST_RUNNER> --a11y
```

**Accessibility Checklist**:

- [ ] Semantic HTML (header, nav, main, footer)
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation works for all features
- [ ] Focus indicators visible
- [ ] Color contrast 4.5:1 minimum
- [ ] Images have descriptive alt text
- [ ] Forms have proper labels
- [ ] Screen reader tested manually

---

## Gate 8: Integration

### Purpose

Verify the application works correctly in a production-like environment with all dependencies and integrations.

### What It Checks

- Application builds successfully
- Production deployment succeeds
- Environment configuration valid
- External API integrations working
- Database migrations successful
- Service health checks passing
- Monitoring and logging functional

### Generic Commands

```bash
# Build verification
<BUILD_TOOL> --production
<BUILD_TOOL> --check

# Integration tests
<TEST_RUNNER> --integration --env=staging

# Health checks
curl -f <HEALTH_ENDPOINT> || exit 1
<MONITORING_TOOL> check

# Deployment validation
<DEPLOY_TOOL> verify --environment staging

# End-to-end smoke tests
<E2E_RUNNER> --smoke-tests --env=staging
```

### Pass Criteria

- Production build completes successfully
- All integration tests pass
- Health endpoints return 200 OK
- External services reachable
- Database connections successful
- Monitoring dashboards show green
- Smoke tests pass in staging

### Common Issues and Fixes

**Issue**: Build failures

```bash
# Solution: Debug build process
<BUILD_TOOL> --verbose --debug
# Check environment variables and dependencies
```

**Issue**: Integration test failures

```bash
# Solution: Verify external service availability
<TEST_RUNNER> --integration --verbose
# Check network connectivity and API keys
```

**Issue**: Health check failures

```bash
# Solution: Investigate service status
curl -v <HEALTH_ENDPOINT>
<MONITORING_TOOL> logs --since 1h
# Fix underlying service issues
```

**Issue**: Database migration errors

```bash
# Solution: Test migrations in isolation
<MIGRATION_TOOL> up --dry-run
<MIGRATION_TOOL> status
# Fix migration scripts and rerun
```

### Automation Tips

**Pre-deployment Hook**:

```bash
#!/bin/bash
echo "Gate 8: Integration (Pre-deployment)"

# Verify production build
<BUILD_TOOL> --production
if [ $? -ne 0 ]; then
    echo "Production build failed!"
    exit 1
fi

# Run smoke tests
<E2E_RUNNER> --smoke-tests
```

**CI/CD Integration**:

```yaml
- name: Gate 8 - Integration
  run: |
    # Build for production
    <BUILD_TOOL> --production

    # Deploy to staging
    <DEPLOY_TOOL> --environment staging

    # Run integration tests
    <TEST_RUNNER> --integration --env=staging

    # Health checks
    curl -f $STAGING_URL/health

    # Smoke tests
    <E2E_RUNNER> --smoke-tests --env=staging
  env:
    STAGING_URL: ${{ secrets.STAGING_URL }}
```

**Post-deployment Validation**:

```bash
#!/bin/bash
# Run after deployment

# Health check
curl -f https://api.example.com/health

# Monitor logs
<MONITORING_TOOL> logs --follow --error-level ERROR

# Verify key features
<E2E_RUNNER> --critical-paths --env=production
```

---

## Complete Quality Gate Workflow

### Local Development

```bash
# Pre-commit (Gates 1-4)
git add .
git commit -m "feat: new feature"
# Runs: syntax, types, lint, security (auto-fix enabled)

# Pre-push (Gates 5-6 quick)
git push
# Runs: affected tests, critical benchmarks
```

### CI/CD Pipeline

```yaml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Gate 1 - Syntax
        run: <PARSER> --check src/

      - name: Gate 2 - Types
        run: <TYPE_CHECKER> --strict

      - name: Gate 3 - Lint
        run: <LINTER> --max-warnings 0

      - name: Gate 4 - Security
        run: |
          <PACKAGE_MANAGER> audit
          <SECURITY_SCANNER> .

      - name: Gate 5 - Tests
        run: <TEST_RUNNER> --coverage --threshold=80

      - name: Gate 6 - Performance
        run: <BENCHMARK_TOOL> run --compare baseline.json

      - name: Gate 7 - Accessibility
        run: <A11Y_SCANNER> src/

      - name: Gate 8 - Integration
        run: |
          <BUILD_TOOL> --production
          <E2E_RUNNER> --smoke-tests
```

### Deployment Pipeline

```bash
# Staging deployment
1. All gates pass in CI
2. Deploy to staging
3. Run integration tests (Gate 8)
4. Manual QA approval

# Production deployment
1. All gates pass
2. Staging validation complete
3. Deploy to production
4. Post-deployment health checks
5. Monitor for 24 hours
```

---

## Continuous Improvement

### Gate Metrics Tracking

```bash
# Track gate performance over time
gate,timestamp,duration,status
syntax,2024-01-15T10:00:00Z,2.3s,pass
types,2024-01-15T10:00:02Z,5.1s,pass
lint,2024-01-15T10:00:07Z,3.8s,pass
security,2024-01-15T10:00:11Z,12.4s,pass
tests,2024-01-15T10:00:23Z,45.2s,pass
performance,2024-01-15T10:01:08Z,23.1s,pass
accessibility,2024-01-15T10:01:31Z,8.3s,pass
integration,2024-01-15T10:01:39Z,67.5s,pass
```

### Quality Trends

- Monitor gate failure rates
- Track time to fix failures
- Measure test coverage trends
- Monitor performance regression frequency
- Track security vulnerability resolution time

### Optimization Opportunities

- Parallelize independent gates (1-4)
- Cache dependencies between runs
- Incremental analysis for large codebases
- Smart test selection (run affected tests only)
- Progressive quality gates (fail fast)
