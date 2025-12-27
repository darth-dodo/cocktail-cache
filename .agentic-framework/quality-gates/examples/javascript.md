# JavaScript/TypeScript Quality Gates

## Overview

Language-specific implementation of the 8-step quality gate system for JavaScript and TypeScript projects. Includes practical commands for npm/pnpm, modern tooling, and web-specific validations.

**Tech Stack**: Node.js, TypeScript, ESLint, Vitest, Playwright, Lighthouse

---

## Gate 1: Syntax Validation

### Tools

- TypeScript Compiler (`tsc`)
- Node.js native parser
- ESLint parser

### Commands

**TypeScript Projects**:

```bash
# Check syntax without emitting files
tsc --noEmit

# Check specific files
tsc --noEmit src/index.ts

# Watch mode for development
tsc --noEmit --watch

# Check with project config
tsc --noEmit --project tsconfig.json
```

**JavaScript Projects**:

```bash
# Use Node.js to check syntax
node --check src/index.js

# Check all JavaScript files
find src -name "*.js" -exec node --check {} \;

# ESLint can also catch syntax errors
eslint --no-eslintrc --parser-options=ecmaVersion:2022 src/
```

### Configuration

**tsconfig.json**:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": false,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Pre-commit Hook

**.git/hooks/pre-commit**:

```bash
#!/bin/bash
echo "🔍 Gate 1: Syntax Validation"

# Get staged TypeScript/JavaScript files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx)$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# TypeScript syntax check
if command -v tsc &> /dev/null; then
    echo "Checking TypeScript syntax..."
    tsc --noEmit
    if [ $? -ne 0 ]; then
        echo "❌ TypeScript syntax errors found"
        exit 1
    fi
fi

echo "✅ Syntax validation passed"
```

### CI/CD Integration

**.github/workflows/quality-gates.yml**:

```yaml
- name: Gate 1 - Syntax Validation
  run: |
    npm ci
    npx tsc --noEmit
```

### Common Issues

**Issue**: Module not found

```bash
# Check imports
npx tsc --traceResolution | grep "Module not found"

# Verify package installation
npm list <package-name>
npm install <package-name>
```

**Issue**: JSX syntax errors

```bash
# Ensure proper TypeScript config
# tsconfig.json: "jsx": "react-jsx" or "jsx": "preserve"
npx tsc --jsx react-jsx --noEmit
```

---

## Gate 2: Type Safety

### Tools

- TypeScript Compiler (`tsc`)
- ts-prune (find unused exports)
- typescript-eslint (type-aware linting)

### Commands

**Type Checking**:

```bash
# Strict type checking
tsc --strict --noEmit

# Type checking with specific flags
tsc --noEmit --noImplicitAny --strictNullChecks

# Check specific files
tsc --noEmit src/**/*.ts

# Generate declaration files to verify types
tsc --declaration --emitDeclarationOnly
```

**Find Type Issues**:

```bash
# Find unused exports
npx ts-prune

# Find any types
grep -r "any" src/ --include="*.ts" --include="*.tsx"

# Type coverage report
npx type-coverage --detail
```

### Configuration

**tsconfig.json (Strict)**:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🔒 Gate 2: Type Safety"

# Run TypeScript in strict mode
npx tsc --strict --noEmit
if [ $? -ne 0 ]; then
    echo "❌ Type errors found"
    exit 1
fi

# Check type coverage
TYPE_COVERAGE=$(npx type-coverage --at-least 95 2>&1)
if [ $? -ne 0 ]; then
    echo "⚠️  Type coverage below 95%"
    echo "$TYPE_COVERAGE"
fi

echo "✅ Type safety passed"
```

### CI/CD Integration

```yaml
- name: Gate 2 - Type Safety
  run: |
    npx tsc --strict --noEmit
    npx type-coverage --at-least 95
```

### Common Issues

**Issue**: Implicit any types

```bash
# Find all implicit any
npx tsc --noImplicitAny --noEmit 2>&1 | grep "implicitly has an 'any' type"

# Solution: Add explicit types
function processData(data: unknown): ProcessedData {
  // Type guard
  if (typeof data === 'object' && data !== null) {
    return data as ProcessedData;
  }
  throw new Error('Invalid data');
}
```

**Issue**: Null/undefined errors

```bash
# Solution: Use optional chaining and nullish coalescing
const value = user?.profile?.name ?? 'Unknown';

