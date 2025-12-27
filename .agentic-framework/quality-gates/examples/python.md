# Python Quality Gates

## Overview

Language-specific implementation of the 8-step quality gate system for Python projects. Includes practical commands for pip/poetry, modern Python tooling, and best practices for both web and CLI applications.

**Tech Stack**: Python 3.10+, ruff, mypy, pytest, pip-audit, bandit

---

## Gate 1: Syntax Validation

### Tools

- Python built-in parser
- ruff (linter with syntax checking)
- py_compile module

### Commands

**Basic Syntax Check**:

```bash
# Check single file
python -m py_compile src/main.py

# Check all Python files
find src -name "*.py" -exec python -m py_compile {} \;

# Using ruff (faster)
ruff check src/

# Verbose output
python -m compileall src/ -q
```

**AST Validation**:

```bash
# Verify abstract syntax tree
python -c "import ast; ast.parse(open('src/main.py').read())"

# Check all files
for file in src/**/*.py; do
    python -c "import ast; ast.parse(open('$file').read())" || echo "Syntax error in $file"
done
```

### Configuration

**pyproject.toml**:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100
select = ["E", "F"]  # E = pycodestyle, F = pyflakes
src = ["src", "tests"]

[tool.ruff.lint]
extend-select = ["I"]  # isort
```

### Pre-commit Hook

**.git/hooks/pre-commit**:

```bash
#!/bin/bash
echo "🔍 Gate 1: Syntax Validation"

# Get staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Check syntax
for file in $STAGED_FILES; do
    python -m py_compile "$file"
    if [ $? -ne 0 ]; then
        echo "❌ Syntax error in $file"
        exit 1
    fi
done

echo "✅ Syntax validation passed"
```

### CI/CD Integration

**.github/workflows/quality-gates.yml**:

```yaml
- name: Gate 1 - Syntax Validation
  run: |
    python -m compileall src/ -q
    ruff check src/
```

### Common Issues

**Issue**: Indentation errors

```bash
# Solution: Use consistent indentation (4 spaces)
# Check mixed tabs/spaces
grep -n $'\t' src/**/*.py

# Auto-fix with ruff
ruff check --fix src/
```

**Issue**: Import errors

```bash
# Solution: Verify imports exist
python -c "import module_name"

# Check all imports
python -m pip list | grep module_name
```

---

## Gate 2: Type Safety

### Tools

- mypy (static type checker)
- pyright (Microsoft's type checker)
- pydantic (runtime type validation)

### Commands

**Type Checking with mypy**:

```bash
# Check all files
mypy src/

# Strict mode
mypy --strict src/

# Specific files
mypy src/main.py src/utils.py

# Generate coverage report
mypy --html-report mypy-report src/
```

**Type Checking with pyright**:

```bash
# Install
npm install -g pyright

# Run type checking
pyright src/

# Strict mode
pyright --pythonversion 3.10 src/
```

**Type Coverage**:

```bash
# Install type coverage tool
pip install type-coverage

