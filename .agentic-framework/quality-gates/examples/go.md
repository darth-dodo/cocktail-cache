# Go Quality Gates

## Overview

Language-specific implementation of the 8-step quality gate system for Go projects. Includes practical commands for Go tooling, modern best practices, and performance-focused development.

**Tech Stack**: Go 1.21+, golangci-lint, go test, govulncheck, staticcheck

---

## Gate 1: Syntax Validation

### Tools

- `go build` (compiler)
- `go vet` (static analysis)
- `gofmt` (formatter)

### Commands

**Basic Syntax Check**:

```bash
# Build without creating binary
go build -o /dev/null ./...

# Check all packages
go build ./...

# Verbose output
go build -v ./...

# Cross-compilation check
GOOS=linux GOARCH=amd64 go build ./...
```

**Syntax Verification**:

```bash
# Format check (shows unformatted files)
gofmt -l .

# Vet analysis
go vet ./...

# Check specific package
go vet ./cmd/server
```

**Build Tags and Constraints**:

```bash
# Check build with specific tags
go build -tags=integration ./...

# Check all supported platforms
for GOOS in darwin linux windows; do
    for GOARCH in amd64 arm64; do
        GOOS=$GOOS GOARCH=$GOARCH go build -o /dev/null ./... || echo "Failed: $GOOS/$GOARCH"
    done
done
```

### Configuration

**go.mod**:

```go
module github.com/yourusername/yourproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
)
```

**.golangci.yml** (for linting, used in later gates):

```yaml
run:
  timeout: 5m
  tests: true
  modules-download-mode: readonly

linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - typecheck
    - unused
```

### Pre-commit Hook

**.git/hooks/pre-commit**:

```bash
#!/bin/bash
echo "🔍 Gate 1: Syntax Validation"

# Check formatting
UNFORMATTED=$(gofmt -l .)
if [ -n "$UNFORMATTED" ]; then
    echo "❌ The following files are not formatted:"
    echo "$UNFORMATTED"
    echo "Run: gofmt -w ."
    exit 1
fi

# Build check
go build -o /dev/null ./...
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

# Vet analysis
go vet ./...
if [ $? -ne 0 ]; then
    echo "❌ go vet found issues"
    exit 1
fi

echo "✅ Syntax validation passed"
```

### CI/CD Integration

**.github/workflows/quality-gates.yml**:

```yaml
- name: Gate 1 - Syntax Validation
  run: |
    gofmt -l .
    go build -o /dev/null ./...
    go vet ./...
```

### Common Issues

**Issue**: Import cycle

```bash
# Detect import cycles
go list -f '{{.ImportPath}} {{.Imports}}' ./... | grep -E '\[.*\]'

# Solution: Refactor to break circular dependencies
```

**Issue**: Unused imports

```bash
# Solution: Use goimports to auto-remove
go install golang.org/x/tools/cmd/goimports@latest
goimports -w .
```

---

## Gate 2: Type Safety

### Tools

- Go's built-in type system
- `staticcheck` (advanced static analysis)
- `go vet` (basic checks)

### Commands

**Type Checking**:

```bash
# Go's compiler is the type checker
go build -o /dev/null ./...

# Static analysis
staticcheck ./...

# Check for common mistakes
go vet ./...
```

**Advanced Static Analysis**:

```bash
# Install staticcheck
go install honnef.co/go/tools/cmd/staticcheck@latest

# Run analysis
staticcheck ./...

# Check specific issues
staticcheck -checks SA1019 ./...  # Check deprecated usage
```

**Nil Safety**:

```bash
# Install nilaway for nil safety
go install go.uber.org/nilaway/cmd/nilaway@latest

# Run nil analysis
nilaway ./...
```

### Configuration

**staticcheck.conf**:

```toml
checks = ["all", "-ST1000", "-ST1003"]
initialisms = ["ACL", "API", "ASCII", "CPU", "CSS", "DNS", "EOF", "GUID", "HTML", "HTTP", "HTTPS", "ID", "IP", "JSON", "LHS", "QPS", "RAM", "RHS", "RPC", "SLA", "SMTP", "SQL", "SSH", "TCP", "TLS", "TTL", "UDP", "UI", "UID", "UUID", "URI", "URL", "UTF8", "VM", "XML", "XMPP", "XSRF", "XSS"]
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🔒 Gate 2: Type Safety"

# Static analysis
staticcheck ./...
if [ $? -ne 0 ]; then
    echo "❌ Static analysis found issues"
    exit 1
fi

# Nil safety check
if command -v nilaway &> /dev/null; then
    nilaway ./...
    if [ $? -ne 0 ]; then
        echo "⚠️  Nil safety issues found"
    fi
fi

echo "✅ Type safety passed"
```