# Or explicit checks
if (user && user.profile && user.profile.name) {
  console.log(user.profile.name);
}
```

---

## Gate 3: Code Quality (Lint)

### Tools

- ESLint
- Prettier
- eslint-plugin-import
- eslint-plugin-jsx-a11y (React)

### Commands

**Linting**:

```bash
# Lint all files
npm run lint
npx eslint src/

# Lint with auto-fix
npm run lint -- --fix
npx eslint src/ --fix

# Lint specific files
npx eslint src/components/**/*.tsx

# Check for unused imports/exports
npx eslint --report-unused-disable-directives src/
```

**Formatting**:

```bash
# Check formatting
npx prettier --check src/

# Auto-format
npx prettier --write src/

# Format specific files
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"
```

**Complexity Analysis**:

```bash
# ESLint complexity rule
npx eslint --rule 'complexity: [error, 10]' src/

# TypeScript ESLint complexity
npx eslint --rule '@typescript-eslint/complexity: [error, 15]' src/
```

### Configuration

**package.json scripts**:

```json
{
  "scripts": {
    "lint": "eslint src/ --ext .ts,.tsx,.js,.jsx",
    "lint:fix": "eslint src/ --ext .ts,.tsx,.js,.jsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json,css}\""
  }
}
```

**eslint.config.js** (Flat Config):

```javascript
import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import prettier from 'eslint-config-prettier';

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: './tsconfig.json',
      },
    },
    plugins: {
      '@typescript-eslint': typescript,
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
        },
      ],
      complexity: ['error', 15],
      'max-lines-per-function': ['warn', 50],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
  prettier,
];
```

**.prettierrc**:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always"
}
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "✨ Gate 3: Code Quality"

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx)$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Format files
echo "Formatting files..."
npx prettier --write $STAGED_FILES
git add $STAGED_FILES

# Lint files
echo "Linting files..."
npx eslint $STAGED_FILES --fix
if [ $? -ne 0 ]; then
    echo "❌ Linting errors found. Some may require manual fixes."
    exit 1
fi

# Re-add fixed files
git add $STAGED_FILES

echo "✅ Code quality passed"
```

### CI/CD Integration

```yaml
- name: Gate 3 - Code Quality
  run: |
    npm run format:check
    npm run lint -- --max-warnings 0
```

---

## Gate 4: Security

### Tools

- npm audit / pnpm audit
- Snyk
- ESLint security plugins
- git-secrets

### Commands

**Dependency Audit**:

```bash
# npm
npm audit
npm audit --audit-level=moderate
npm audit fix

# pnpm
pnpm audit
pnpm audit --fix

# Detailed report
npm audit --json > audit-report.json
```

**Security Scanning**:

```bash
# Snyk (requires snyk CLI)
npx snyk test
npx snyk test --severity-threshold=high

# Check for known vulnerabilities
npx snyk monitor

# License compliance
npx license-checker --summary
```

**Secret Detection**:

```bash
# git-secrets
git secrets --scan
git secrets --scan-history

# Detect hardcoded secrets
grep -r "API_KEY\|SECRET\|PASSWORD" src/ --include="*.ts" --include="*.js"

# Check .env files not committed
git ls-files | grep "\.env$"
```

**Security Linting**:

```bash
# ESLint security plugin
npm install --save-dev eslint-plugin-security
npx eslint --plugin security src/
```

### Configuration

**package.json**:

```json
{
  "scripts": {
    "audit": "npm audit --audit-level=moderate",
    "audit:fix": "npm audit fix",
    "security": "npx snyk test",
    "licenses": "npx license-checker --summary"
  }
}
```

**eslint.config.js (Security)**:

```javascript
import security from 'eslint-plugin-security';

export default [
  {
    plugins: {
      security,
    },
    rules: {
      'security/detect-object-injection': 'warn',
      'security/detect-non-literal-regexp': 'warn',
      'security/detect-unsafe-regex': 'error',
      'security/detect-buffer-noassert': 'error',
      'security/detect-child-process': 'warn',
      'security/detect-disable-mustache-escape': 'error',
      'security/detect-eval-with-expression': 'error',
      'security/detect-no-csrf-before-method-override': 'error',
      'security/detect-possible-timing-attacks': 'warn',
    },
  },
];
```

**.gitignore**:

```
# Environment variables
.env
.env.local
.env.*.local

# Secrets
*.pem
*.key
secrets/

# Dependency vulnerabilities
npm-audit.json
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🛡️  Gate 4: Security"

# Check for secrets in staged files
echo "Scanning for secrets..."
STAGED_FILES=$(git diff --cached --name-only)
for file in $STAGED_FILES; do
    if grep -qE "(api[_-]?key|secret|password|token).*=.*['\"][^'\"]+['\"]" "$file" 2>/dev/null; then
        echo "⚠️  Potential secret found in $file"
        grep -nE "(api[_-]?key|secret|password|token).*=.*['\"][^'\"]+['\"]" "$file"
    fi
done

# Quick dependency check
echo "Checking dependencies..."
npm audit --audit-level=high --production
if [ $? -ne 0 ]; then
    echo "❌ High severity vulnerabilities found"
    exit 1
fi

echo "✅ Security check passed"
```

### CI/CD Integration

```yaml
- name: Gate 4 - Security
  run: |
    npm audit --audit-level=moderate
    npx snyk test --severity-threshold=high
    npx license-checker --failOn "GPL;AGPL"
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Common Issues

**Issue**: Vulnerable dependencies

```bash
# Check for updates
npm outdated

# Update to secure version
npm install package@latest

# If no fix available, use overrides (npm 8.3+)
# package.json
{
  "overrides": {
    "vulnerable-package": "^2.0.0"
  }
}
```

**Issue**: Secrets in code

```bash
# Solution: Use environment variables
# .env (DO NOT COMMIT)
API_KEY=your-secret-key

# src/config.ts
export const config = {
  apiKey: process.env.VITE_API_KEY || '',
};
```

---

## Gate 5: Tests

### Tools

- Vitest (unit/integration)
- Playwright (E2E)
- @testing-library/react (component testing)
- c8 / istanbul (coverage)

### Commands

**Unit Tests (Vitest)**:

```bash
# Run all tests
npm test
npx vitest run

# Watch mode
npm test -- --watch
npx vitest

# Coverage
npm run test:coverage
npx vitest run --coverage

# Specific tests
npx vitest src/utils
npx vitest src/utils/auth.test.ts
```

**E2E Tests (Playwright)**:

```bash
# Run E2E tests
npm run test:e2e
npx playwright test

# Headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug

# Specific browser
npx playwright test --project=chromium
```

**Component Tests**:

```bash
# React Testing Library
npx vitest run src/components/

# Generate coverage for components
npx vitest run --coverage src/components/
```

### Configuration

**package.json**:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

**vitest.config.ts**:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'c8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/', '**/*.d.ts', '**/*.config.*', '**/mockData/'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
      },
    },
  },
});
```

**playwright.config.ts**:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Pre-commit Hook

```bash
#!/bin/bash
echo "🧪 Gate 5: Tests (Quick)"

# Run tests for affected files only
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$')

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

# Run tests in affected directories
npx vitest run --changed HEAD
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
    # Unit and integration tests
    npm run test:coverage

    # E2E tests
    npx playwright install --with-deps
    npm run test:e2e

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/coverage-final.json
```

### Example Tests

**Unit Test (Vitest)**:

```typescript
// src/utils/auth.test.ts
import { describe, it, expect } from 'vitest';
import { validateToken } from './auth';

describe('validateToken', () => {
  it('should return true for valid token', () => {
    const token = 'valid-token-123';
    expect(validateToken(token)).toBe(true);
  });

  it('should return false for invalid token', () => {
    expect(validateToken('')).toBe(false);
    expect(validateToken(null)).toBe(false);
  });
});
```

**Component Test (React Testing Library)**:

```typescript
// src/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('should render with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('should call onClick handler', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

**E2E Test (Playwright)**:

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'invalid@example.com');
    await page.fill('[name="password"]', 'wrong');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });
});
```

---

## Gate 6: Performance

### Tools

- Vite build analyzer
- Lighthouse CI
- Vitest benchmark
- webpack-bundle-analyzer (if using webpack)

### Commands

**Bundle Analysis**:

```bash
# Vite
npm run build
npx vite-bundle-visualizer

# Webpack
npx webpack-bundle-analyzer dist/stats.json

# Check bundle size
npm run build
du -sh dist/
```

**Lighthouse**:

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Run audit
lhci autorun

# Single URL
lighthouse https://example.com --view
lighthouse https://example.com --only-categories=performance
```

**Performance Benchmarks**:

```bash
# Vitest benchmarks
npx vitest bench
```

### Configuration

**package.json**:

```json
{
  "scripts": {
    "build": "vite build",
    "build:analyze": "vite-bundle-visualizer",
    "perf:lighthouse": "lhci autorun",
    "perf:bench": "vitest bench"
  }
}
```

**vite.config.ts**:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
});
```

**lighthouserc.json**:

```json
{
  "ci": {
    "collect": {
      "startServerCommand": "npm run preview",
      "url": ["http://localhost:4173/"],
      "numberOfRuns": 3
    },
    "assert": {
      "preset": "lighthouse:recommended",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "first-contentful-paint": ["warn", { "maxNumericValue": 2000 }],
        "interactive": ["warn", { "maxNumericValue": 3500 }],
        "speed-index": ["warn", { "maxNumericValue": 3000 }]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

### Benchmark Example

**src/utils/search.bench.ts**:

```typescript
import { bench, describe } from 'vitest';
import { searchUsers } from './search';

describe('Search performance', () => {
  const users = Array.from({ length: 10000 }, (_, i) => ({
    id: i,
    name: `User ${i}`,
  }));

  bench('linear search', () => {
    searchUsers(users, 'User 5000');
  });

  bench('binary search', () => {
    searchUsersBinary(users, 'User 5000');
  });
});
```

### CI/CD Integration

```yaml
- name: Gate 6 - Performance
  run: |
    # Build and analyze bundle
    npm run build
    npx vite-bundle-visualizer --json > bundle-analysis.json

    # Check bundle size
    BUNDLE_SIZE=$(du -sm dist/ | cut -f1)
    if [ $BUNDLE_SIZE -gt 5 ]; then
      echo "Bundle size exceeds 5MB: ${BUNDLE_SIZE}MB"
      exit 1
    fi

    # Run Lighthouse
    npm run perf:lighthouse

- name: Upload Performance Report
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: |
      .lighthouseci/
      bundle-analysis.json
```

### Performance Optimization Tips

**Code Splitting**:

```typescript
// Lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));

// Lazy load heavy components
const Chart = lazy(() => import('./components/Chart'));
```

**Image Optimization**:

```typescript
// Use modern formats
<picture>
  <source srcSet="image.webp" type="image/webp" />
  <source srcSet="image.jpg" type="image/jpeg" />
  <img src="image.jpg" alt="Description" loading="lazy" />
</picture>
```

---

## Gate 7: Accessibility

### Tools

- axe-core
- eslint-plugin-jsx-a11y
- Lighthouse accessibility audit
- @axe-core/playwright

### Commands

**Linting**:

```bash
# ESLint with a11y plugin
npx eslint --plugin jsx-a11y src/

# Check specific components
npx eslint src/components/**/*.tsx
```

**Automated Testing**:

```bash
# Playwright with axe
npx playwright test --grep @a11y

# Lighthouse accessibility
lighthouse https://example.com --only-categories=accessibility
```

**Manual Testing**:

```bash
# Install axe DevTools browser extension
# Or use axe-cli
npx axe https://example.com
```

### Configuration

**eslint.config.js**:

```javascript
import jsxA11y from 'eslint-plugin-jsx-a11y';

export default [
  {
    plugins: {
      'jsx-a11y': jsxA11y,
    },
    rules: {
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/anchor-has-content': 'error',
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-role': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/heading-has-content': 'error',
      'jsx-a11y/img-redundant-alt': 'error',
      'jsx-a11y/label-has-associated-control': 'error',
      'jsx-a11y/no-autofocus': 'warn',
    },
  },
];
```

**Playwright Accessibility Test**:

```typescript
// tests/e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('should not have accessibility violations', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page }).include('main').analyze();

    const headingViolations = accessibilityScanResults.violations.filter(
      (v) => v.id === 'heading-order'
    );

    expect(headingViolations).toHaveLength(0);
  });
});
```

### CI/CD Integration

```yaml
- name: Gate 7 - Accessibility
  run: |
    # Lint for a11y issues
    npm run lint

    # Run accessibility tests
    npx playwright test tests/e2e/accessibility.spec.ts

    # Lighthouse a11y audit
    lhci autorun --only-categories=accessibility
```

### Accessibility Checklist

```typescript
// Component example with accessibility
export function Button({
  children,
  onClick,
  disabled = false,
  ariaLabel
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
      aria-disabled={disabled}
      type="button"
    >
      {children}
    </button>
  );
}

// Form with accessibility
export function LoginForm() {
  return (
    <form aria-labelledby="login-heading">
      <h2 id="login-heading">Login</h2>

      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        aria-required="true"
        aria-invalid={emailError ? 'true' : 'false'}
        aria-describedby={emailError ? 'email-error' : undefined}
      />
      {emailError && <span id="email-error" role="alert">{emailError}</span>}

      <button type="submit">Login</button>
    </form>
  );
}
```

---

## Gate 8: Integration

### Tools

- Playwright (E2E)
- Docker
- Vite preview server

### Commands

**Build Verification**:

```bash
# Production build
npm run build