# Check coverage
type-coverage src/ --min-coverage 90
```

### Configuration

**pyproject.toml**:

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**pyrightconfig.json**:

```json
{
  "include": ["src"],
  "exclude": ["**/node_modules", "**/__pycache__"],
  "pythonVersion": "3.10",
  "typeCheckingMode": "strict",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "strictListInference": true,
  "strictDictionaryInference": true,
  "strictSetInference": true
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🔒 Gate 2: Type Safety"

# Run mypy in strict mode
mypy --strict src/
if [ $? -ne 0 ]; then
    echo "❌ Type checking failed"
    exit 1
fi

# Check type coverage
TYPE_COVERAGE=$(type-coverage src/ --min-coverage 90 2>&1)
if [ $? -ne 0 ]; then
    echo "⚠️  Type coverage below 90%"
    echo "$TYPE_COVERAGE"
fi

echo "✅ Type safety passed"
```

### CI/CD Integration

```yaml
- name: Gate 2 - Type Safety
  run: |
    pip install mypy type-coverage
    mypy --strict src/
    type-coverage src/ --min-coverage 90
```

### Type Hints Examples

**Basic Types**:

```python
from typing import List, Dict, Optional, Union, Tuple, Callable

def process_data(
    items: List[str],
    config: Dict[str, int],
    max_retries: int = 3,
    callback: Optional[Callable[[str], None]] = None
) -> Tuple[bool, str]:
    """Process data with type safety."""
    for item in items:
        if callback:
            callback(item)
    return True, "Success"
```

**Advanced Types**:

```python
from typing import TypedDict, Literal, Protocol, Generic, TypeVar

# Typed dictionary
class UserDict(TypedDict):
    id: int
    name: str
    email: str
    active: bool

# Literal types
Status = Literal["pending", "active", "completed"]

# Protocol (structural subtyping)
class Drawable(Protocol):
    def draw(self) -> None: ...

# Generics
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: int) -> Optional[T]:
        ...
```

---

## Gate 3: Code Quality (Lint)

### Tools

- ruff (fast Python linter and formatter)
- black (code formatter)
- isort (import sorter)
- pylint (comprehensive linter)

### Commands

**Linting with ruff**:

```bash
# Lint all files
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/

# Check specific rules
ruff check --select E,F,I src/
```

**Formatting with black**:

```bash
# Check formatting
black --check src/

# Auto-format
black src/

# Diff preview
black --diff src/
```

**Import Sorting**:

```bash
# Check imports
isort --check-only src/

# Auto-sort imports
isort src/

# With black compatibility
isort --profile black src/
```

**Comprehensive Linting with pylint**:

```bash
# Lint with pylint
pylint src/

# Score threshold
pylint src/ --fail-under=8.0

# Specific checks
pylint --disable=C,R src/  # Disable convention and refactor
```

### Configuration

**pyproject.toml (ruff)**:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "D",   # pydocstyle
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C90", # mccabe complexity
    "S",   # bandit security
]
ignore = [
    "D203", # one-blank-line-before-class
    "D213", # multi-line-summary-second-line
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "D"]  # Allow assert, ignore docstrings
```

**pyproject.toml (black)**:

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''
```

**pyproject.toml (isort)**:

```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

**.pylintrc**:

```ini
[MASTER]
jobs=0
load-plugins=pylint.extensions.docparams

[MESSAGES CONTROL]
disable=
    C0111,  # missing-docstring
    C0103,  # invalid-name
    R0903,  # too-few-public-methods
max-line-length=100

[DESIGN]
max-args=7
max-attributes=10
max-branches=15
max-locals=20
max-statements=60
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "✨ Gate 3: Code Quality"

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Format with ruff
echo "Formatting code..."
ruff format $STAGED_FILES
ruff check --fix $STAGED_FILES

# Sort imports
isort $STAGED_FILES

# Add formatted files
git add $STAGED_FILES

# Final lint check
ruff check $STAGED_FILES
if [ $? -ne 0 ]; then
    echo "❌ Linting errors found"
    exit 1
fi

echo "✅ Code quality passed"
```

### CI/CD Integration

```yaml
- name: Gate 3 - Code Quality
  run: |
    pip install ruff black isort pylint
    ruff check src/
    black --check src/
    isort --check-only src/
    pylint src/ --fail-under=8.0
```

---

## Gate 4: Security

### Tools

- pip-audit (dependency vulnerability scanner)
- bandit (security linter)
- safety (dependency checker)
- detect-secrets (secret scanner)

### Commands

**Dependency Audit**:

```bash
# pip-audit (recommended)
pip install pip-audit
pip-audit

# With requirements file
pip-audit -r requirements.txt

# Fix vulnerabilities
pip-audit --fix

# safety (alternative)
pip install safety
safety check
safety check --json
```

**Security Scanning with bandit**:

