# GitHub Actions Secrets Setup Guide

This guide explains how to set up required secrets for CI/CD pipelines.

## Frontend Secrets

Add these secrets to your GitHub repository (`Settings > Secrets and variables > Actions`):

### Vercel Deployment
- `VERCEL_TOKEN`: Your Vercel authentication token
  - Get from: https://vercel.com/account/tokens
- `VERCEL_ORG_ID`: Your Vercel organization/team ID
  - Get from: Vercel dashboard
- `VERCEL_PROJECT_ID_BUYER`: Project ID for buyer app
- `VERCEL_PROJECT_ID_SUPPLIER`: Project ID for supplier app
- `VERCEL_PROJECT_ID_ADMIN`: Project ID for admin app

### Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL for staging/production

## Backend Secrets

### Database
- `STAGING_DATABASE_URL`: PostgreSQL connection string for staging

### AWS Credentials
- `AWS_ACCESS_KEY_ID`: AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key

### JWT
- `JWT_SECRET_KEY`: Secret key for JWT token signing (min 32 characters)

### Third-party APIs
- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `HEYGEN_API_KEY`: HeyGen video generation API key
- `CLAY_API_KEY`: Clay.com data enrichment API key
- `APOLLO_API_KEY`: Apollo sales intelligence API key

### Deployment
- `STAGING_DEPLOY_KEY`: SSH private key for staging server
- `STAGING_DEPLOY_HOST`: Staging server hostname/IP
- `STAGING_DEPLOY_USER`: Staging server SSH user
- `STAGING_DEPLOY_PATH`: Deployment path on staging server

## How to Add Secrets

### Via GitHub Web UI
1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Enter Name and Value
4. Click "Add secret"

### Via GitHub CLI
```bash
# Set a single secret
gh secret set SECRET_NAME --body "secret_value"

# Set from file
gh secret set SECRET_NAME --body-file path/to/file
```

## Environment Variables for Workflows

### Production Deployment Variables
Add to `Settings > Variables > Actions`:

- `DOCKER_REGISTRY`: Container registry URL (e.g., ghcr.io)
- `PRODUCTION_API_URL`: Production API endpoint
- `STAGING_API_URL`: Staging API endpoint

## Testing Secrets Locally

Create a `.env.local` file in the backend directory with your secrets:

```bash
cp backend/.env.local.example backend/.env.local
# Edit backend/.env.local and add your actual values
```

**Important**: Never commit `.env.local` to version control!

## Rotating Secrets

When rotating secrets:

1. Generate new secret value
2. Update in GitHub Secrets
3. Update in any deployed environments
4. Invalidate old credentials (if applicable)
5. Update local `.env.local` files

## Troubleshooting

### "403 Forbidden" during deployment
- Check `STAGING_DEPLOY_KEY` is a valid SSH private key
- Verify deploy user has access to deploy path
- Ensure SSH key permissions are correct (600)

### "Invalid token" errors
- Regenerate API keys in respective services
- Update secrets immediately
- Clear any caches in deployed environments

### Build fails due to missing secrets
- Check secret names match workflow references (case-sensitive)
- Ensure secrets are in correct repository (not organization)
- Verify pull requests can access secrets if needed
