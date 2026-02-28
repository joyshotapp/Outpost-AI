# CI/CD Pipeline Documentation

## Overview

The Factory Insider project uses GitHub Actions for continuous integration and deployment (CI/CD). The pipeline includes:

- **Lint**: Code quality checks (flake8, eslint, black, prettier)
- **Test**: Unit and integration tests with coverage reporting
- **Build**: Docker image building and publishing
- **Deploy**: Automated deployment to staging environments

## Workflow Files

### Backend Pipeline (`.github/workflows/backend.yml`)

Triggered on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches
- Changes to `backend/**` or `.github/workflows/backend.yml`

**Jobs:**

1. **Lint** (ubuntu-latest)
   - Python 3.12
   - flake8: Code style checking
   - black: Code formatting
   - isort: Import sorting
   - mypy: Type checking

2. **Test** (ubuntu-latest + PostgreSQL + Redis)
   - Unit tests with pytest
   - Code coverage reporting to Codecov
   - Test database: PostgreSQL 16
   - Test cache: Redis 7

3. **Build** (on main/master)
   - Build Docker image
   - Push to GitHub Container Registry
   - Cache layers with buildx

4. **Deploy to Staging** (on develop)
   - SSH deployment to staging server
   - Database migrations with Alembic
   - Service health checks

### Frontend Pipeline (`.github/workflows/frontend.yml`)

Triggered on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches
- Changes to `frontend/**` or `.github/workflows/frontend.yml`

**Jobs:**

1. **Lint** (ubuntu-latest + Node.js 20)
   - ESLint: Code style
   - Prettier: Code formatting
   - TypeScript type checking

2. **Test** (ubuntu-latest + Node.js 20)
   - Jest unit tests
   - Coverage reporting to Codecov

3. **Build** (ubuntu-latest + Node.js 20)
   - Build all three Next.js apps (buyer, supplier, admin)
   - Parallel builds for each app

4. **Docker Build** (on main/master)
   - Build Docker image for each app
   - Push to GitHub Container Registry

5. **E2E Tests** (on pull requests)
   - Playwright E2E tests
   - Artifact upload (test reports)

6. **Deploy to Staging** (on develop)
   - Deploy to Vercel
   - Deploy all three apps

## Environment Setup

### Required GitHub Secrets

See [`.github/SETUP_SECRETS.md`](./SETUP_SECRETS.md) for complete setup instructions.

### Required Variables

Environment variables for the workflows:

**Backend:**
```
ENVIRONMENT=staging
DEBUG=false
NEXT_PUBLIC_API_URL=https://api-staging.factory-insider.dev
```

**Frontend:**
```
NEXT_PUBLIC_API_URL=https://api-staging.factory-insider.dev
```

## Deployment Environments

### Staging

**Branch:** `develop`
**When:** After passing all checks
**Backend:** Custom VM via SSH
**Frontend:** Vercel

**Requirements:**
- SSH access to staging server
- Vercel project configured
- Environment variables set in deployment target

### Production

**Branch:** `main` or `master`
**When:** Manual approval (optional)
**Backend:** AWS ECS (via Terraform)
**Frontend:** Vercel (production)

## Local Testing

### Backend Tests

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestAuth::test_register_success

# Run in watch mode
pytest-watch
```

### Frontend Tests

```bash
cd frontend

# Install dependencies
npm install

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific app tests
npm test -- --testPathPattern="apps/buyer"

# Watch mode
npm test -- --watch

# E2E tests
npm run test:e2e

# E2E tests UI mode
npm run test:e2e -- --ui
```

### Lint Checks

```bash
# Backend
cd backend
black --check app tests
isort --check-only app tests
flake8 app tests
mypy app

# Frontend
cd frontend
npm run lint
npm run format:check
npm run type-check
```

## Docker Image Registry

Images are pushed to GitHub Container Registry (ghcr.io):

```
ghcr.io/yourorg/factory-insider/backend:main
ghcr.io/yourorg/factory-insider/frontend-buyer:main
ghcr.io/yourorg/factory-insider/frontend-supplier:main
ghcr.io/yourorg/factory-insider/frontend-admin:main
```

## Rollback Procedures

### Backend Rollback

If deployment fails:

```bash
# SSH into staging server
ssh user@staging-host

# Stop current deployment
cd /deploy/path
docker-compose -f docker-compose.staging.yml down

# Revert to previous commit
git checkout previous-commit-hash

# Redeploy
docker-compose -f docker-compose.staging.yml up -d
```

### Frontend Rollback

On Vercel dashboard:
1. Go to Deployments
2. Click "Redeploy" on previous successful deployment

## Monitoring

### Build Status

Monitor workflows at: `https://github.com/yourorg/factory-insider/actions`

### Coverage Reports

Coverage reports are uploaded to Codecov:
- Backend: `https://codecov.io/gh/yourorg/factory-insider?flags=backend`
- Frontend: `https://codecov.io/gh/yourorg/factory-insider?flags=frontend`

### Deployment Status

- **Backend:** SSH logs + Docker health checks
- **Frontend:** Vercel analytics dashboard

## Troubleshooting

### Workflow Won't Trigger

1. Check branch protection rules allow workflows
2. Verify path triggers match changed files
3. Check if workflow is disabled in GitHub settings

### Tests Fail Locally but Pass in CI

- Ensure Node.js/Python versions match
- Check all dependencies are installed
- Verify environment variables are set
- Clear build cache: `npm run clean` or `pytest --cache-clear`

### Deployment Fails

1. Check secrets are correctly set
2. Verify SSH key/Vercel token is valid
3. Check deployment target is accessible
4. Review workflow logs for specific error

## Best Practices

### Code Quality

- Maintain >80% test coverage
- Fix all lint warnings before pushing
- Run local tests before creating PR
- Use type hints in Python and TypeScript

### Deployments

- Always test locally first
- Create feature branches for PRs
- Run through develop branch first
- Use meaningful commit messages

### Security

- Rotate secrets regularly
- Never commit secrets to repository
- Use SSH keys for server access
- Enable branch protection rules

## CI/CD Configuration Files

- Backend workflow: `.github/workflows/backend.yml`
- Frontend workflow: `.github/workflows/frontend.yml`
- Staging compose: `docker-compose.staging.yml`
- Secrets guide: `.github/SETUP_SECRETS.md`

## Related Documentation

- [Development Guide](./DEVELOPMENT.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Testing Guide](./TESTING.md)