```bash
# Scan all files
bandit -r src/

# High severity only
bandit -r src/ -ll

# Generate report
bandit -r src/ -f json -o bandit-report.json

# Exclude test files
bandit -r src/ --exclude tests/
```

**Secret Detection**:

```bash
# Install detect-secrets
pip install detect-secrets

# Scan for secrets
detect-secrets scan src/

# Create baseline
detect-secrets scan > .secrets.baseline

# Audit findings
detect-secrets audit .secrets.baseline
```

**License Checking**:

```bash
# Install pip-licenses
pip install pip-licenses

# List all licenses
pip-licenses

# Check for specific licenses
pip-licenses --format=json | jq '.[] | select(.License | contains("GPL"))'
```

### Configuration

**pyproject.toml (bandit)**:

```toml
[tool.bandit]
exclude_dirs = ["/tests", "/venv", "/.venv"]
tests = ["B201", "B301"]
skips = ["B101", "B601"]

[tool.bandit.assert_used]
skips = ["*/test_*.py", "*_test.py"]
```

**.secrets.baseline**:

```json
{
  "version": "1.4.0",
  "plugins_used": [
    {
      "name": "ArtifactoryDetector"
    },
    {
      "name": "AWSKeyDetector"
    },
    {
      "name": "Base64HighEntropyString",
      "limit": 4.5
    },
    {
      "name": "BasicAuthDetector"
    },
    {
      "name": "JwtTokenDetector"
    }
  ],
  "results": {},
  "generated_at": "2024-01-15T10:00:00Z"
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🛡️  Gate 4: Security"

# Check for secrets
echo "Scanning for secrets..."
detect-secrets scan --baseline .secrets.baseline
if [ $? -ne 0 ]; then
    echo "⚠️  New secrets detected!"
    exit 1
fi

# Quick dependency check (full audit in CI)
pip-audit --desc on | grep -E "high|critical"
if [ $? -eq 0 ]; then
    echo "❌ Critical/high vulnerabilities found"
    exit 1
fi

# Bandit scan on staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ ! -z "$STAGED_FILES" ]; then
    bandit -ll $STAGED_FILES
fi

echo "✅ Security check passed"
```

### CI/CD Integration

```yaml
- name: Gate 4 - Security
  run: |
    pip install pip-audit bandit safety detect-secrets
    pip-audit --desc
    bandit -r src/ -ll -f json -o bandit-report.json
    detect-secrets scan src/
  continue-on-error: false

- name: Upload Security Report
  uses: actions/upload-artifact@v3
  with:
    name: security-report
    path: bandit-report.json
```

### Security Best Practices

**Environment Variables**:

```python
# Bad - hardcoded secrets
API_KEY = "sk_live_abc123xyz789"

# Good - environment variables
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

**SQL Injection Prevention**:

```python
# Bad - SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good - parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Or use ORM
from sqlalchemy import select
stmt = select(User).where(User.id == user_id)
```

**Input Validation**:

```python
from pydantic import BaseModel, EmailStr, validator

class UserInput(BaseModel):
    email: EmailStr
    age: int

    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v
```

---

## Gate 5: Tests

### Tools

- pytest (testing framework)
- pytest-cov (coverage plugin)
- pytest-xdist (parallel execution)
- hypothesis (property-based testing)

### Commands

**Running Tests**:

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Parallel execution
pytest -n auto

# Specific tests
pytest tests/test_auth.py
pytest tests/test_auth.py::test_login

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

**Coverage**:

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html

# Coverage threshold
pytest --cov=src --cov-fail-under=80

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

**Test Markers**:

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration
```

### Configuration

**pyproject.toml**:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
    "e2e: End-to-end tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🧪 Gate 5: Tests (Quick)"

# Run tests for affected files
CHANGED_DIRS=$(git diff --cached --name-only --diff-filter=ACM | \
    grep '\.py$' | \
    xargs -I {} dirname {} | \
    sort -u)