### CI/CD Integration

```yaml
- name: Gate 2 - Type Safety
  run: |
    go install honnef.co/go/tools/cmd/staticcheck@latest
    staticcheck ./...
```

### Type Safety Examples

**Interfaces and Type Assertions**:

```go
// Good: Type assertion with check
func processValue(v interface{}) error {
    str, ok := v.(string)
    if !ok {
        return fmt.Errorf("expected string, got %T", v)
    }
    // Use str safely
    return nil
}

// Better: Use type switch
func processValue(v interface{}) error {
    switch val := v.(type) {
    case string:
        // Handle string
        return nil
    case int:
        // Handle int
        return nil
    default:
        return fmt.Errorf("unexpected type: %T", val)
    }
}
```

**Pointer Safety**:

```go
// Good: Check for nil
func getUserName(user *User) string {
    if user == nil {
        return "Guest"
    }
    return user.Name
}

// Better: Use pointer receivers appropriately
type User struct {
    Name string
}

// Value receiver for methods that don't modify
func (u User) GetName() string {
    return u.Name
}

// Pointer receiver for methods that modify
func (u *User) SetName(name string) {
    u.Name = name
}
```

---

## Gate 3: Code Quality (Lint)

### Tools

- `golangci-lint` (meta-linter)
- `gofmt` / `gofumpt` (formatting)
- `goimports` (import management)

### Commands

**Linting**:

```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run all linters
golangci-lint run

# Run with auto-fix
golangci-lint run --fix

# Specific linters
golangci-lint run --enable=gocyclo --enable=gocognit

# Fast mode (cache enabled)
golangci-lint run --fast
```

**Formatting**:

```bash
# Format all files
gofmt -w .

# Or use gofumpt (stricter)
go install mvdan.cc/gofumpt@latest
gofumpt -w .

# Organize imports
goimports -w .
```

**Complexity Analysis**:

```bash
# Install gocyclo
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest

# Check complexity (threshold: 15)
gocyclo -over 15 .

# Cognitive complexity
go install github.com/uudashr/gocognit/cmd/gocognit@latest
gocognit -over 15 .
```

### Configuration

**.golangci.yml**:

```yaml
run:
  timeout: 5m
  tests: true
  skip-dirs:
    - vendor
    - mocks
  modules-download-mode: readonly

linters:
  enable:
    - errcheck # Check error handling
    - gosimple # Simplify code
    - govet # Vet examination
    - ineffassign # Detect ineffectual assignments
    - staticcheck # Static analysis
    - typecheck # Type checking
    - unused # Check unused code
    - gocyclo # Cyclomatic complexity
    - gocognit # Cognitive complexity
    - gofmt # Format checking
    - goimports # Import management
    - misspell # Spell checking
    - gocritic # Comprehensive checks
    - revive # Fast, configurable linter
    - gosec # Security issues
    - bodyclose # HTTP response body close
    - noctx # HTTP requests without context
    - rowserrcheck # SQL rows error check
    - sqlclosecheck # SQL Close check
    - unparam # Unused function parameters
    - unconvert # Unnecessary conversions

  disable:
    - exhaustive # Can be too strict
    - funlen # Function length (subjective)
    - gochecknoglobals # Allow some globals

linters-settings:
  gocyclo:
    min-complexity: 15

  gocognit:
    min-complexity: 20

  gocritic:
    enabled-tags:
      - diagnostic
      - performance
      - style
    disabled-checks:
      - ifElseChain
      - singleCaseSwitch

  revive:
    rules:
      - name: var-naming
        severity: warning
      - name: exported
        severity: warning

issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - gocyclo
        - errcheck
        - gosec
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "✨ Gate 3: Code Quality"

# Format code
gofumpt -w .
goimports -w .

# Add formatted files
git add -u

# Run linter
golangci-lint run --fix
if [ $? -ne 0 ]; then
    echo "❌ Linting errors found"
    exit 1
fi

# Re-add fixed files
git add -u

echo "✅ Code quality passed"
```