# Preview production build
npm run preview

# Check build output
ls -lh dist/
```

**Integration Tests**:

```bash
# Run E2E tests against production build
npm run build
npm run preview &
npx playwright test
```

**Health Checks**:

```bash
# Check if app is running
curl -f http://localhost:4173/

# Check API endpoints
curl -f http://localhost:4173/api/health
```

### Configuration

**package.json**:

```json
{
  "scripts": {
    "build": "tsc && vite build",
    "preview": "vite preview --port 4173",
    "test:integration": "npm run build && npm run preview & npx playwright test; kill %1"
  }
}
```

**Dockerfile**:

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

RUN npm ci --production

EXPOSE 4173
CMD ["npm", "run", "preview"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - '4173:4173'
    environment:
      - NODE_ENV=production
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:4173/']
      interval: 30s
      timeout: 10s
      retries: 3
```

### CI/CD Integration

```yaml
- name: Gate 8 - Integration
  run: |
    # Build
    npm run build

    # Start preview server
    npm run preview &
    PREVIEW_PID=$!

    # Wait for server
    npx wait-on http://localhost:4173

    # Run smoke tests
    npx playwright test tests/e2e/smoke.spec.ts

    # Cleanup
    kill $PREVIEW_PID

- name: Build Docker Image
  run: |
    docker build -t app:${{ github.sha }} .
    docker run -d -p 4173:4173 app:${{ github.sha }}
    sleep 5
    curl -f http://localhost:4173/ || exit 1
```

### Smoke Tests

**tests/e2e/smoke.spec.ts**:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('API health check passes', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  test('critical user path works', async ({ page }) => {
    await page.goto('/');
    await page.click('a[href="/login"]');
    await expect(page).toHaveURL(/.*login/);
  });
});
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
npx tsc --noEmit

# Gate 2: Types
echo "🔒 Gate 2: Type Safety"
npx tsc --strict --noEmit

# Gate 3: Lint
echo "✨ Gate 3: Code Quality"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx)$')
if [ ! -z "$STAGED_FILES" ]; then
    npx prettier --write $STAGED_FILES
    npx eslint $STAGED_FILES --fix
    git add $STAGED_FILES
fi

# Gate 4: Security
echo "🛡️  Gate 4: Security"
npm audit --audit-level=high --production

# Gate 5: Tests (quick)
echo "🧪 Gate 5: Tests"
npx vitest run --changed HEAD --coverage=false

echo "✅ All quality gates passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Complete CI/CD Pipeline

**.github/workflows/quality-gates.yml**:

```yaml
name: Quality Gates

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality-gates:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install Dependencies
        run: npm ci

      - name: Gate 1 - Syntax Validation
        run: npx tsc --noEmit

      - name: Gate 2 - Type Safety
        run: |
          npx tsc --strict --noEmit
          npx type-coverage --at-least 95

      - name: Gate 3 - Code Quality
        run: |
          npx prettier --check "src/**/*.{ts,tsx,js,jsx}"
          npx eslint src/ --max-warnings 0

      - name: Gate 4 - Security
        run: |
          npm audit --audit-level=moderate
          npx snyk test --severity-threshold=high
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: Gate 5 - Tests
        run: |
          npm run test:coverage
          npx playwright install --with-deps
          npm run test:e2e

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

      - name: Gate 6 - Performance
        run: |
          npm run build
          npx vite-bundle-visualizer --json
          npm run perf:lighthouse

      - name: Gate 7 - Accessibility
        run: |
          npx playwright test tests/e2e/accessibility.spec.ts

      - name: Gate 8 - Integration
        run: |
          npm run preview &
          npx wait-on http://localhost:4173
          npx playwright test tests/e2e/smoke.spec.ts

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: quality-reports
          path: |
            .lighthouseci/
            playwright-report/
            coverage/
```

---

## Summary

This JavaScript/TypeScript quality gate implementation provides:

- **Automated validation** at every commit
- **Comprehensive testing** across unit, integration, and E2E
- **Security scanning** for dependencies and code
- **Performance monitoring** with Lighthouse and bundle analysis
- **Accessibility compliance** with axe-core and ESLint
- **Production readiness** verification with smoke tests

All gates integrate seamlessly with modern JavaScript tooling (Vite, TypeScript, ESLint, Vitest, Playwright) and can be adapted for React, Vue, or other frameworks.