if [ -z "$CHANGED_DIRS" ]; then
    exit 0
fi

# Run affected tests
pytest --lf --tb=short --no-cov
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "✅ Tests passed"
```

### CI/CD Integration

```yaml
- name: Gate 5 - Tests
  run: |
    pip install pytest pytest-cov pytest-xdist hypothesis
    pytest --cov=src --cov-report=xml --cov-fail-under=80 -n auto

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

### Test Examples

**Unit Test**:

```python
# tests/test_auth.py
import pytest
from src.auth import validate_password, hash_password

class TestAuth:
    def test_validate_password_success(self):
        """Test password validation with valid password."""
        assert validate_password("SecureP@ss123")

    def test_validate_password_too_short(self):
        """Test password validation rejects short passwords."""
        assert not validate_password("short")

    @pytest.mark.parametrize("password", [
        "nouppercasel",
        "NOLOWERCASE",
        "NoDigits",
        "NoSpecial123",
    ])
    def test_validate_password_missing_requirements(self, password):
        """Test password validation for missing requirements."""
        assert not validate_password(password)

    def test_hash_password_different_each_time(self):
        """Test that password hashing produces different hashes."""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
```

**Integration Test with Fixtures**:

```python
# tests/conftest.py
import pytest
from src.database import Database

@pytest.fixture
def db():
    """Create test database."""
    database = Database(":memory:")
    database.create_tables()
    yield database
    database.close()

@pytest.fixture
def test_user(db):
    """Create test user."""
    user = db.create_user(
        email="test@example.com",
        name="Test User"
    )
    return user

# tests/test_integration.py
def test_user_workflow(db, test_user):
    """Test complete user workflow."""
    # Create
    assert test_user.id is not None

    # Read
    user = db.get_user(test_user.id)
    assert user.email == "test@example.com"

    # Update
    db.update_user(test_user.id, name="Updated Name")
    user = db.get_user(test_user.id)
    assert user.name == "Updated Name"

    # Delete
    db.delete_user(test_user.id)
    assert db.get_user(test_user.id) is None
```

**Property-Based Testing with Hypothesis**:

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=100))
def test_calculate_discount(age):
    """Test discount calculation for all valid ages."""
    discount = calculate_discount(age)
    assert 0 <= discount <= 100

@given(st.lists(st.integers()))
def test_sort_is_idempotent(items):
    """Test that sorting twice gives same result."""
    sorted_once = sorted(items)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice
```

---

## Gate 6: Performance

### Tools

- pytest-benchmark (performance testing)
- memory_profiler (memory usage)
- py-spy (sampling profiler)
- locust (load testing)

### Commands

**Benchmarking**:

```bash
# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Compare with previous results
pytest tests/benchmarks/ --benchmark-compare

# Save baseline
pytest tests/benchmarks/ --benchmark-save=baseline

# Memory profiling
python -m memory_profiler src/main.py

# Line-by-line profiling
kernprof -l -v src/main.py
```

**Profiling**:

```bash
# Install py-spy
pip install py-spy

# Profile running process
py-spy top --pid <PID>

# Generate flamegraph
py-spy record -o profile.svg -- python src/main.py

# CPU profiling with cProfile
python -m cProfile -o output.prof src/main.py
python -m pstats output.prof
```

**Load Testing**:

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode
locust -f tests/load/locustfile.py --headless --users 100 --spawn-rate 10
```

### Configuration

**pyproject.toml (pytest-benchmark)**:

```toml
[tool.pytest]
addopts = [
    "--benchmark-min-rounds=5",
    "--benchmark-warmup=on",
]

[tool.pytest.benchmark]
min_rounds = 5
max_time = 1.0
min_time = 0.000005
warmup = true
warmup_iterations = 100000
```

**Benchmark Example**:

```python
# tests/benchmarks/test_performance.py
import pytest

def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def test_fibonacci_performance(benchmark):
    """Benchmark fibonacci calculation."""
    result = benchmark(fibonacci, 20)
    assert result == 6765

@pytest.mark.parametrize("n", [10, 20, 30])
def test_fibonacci_scaling(benchmark, n):
    """Test fibonacci performance scaling."""
    benchmark(fibonacci, n)
```

**Memory Profiling Example**:

```python
# src/main.py
from memory_profiler import profile

@profile
def load_large_dataset():
    """Load and process large dataset."""
    data = []
    for i in range(1000000):
        data.append({"id": i, "value": i * 2})
    return data

if __name__ == "__main__":
    load_large_dataset()
```

**Load Test Example**:

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(1)
    def view_api(self):
        self.client.get("/api/users")

    def on_start(self):
        """Login on start."""
        self.client.post("/login", json={
            "username": "test",
            "password": "test123"
        })
```

### CI/CD Integration

```yaml
- name: Gate 6 - Performance
  run: |
    pip install pytest-benchmark py-spy memory-profiler
    pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json

- name: Upload Performance Report
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: benchmark.json
```

### Performance Optimization Tips

**Caching**:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    """Cache expensive computations."""
    return sum(range(n))
```

**Lazy Evaluation**:

```python
# Generator for memory efficiency
def process_large_file(filename: str):
    """Process large file line by line."""
    with open(filename) as f:
        for line in f:
            yield process_line(line)

# Instead of loading everything
def process_large_file_bad(filename: str):
    with open(filename) as f:
        lines = f.readlines()  # Loads entire file into memory
    return [process_line(line) for line in lines]
```

---

## Gate 7: Accessibility

### Tools

- axe-selenium-python (accessibility testing)
- Flask/Django accessibility middleware
- WCAG validation tools

### Commands

**Accessibility Testing**:

```bash
# Install axe-selenium
pip install axe-selenium-python selenium

# Run accessibility tests
pytest tests/accessibility/
```

### Accessibility Test Example

**tests/accessibility/test_wcag.py**:

```python
from selenium import webdriver
from axe_selenium_python import Axe
import pytest

@pytest.fixture
def driver():
    """Setup Chrome driver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_homepage_accessibility(driver):
    """Test homepage WCAG compliance."""
    driver.get("http://localhost:8000")
    axe = Axe(driver)

    # Run accessibility scan
    axe.inject()
    results = axe.run()

    # Assert no violations
    violations = results["violations"]
    assert len(violations) == 0, f"Found {len(violations)} accessibility violations"

def test_form_accessibility(driver):
    """Test form has proper labels and ARIA."""
    driver.get("http://localhost:8000/form")
    axe = Axe(driver)
    axe.inject()

    # Check specific WCAG tags
    results = axe.run(options={
        "runOnly": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
    })

    assert results["violations"] == []
```

### Flask/Django Accessibility

**Flask Example**:

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    """Homepage with semantic HTML."""
    return render_template("index.html")

# templates/index.html with accessibility
"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessible Web App</title>
</head>
<body>
    <header>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <h1>Welcome</h1>
        <form aria-labelledby="form-heading">
            <h2 id="form-heading">Contact Form</h2>

            <label for="name">Name:</label>
            <input
                type="text"
                id="name"
                name="name"
                required
                aria-required="true"
            />

            <label for="email">Email:</label>
            <input
                type="email"
                id="email"
                name="email"
                required
                aria-required="true"
                aria-describedby="email-help"
            />
            <span id="email-help">We'll never share your email.</span>

            <button type="submit" aria-label="Submit form">Submit</button>
        </form>
    </main>
