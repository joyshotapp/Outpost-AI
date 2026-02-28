# Testing Framework Guide

Comprehensive guide for testing the Factory Insider platform using pytest, Playwright, and integration tests.

## Testing Stack

- **Backend**: pytest + pytest-asyncio + pytest-cov
- **Frontend**: Jest + React Testing Library + Playwright
- **Integration**: API tests with real database/Redis
- **E2E**: Playwright for user workflows

## Backend Testing

### Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create test database
createdb factory_insider_test
```

### Unit Tests

Tests for individual functions and classes:

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test
pytest tests/unit/test_auth.py::TestAuth::test_register_success

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Watch mode (auto-rerun on changes)
pytest-watch tests/
```

### Integration Tests

Tests with real database and services:

```bash
# Run integration tests
pytest tests/integration/

# Run with specific database
DATABASE_URL=postgresql://user:pass@localhost/test_db pytest tests/integration/

# Run with coverage
pytest tests/integration/ --cov=app
```

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_auth.py            # Example auth tests
├── integration/
│   ├── test_rfq_flow.py    # RFQ submission workflow
│   ├── test_user_flow.py   # User lifecycle
│   └── test_api.py         # API endpoint tests
└── unit/
    ├── test_models.py      # ORM model tests
    └── test_security.py    # Security utilities
```

### Writing Tests

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_user_registration(db: AsyncSession):
    """Test user registration endpoint"""
    from app.models import User

    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "securepass123",
        "full_name": "Test User"
    }

    # Act
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Assert
    assert user.id is not None
    assert user.email == "test@example.com"
```

### Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
async def test_db():
    """In-memory database session"""
    # Setup
    yield session
    # Teardown

@pytest.fixture
def client(test_db):
    """FastAPI test client"""
    # Setup with dependency override
    return TestClient(app)

@pytest.fixture
async def authenticated_user(test_db):
    """Create authenticated test user"""
    # Create and return user
    yield user
```

### Markers

Use markers to organize tests:

```python
@pytest.mark.asyncio
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.asyncio
@pytest.mark.integration
def test_with_database():
    pass

# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## Frontend Testing

### Setup

```bash
cd frontend

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Unit Tests

Jest tests for components:

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Run specific test file
npm test -- test_auth.spec.ts

# Generate coverage report
npm test -- --coverage

# Update snapshots
npm test -- --updateSnapshot
```

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import { LoginForm } from '@/components/LoginForm';