### CI/CD Integration

```yaml
- name: Gate 3 - Code Quality
  run: |
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
    golangci-lint run --timeout=5m
```

### Code Quality Examples

**Error Handling**:

```go
// Bad: Ignoring errors
data, _ := ioutil.ReadFile("file.txt")

// Good: Handling errors
data, err := os.ReadFile("file.txt")
if err != nil {
    return fmt.Errorf("reading file: %w", err)
}
```

**Simplification**:

```go
// Bad: Unnecessary complexity
if condition == true {
    return true
} else {
    return false
}

// Good: Simplified
return condition
```

---

## Gate 4: Security

### Tools

- `gosec` (security scanner)
- `govulncheck` (vulnerability scanner)
- `nancy` (dependency checker)

### Commands

**Security Scanning**:

```bash
# Install gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Scan all packages
gosec ./...

# JSON output
gosec -fmt=json -out=gosec-report.json ./...

# Exclude test files
gosec -exclude-dir=tests ./...
```

**Vulnerability Checking**:

```bash
# Install govulncheck
go install golang.org/x/vuln/cmd/govulncheck@latest

# Check for vulnerabilities
govulncheck ./...

# JSON output
govulncheck -json ./...
```

**Dependency Audit**:

```bash
# Install nancy
go install github.com/sonatype-nexus-community/nancy@latest

# Check dependencies
go list -json -m all | nancy sleuth

# Check with go mod
go mod verify
```

**Secret Detection**:

```bash
# Install gitleaks
brew install gitleaks  # macOS
# or download from: https://github.com/gitleaks/gitleaks

# Scan for secrets
gitleaks detect --source . --verbose
```

### Configuration

**.gosec.json**:

```json
{
  "global": {
    "nosec": false,
    "audit": true
  },
  "severity": "medium",
  "confidence": "medium",
  "exclude": ["G104", "G304"],
  "exclude-dirs": ["vendor", "testdata"]
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🛡️  Gate 4: Security"

# Check for secrets
if command -v gitleaks &> /dev/null; then
    gitleaks detect --source . --no-git
    if [ $? -ne 0 ]; then
        echo "❌ Secrets detected!"
        exit 1
    fi
fi

# Security scan
gosec -exclude-dir=tests ./...
if [ $? -ne 0 ]; then
    echo "❌ Security issues found"
    exit 1
fi

echo "✅ Security check passed"
```

### CI/CD Integration

```yaml
- name: Gate 4 - Security
  run: |
    go install github.com/securego/gosec/v2/cmd/gosec@latest
    go install golang.org/x/vuln/cmd/govulncheck@latest

    gosec -fmt=json -out=gosec-report.json ./...
    govulncheck ./...

- name: Upload Security Report
  uses: actions/upload-artifact@v3
  with:
    name: security-report
    path: gosec-report.json
```

### Security Best Practices

**SQL Injection Prevention**:

```go
// Bad: SQL injection risk
query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)
db.Query(query)

// Good: Parameterized query
query := "SELECT * FROM users WHERE id = ?"
db.Query(query, userID)
```

**Secrets Management**:

```go
// Bad: Hardcoded credentials (NEVER DO THIS)
const apiKey = "DO-NOT-HARDCODE-KEYS"

// Good: Environment variables
func getAPIKey() (string, error) {
    key := os.Getenv("API_KEY")
    if key == "" {
        return "", errors.New("API_KEY not set")
    }
    return key, nil
}
```

**Input Validation**:

```go
import "regexp"

func validateEmail(email string) error {
    emailRegex := regexp.MustCompile(`^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,4}$`)
    if !emailRegex.MatchString(email) {
        return errors.New("invalid email format")
    }
    return nil
}
```

---

## Gate 5: Tests

### Tools

- `go test` (built-in testing)
- `testify` (assertion library)
- `gotestsum` (test runner with better output)
- `go-fuzz` (fuzzing)

### Commands

**Running Tests**:

```bash
# Run all tests
go test ./...

# With coverage
go test -cover ./...
go test -coverprofile=coverage.out ./...

# View coverage in browser
go tool cover -html=coverage.out

# Verbose output
go test -v ./...

# Parallel execution
go test -parallel=4 ./...

# Run specific test
go test -run TestUserLogin ./...

# Short mode (skip long tests)
go test -short ./...
```

**Test Coverage**:

```bash
# Generate coverage
go test -coverprofile=coverage.out ./...

# Coverage by package
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out

# Fail if coverage below threshold
go test -cover ./... | grep -E 'coverage: [0-9]+' | \
    awk '{if ($2 < 80) exit 1}'
```

**Benchmarking**:

```bash
# Run benchmarks
go test -bench=. ./...

# With memory stats
go test -bench=. -benchmem ./...

# CPU profiling
go test -bench=. -cpuprofile=cpu.prof ./...
go tool pprof cpu.prof
```

**Test with Race Detector**:

```bash
# Detect race conditions
go test -race ./...
```

### Configuration

**Test Files**:

```go
// user_test.go
package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUserCreation(t *testing.T) {
    user := NewUser("test@example.com", "Test User")

    assert.NotNil(t, user)
    assert.Equal(t, "test@example.com", user.Email)
    assert.Equal(t, "Test User", user.Name)
}

func TestUserValidation(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid email", "test@example.com", false},
        {"invalid email", "invalid", true},
        {"empty email", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validateEmail(tt.email)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

**Benchmark Example**:

```go
func BenchmarkUserCreation(b *testing.B) {
    for i := 0; i < b.N; i++ {
        NewUser("test@example.com", "Test User")
    }
}

func BenchmarkConcurrentAccess(b *testing.B) {
    cache := NewCache()

    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            cache.Get("key")
        }
    })
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🧪 Gate 5: Tests"