</body>
</html>
"""
```

### CI/CD Integration

```yaml
- name: Gate 7 - Accessibility
  run: |
    pip install axe-selenium-python selenium
    pytest tests/accessibility/
```

---

## Gate 8: Integration

### Tools

- Docker
- pytest integration tests
- FastAPI/Django test client

### Commands

**Build Verification**:

```bash
# Build Docker image
docker build -t myapp:latest .

# Run container
docker run -d -p 8000:8000 myapp:latest

# Health check
curl -f http://localhost:8000/health
```

**Integration Tests**:

```bash
# Run integration tests
pytest tests/integration/ -v

# With Docker Compose
docker-compose up -d
pytest tests/integration/
docker-compose down
```

### Configuration

**Dockerfile**:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - '8000:8000'
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 10s
      timeout: 5s
      retries: 5

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Integration Test Example

**tests/integration/test_api.py**:

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_user_creation_flow(client):
    """Test complete user creation workflow."""
    # Create user
    response = client.post("/users", json={
        "email": "test@example.com",
        "name": "Test User"
    })
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Get user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

    # Delete user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204
```

### CI/CD Integration

```yaml
- name: Gate 8 - Integration
  run: |
    # Build Docker image
    docker build -t myapp:${{ github.sha }} .

    # Start services
    docker-compose up -d

    # Wait for health check
    timeout 30 bash -c 'until curl -f http://localhost:8000/health; do sleep 1; done'

    # Run integration tests
    pytest tests/integration/ -v

    # Cleanup
    docker-compose down

- name: Push Docker Image
  if: github.ref == 'refs/heads/main'
  run: |
    docker tag myapp:${{ github.sha }} myapp:latest
    docker push myapp:latest
```

---

## Complete Workflow

### Pre-commit Hook (Combined)

**.git/hooks/pre-commit**:

```bash
#!/bin/bash
set -e

echo "🚀 Running Quality Gates..."

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Gate 1: Syntax
echo "🔍 Gate 1: Syntax Validation"
for file in $STAGED_FILES; do
    python -m py_compile "$file"
done

# Gate 2: Types
echo "🔒 Gate 2: Type Safety"
mypy --strict src/

# Gate 3: Lint & Format
echo "✨ Gate 3: Code Quality"
ruff format $STAGED_FILES
ruff check --fix $STAGED_FILES
isort $STAGED_FILES
git add $STAGED_FILES

# Gate 4: Security
echo "🛡️  Gate 4: Security"
detect-secrets scan --baseline .secrets.baseline
bandit -ll $STAGED_FILES

# Gate 5: Tests
echo "🧪 Gate 5: Tests"
pytest --lf --tb=short --no-cov

echo "✅ All quality gates passed!"
```

### Complete CI/CD Pipeline

**.github/workflows/quality-gates.yml**:

```yaml
name: Python Quality Gates

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality-gates:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Gate 1 - Syntax Validation
        run: python -m compileall src/ -q

      - name: Gate 2 - Type Safety
        run: |
          mypy --strict src/
          type-coverage src/ --min-coverage 90

      - name: Gate 3 - Code Quality
        run: |
          ruff check src/
          black --check src/
          isort --check-only src/
          pylint src/ --fail-under=8.0

      - name: Gate 4 - Security
        run: |
          pip-audit
          bandit -r src/ -ll -f json -o bandit-report.json
          detect-secrets scan src/

      - name: Gate 5 - Tests
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=80 -n auto
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

      - name: Gate 6 - Performance
        run: pytest tests/benchmarks/ --benchmark-only

      - name: Gate 7 - Accessibility
        run: pytest tests/accessibility/

      - name: Gate 8 - Integration
        run: |
          docker build -t myapp:test .
          docker-compose up -d
          sleep 10
          pytest tests/integration/ -v
          docker-compose down
```

---

## Summary

This Python quality gate implementation provides:

- **Modern tooling** with ruff, mypy, pytest
- **Comprehensive security** scanning with pip-audit, bandit
- **Type safety** with strict mypy configuration
- **Performance monitoring** with pytest-benchmark
- **Accessibility testing** with axe-selenium-python
- **Production readiness** with Docker integration tests

All gates integrate seamlessly with Python's ecosystem and can be adapted for FastAPI, Django, Flask, or CLI applications.