describe('LoginForm', () => {
  it('should render login form', () => {
    render(<LoginForm />);
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('should submit login on form submit', async () => {
    const { user } = render(<LoginForm />);

    await user.type(screen.getByPlaceholderText('Email'), 'test@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: /login/i }));

    // Assert
  });
});
```

### E2E Tests

Playwright for end-to-end testing:

```bash
# Run E2E tests
npm run test:e2e

# Run specific test
npx playwright test tests/e2e/auth.spec.ts

# Debug mode with UI
npx playwright test --ui

# Run with specific browser
npx playwright test --project=chromium

# View last test report
npx playwright show-report
```

### E2E Test Example

```typescript
import { test, expect } from '@playwright/test';

test('user registration flow', async ({ page }) => {
  // Navigate to app
  await page.goto('http://localhost:3000/register');

  // Fill form
  await page.fill('input[type="email"]', 'newuser@example.com');
  await page.fill('input[type="password"]', 'SecurePass123!');
  await page.fill('input[name="fullName"]', 'Test User');

  // Submit
  await page.click('button:has-text("Register")');

  // Verify redirect
  await expect(page).toHaveURL(/\/dashboard/);

  // Verify success message
  await expect(page.locator('text=Welcome')).toBeVisible();
});

test('RFQ submission flow', async ({ page, apiRequestContext }) => {
  // Login via API
  const loginResponse = await apiRequestContext.post('/api/v1/auth/login', {
    data: {
      email: 'buyer@example.com',
      password: 'password123'
    }
  });

  const { access_token } = await loginResponse.json();

  // Navigate to RFQ page
  await page.goto('http://localhost:3000/rfq/new', {
    extraHTTPHeaders: {
      'Authorization': `Bearer ${access_token}`
    }
  });

  // Fill RFQ form
  await page.fill('input[placeholder="RFQ Title"]', 'Aluminum Brackets');
  await page.fill('textarea', 'Need 1000 units of custom aluminum brackets');
  await page.selectOption('select[name="quantity"]', '1000');

  // Submit
  await page.click('button:has-text("Submit RFQ")');

  // Verify submission
  await expect(page).toHaveURL(/\/rfq\/\d+/);
});
```

## Test Coverage

### Coverage Requirements

- **Backend**: Minimum 80% overall coverage
- **Frontend**: Minimum 70% for critical paths
- **Critical paths**: >90% required

### Generate Coverage Reports

```bash
# Backend
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Frontend
npm test -- --coverage --watchAll=false
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main, master, develop
- Pull requests
- Manual trigger

See `.github/workflows/backend.yml` and `.github/workflows/frontend.yml`

### Local Pre-commit

Run tests before committing:

```bash
# Install pre-commit hook
pip install pre-commit
pre-commit install

# Create .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
```

## Performance Testing

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py -u 100 -r 10 -t 1h
```

### Database Query Performance

```bash
# Enable slow query logging
pytest tests/ --durations=10  # Show 10 slowest tests

# Profile specific test
pytest tests/test_auth.py --profile
```

## Test Organization

### Naming Conventions

- **Test files**: `test_*.py` or `*_test.py`
- **Test classes**: `Test<Feature>`
- **Test methods**: `test_<behavior>`
- **E2E files**: `*.spec.ts`

### Test Isolation

- Use database transactions
- Clean up after each test
- Use separate test databases
- Mock external APIs

## Mocking

### Backend Mocking

```python
from unittest.mock import patch, MagicMock

@patch('app.security.hash_password')
def test_with_mock(mock_hash):
    mock_hash.return_value = "mocked_hash"

    # Test code
    assert mock_hash.called
```

### Frontend Mocking

```typescript
import { jest } from '@jest/globals';

jest.mock('@/lib/api', () => ({
  fetchUser: jest.fn(() => Promise.resolve({ id: 1 }))
}));
```

## Debugging Tests

### Backend Debugging

```bash
# Run with verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Drop into debugger
pytest tests/ --pdb

# Only stop on failures
pytest tests/ --pdbcls=IPython.terminal.debugger:Pdb
```

### Frontend Debugging

```bash
# Debug single test
node --inspect-brk node_modules/.bin/jest --runInBand tests/auth.spec.ts

# Watch and debug
npm test -- --watch tests/auth.spec.ts
```

## Test Reports

### Backend Reports

```bash
# HTML report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# XML report for CI
pytest tests/ --cov=app --cov-report=xml
```

### Frontend Reports

```bash
# HTML report
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html

# LCOV report
npm test -- --coverage --watchAll=false --collectCoverageFrom='**/*.{ts,tsx}'
```

## Best Practices

1. **Test Behavior, Not Implementation**
   - Focus on what the code does, not how it does it
   - Tests should be resilient to refactoring

2. **Keep Tests DRY**
   - Use fixtures and helpers
   - Extract common setup

3. **Use Descriptive Names**
   - `test_register_with_invalid_email_shows_error` not `test_register1`
   - Names should describe the scenario

4. **One Assertion Per Test** (when possible)
   - Makes it clear what failed
   - Easier to debug

5. **Test Edge Cases**
   - Empty inputs
   - Null/None values
   - Boundary conditions
   - Invalid data types

6. **Mock External Dependencies**
   - Third-party APIs
   - External services
   - Don't test third-party code

7. **Clean Up**
   - Delete test data after tests
   - Close connections
   - Reset mocks

## Troubleshooting

### AsyncIO Errors

```bash
# Ensure pytest-asyncio is configured
# In pytest.ini:
[pytest]
asyncio_mode = auto
```

### Port Already in Use

```bash
# Kill process using port
lsof -ti:3000 | xargs kill -9
```

### Database Locked

```bash
# Drop test database and recreate
dropdb factory_insider_test
createdb factory_insider_test
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://testingjavascript.com/)

## Related Documentation

- [CI/CD Pipeline](./CI_CD_PIPELINE.md)
- [Development Guide](./DEVELOPMENT.md)