# Run tests with race detector
go test -race -short ./...
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
    go test -race -coverprofile=coverage.out -covermode=atomic ./...
    go tool cover -func=coverage.out

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.out
```

### Test Examples

**Table-Driven Tests**:

```go
func TestCalculateDiscount(t *testing.T) {
    tests := []struct {
        name     string
        price    float64
        discount float64
        want     float64
    }{
        {"no discount", 100, 0, 100},
        {"10% discount", 100, 10, 90},
        {"50% discount", 200, 50, 100},
        {"full discount", 50, 100, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := calculateDiscount(tt.price, tt.discount)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

**Mock Testing**:

```go
// Using testify/mock
type MockDatabase struct {
    mock.Mock
}

func (m *MockDatabase) GetUser(id int) (*User, error) {
    args := m.Called(id)
    return args.Get(0).(*User), args.Error(1)
}

func TestUserService(t *testing.T) {
    mockDB := new(MockDatabase)
    service := NewUserService(mockDB)

    // Setup expectations
    mockDB.On("GetUser", 1).Return(&User{ID: 1, Name: "Test"}, nil)

    // Test
    user, err := service.GetUser(1)

    // Verify
    assert.NoError(t, err)
    assert.Equal(t, 1, user.ID)
    mockDB.AssertExpectations(t)
}
```

---

## Gate 6: Performance

### Tools

- `go test -bench` (benchmarking)
- `pprof` (profiling)
- `go-torch` (flame graphs)
- `vegeta` (load testing)

### Commands

**Benchmarking**:

```bash
# Run benchmarks
go test -bench=. -benchmem ./...

# Compare benchmarks
go install golang.org/x/perf/cmd/benchstat@latest
go test -bench=. -count=5 | tee old.txt
# make changes
go test -bench=. -count=5 | tee new.txt
benchstat old.txt new.txt
```

**CPU Profiling**:

```bash
# Profile tests
go test -cpuprofile=cpu.prof -bench=. ./...

# Analyze profile
go tool pprof cpu.prof
# Commands: top, list, web

# Memory profiling
go test -memprofile=mem.prof -bench=. ./...
go tool pprof mem.prof
```

**Live Profiling**:

```go
import (
    _ "net/http/pprof"
    "net/http"
)

func main() {
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()
    // Your application code
}

// Access profiles at:
// http://localhost:6060/debug/pprof/
```

**Load Testing with vegeta**:

```bash
# Install vegeta
go install github.com/tsenart/vegeta@latest

# Load test
echo "GET http://localhost:8080/" | vegeta attack -duration=30s -rate=100 | vegeta report

# Custom targets
cat targets.txt | vegeta attack -duration=30s | vegeta report
```

### Configuration

**Benchmark Example**:

```go
// search_bench_test.go
func BenchmarkLinearSearch(b *testing.B) {
    data := generateData(10000)
    target := 5000

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        linearSearch(data, target)
    }
}

func BenchmarkBinarySearch(b *testing.B) {
    data := generateData(10000)
    target := 5000

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        binarySearch(data, target)
    }
}

// Memory allocation benchmark
func BenchmarkStringConcat(b *testing.B) {
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        var s string
        for j := 0; j < 100; j++ {
            s += "a"
        }
    }
}

func BenchmarkStringBuilder(b *testing.B) {
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        var b strings.Builder
        for j := 0; j < 100; j++ {
            b.WriteString("a")
        }
        _ = b.String()
    }
}
```

**vegeta targets.txt**:

```
GET http://localhost:8080/api/users
GET http://localhost:8080/api/products
POST http://localhost:8080/api/orders
Content-Type: application/json
@./testdata/order.json
```

### CI/CD Integration

```yaml
- name: Gate 6 - Performance
  run: |
    go test -bench=. -benchmem ./... > bench.txt
    go install golang.org/x/perf/cmd/benchstat@latest

- name: Upload Benchmark Results
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-results
    path: bench.txt
```

### Performance Optimization Tips

**Avoid Allocations**:

```go
// Bad: Allocates on every call
func concat(a, b string) string {
    return a + b
}

// Good: Use strings.Builder for multiple concatenations
func concatMany(strs []string) string {
    var b strings.Builder
    for _, s := range strs {
        b.WriteString(s)
    }
    return b.String()
}
```

**Use sync.Pool for Frequent Allocations**:

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processData(data []byte) []byte {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer bufferPool.Put(buf)

    buf.Reset()
    buf.Write(data)
    // process buffer
    return buf.Bytes()
}
```

---

## Gate 7: Accessibility

For Go web applications (not applicable to CLI/backend only):

### Tools

- axe-core (JavaScript accessibility testing)
- pa11y (automated accessibility testing)

### Commands

**Automated Testing**:

```bash
# Install pa11y
npm install -g pa11y

# Test URL
pa11y http://localhost:8080

# Test with specific standard
pa11y --standard WCAG2AA http://localhost:8080

# Generate report
pa11y --reporter json http://localhost:8080 > a11y-report.json
```

### Go Web Example with Accessibility

```go
// main.go
package main

import (
    "html/template"
    "net/http"
)

type Page struct {
    Title   string
    Content string
}

func main() {
    http.HandleFunc("/", homeHandler)
    http.ListenAndServe(":8080", nil)
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
    tmpl := template.Must(template.ParseFiles("templates/home.html"))

    page := Page{
        Title:   "Accessible Web App",
        Content: "Welcome to our accessible application",
    }

    tmpl.Execute(w, page)
}
```

**templates/home.html**:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{.Title}}</title>
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
      <h1>{{.Title}}</h1>
      <p>{{.Content}}</p>

      <form aria-labelledby="contact-heading">
        <h2 id="contact-heading">Contact Form</h2>

        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required aria-required="true" />

        <button type="submit" aria-label="Submit form">Submit</button>
      </form>
    </main>
  </body>
</html>
```

### CI/CD Integration

```yaml
- name: Gate 7 - Accessibility
  run: |
    go run main.go &
    APP_PID=$!
    sleep 3

    npm install -g pa11y
    pa11y --standard WCAG2AA http://localhost:8080

    kill $APP_PID
```

---

## Gate 8: Integration

### Tools

- Docker
- docker-compose
- Go integration tests

### Commands

**Build Verification**:

```bash
# Build binary
go build -o app ./cmd/server

# Build with optimization
go build -ldflags="-s -w" -o app ./cmd/server

# Cross-compile
GOOS=linux GOARCH=amd64 go build -o app-linux ./cmd/server
```

**Docker Build**:

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -d -p 8080:8080 myapp:latest

# Health check
curl -f http://localhost:8080/health
```

**Integration Tests**:

```bash
# Run integration tests
go test -tags=integration ./tests/integration/...

# With docker-compose
docker-compose up -d
go test -tags=integration ./tests/integration/...
docker-compose down
```

### Configuration

**Dockerfile (Multi-stage)**:

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-s -w" -o app ./cmd/server

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy binary from builder
COPY --from=builder /app/app .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["./app"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - '8080:8080'
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    healthcheck:
      test: ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost:8080/health']
      interval: 10s
      timeout: 5s
      retries: 5

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Integration Test Example

**tests/integration/api_test.go**:

```go
//go:build integration
// +build integration

package integration

import (
    "net/http"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestHealthEndpoint(t *testing.T) {
    client := &http.Client{Timeout: 5 * time.Second}

    resp, err := client.Get("http://localhost:8080/health")
    require.NoError(t, err)
    defer resp.Body.Close()

    assert.Equal(t, http.StatusOK, resp.StatusCode)
}

func TestUserCreationWorkflow(t *testing.T) {
    client := &http.Client{Timeout: 5 * time.Second}

    // Create user
    createResp := createUser(t, client, map[string]string{
        "email": "test@example.com",
        "name":  "Test User",
    })
    assert.Equal(t, http.StatusCreated, createResp.StatusCode)

    // Verify user exists
    getResp := getUser(t, client, "test@example.com")
    assert.Equal(t, http.StatusOK, getResp.StatusCode)
}
```

### CI/CD Integration

```yaml
- name: Gate 8 - Integration
  run: |
    # Build binary
    go build -o app ./cmd/server

    # Build Docker image
    docker build -t myapp:${{ github.sha }} .

    # Start services
    docker-compose up -d

    # Wait for health check
    timeout 30 bash -c 'until curl -f http://localhost:8080/health; do sleep 1; done'

    # Run integration tests
    go test -v -tags=integration ./tests/integration/...

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

# Gate 1: Syntax
echo "🔍 Gate 1: Syntax Validation"
gofmt -l .
go build -o /dev/null ./...
go vet ./...

# Gate 2: Types
echo "🔒 Gate 2: Type Safety"
staticcheck ./...

# Gate 3: Lint
echo "✨ Gate 3: Code Quality"
gofumpt -w .
goimports -w .
git add -u
golangci-lint run --fix

# Gate 4: Security
echo "🛡️  Gate 4: Security"
gosec -exclude-dir=tests ./...

# Gate 5: Tests
echo "🧪 Gate 5: Tests"
go test -race -short ./...

echo "✅ All quality gates passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Complete CI/CD Pipeline

**.github/workflows/quality-gates.yml**:

```yaml
name: Go Quality Gates

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

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
          cache: true

      - name: Download Dependencies
        run: go mod download

      - name: Gate 1 - Syntax Validation
        run: |
          gofmt -l .
          go build -o /dev/null ./...
          go vet ./...

      - name: Gate 2 - Type Safety
        run: |
          go install honnef.co/go/tools/cmd/staticcheck@latest
          staticcheck ./...

      - name: Gate 3 - Code Quality
        run: |
          go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
          golangci-lint run --timeout=5m

      - name: Gate 4 - Security
        run: |
          go install github.com/securego/gosec/v2/cmd/gosec@latest
          go install golang.org/x/vuln/cmd/govulncheck@latest
          gosec -fmt=json -out=gosec-report.json ./...
          govulncheck ./...

      - name: Upload Security Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: gosec-report.json

      - name: Gate 5 - Tests
        run: |
          go test -race -coverprofile=coverage.out -covermode=atomic ./...
          go tool cover -func=coverage.out
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost/test
          REDIS_URL: redis://localhost:6379

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out

      - name: Gate 6 - Performance
        run: go test -bench=. -benchmem ./...

      - name: Gate 8 - Integration
        run: |
          go build -o app ./cmd/server
          docker build -t myapp:test .
          docker-compose up -d
          sleep 10
          go test -v -tags=integration ./tests/integration/...
          docker-compose down
```

---

## Summary

This Go quality gate implementation provides:

- **Native tooling** with go test, go vet, gofmt
- **Advanced linting** with golangci-lint
- **Security scanning** with gosec and govulncheck
- **Performance testing** with built-in benchmarking and pprof
- **Type safety** with staticcheck
- **Production readiness** with Docker multi-stage builds

All gates integrate seamlessly with Go's ecosystem and follow Go best practices for high-performance, reliable applications.
