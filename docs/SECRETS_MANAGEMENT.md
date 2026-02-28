# API Keys and Secrets Management

Complete guide for managing third-party API keys and sensitive configuration using AWS Secrets Manager.

## Overview

All sensitive data (API keys, database passwords, tokens) should be managed through AWS Secrets Manager instead of environment files.

## Third-Party API Keys Required

### Core Services

1. **Anthropic Claude API**
   - Purpose: AI-powered RFQ parsing, response generation
   - URL: https://console.anthropic.com
   - Key type: API Key
   - Required for: RFQ parsing, AI summaries, content generation

2. **HeyGen API**
   - Purpose: AI video generation for product demonstrations
   - URL: https://www.heygen.com/developers
   - Key type: API Key
   - Required for: Video avatar generation, multilingual content

3. **Apollo Sales Intelligence**
   - Purpose: B2B contact and company data enrichment
   - URL: https://www.apollo.io/developers
   - Key type: API Key
   - Required for: Lead scoring, company research

4. **Clay.com**
   - Purpose: Data enrichment and verification
   - URL: https://clay.com/api
   - Key type: API Key
   - Required for: Contact enrichment, verification

5. **Pinecone**
   - Purpose: Vector database for RAG
   - URL: https://www.pinecone.io
   - Key type: API Key + Index Name
   - Required for: Embedding storage, semantic search

### Payment & Subscription

6. **Stripe**
   - Purpose: Payment processing
   - URL: https://dashboard.stripe.com
   - Keys: Secret Key, Webhook Secret
   - Required for: Subscription billing

### Communication

7. **Slack**
   - Purpose: Notifications and alerts
   - URL: https://api.slack.com/apps
   - Key type: Webhook URL
   - Required for: Real-time alerts, notifications

## AWS Secrets Manager Setup

### 1. Create Secrets in AWS

#### Using AWS CLI

```bash
# Create secret for database
aws secretsmanager create-secret \
  --name factory-insider/dev/database \
  --secret-string '{
    "username": "postgres",
    "password": "your-secure-password",
    "host": "your-rds-endpoint",
    "port": 5432,
    "dbname": "factory_insider"
  }' \
  --region ap-southeast-1

# Create secret for Anthropic
aws secretsmanager create-secret \
  --name factory-insider/dev/anthropic \
  --secret-string '{
    "api_key": "sk-ant-xxxxx"
  }' \
  --region ap-southeast-1

# Create secret for HeyGen
aws secretsmanager create-secret \
  --name factory-insider/dev/heygen \
  --secret-string '{
    "api_key": "your-heygen-key"
  }' \
  --region ap-southeast-1

# Create secret for Apollo
aws secretsmanager create-secret \
  --name factory-insider/dev/apollo \
  --secret-string '{
    "api_key": "your-apollo-key"
  }' \
  --region ap-southeast-1

# Create secret for Pinecone
aws secretsmanager create-secret \
  --name factory-insider/dev/pinecone \
  --secret-string '{
    "api_key": "your-pinecone-key",
    "index_name": "factory-insider-dev"
  }' \
  --region ap-southeast-1

# Create secret for Stripe
aws secretsmanager create-secret \
  --name factory-insider/dev/stripe \
  --secret-string '{
    "secret_key": "sk_test_xxxxx",
    "webhook_secret": "whsec_xxxxx"
  }' \
  --region ap-southeast-1

# Create secret for Slack
aws secretsmanager create-secret \
  --name factory-insider/dev/slack \
  --secret-string '{
    "webhook_url": "https://hooks.slack.com/services/xxxxx"
  }' \
  --region ap-southeast-1
```

#### Using AWS Console

1. Navigate to AWS Secrets Manager
2. Click "Store a new secret"
3. Select "Other type of secret"
4. Enter secret JSON (see CLI examples above)
5. Name the secret (e.g., `factory-insider/dev/anthropic`)
6. Click "Store"

### 2. Create IAM Policy for ECS/Backend Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:ap-southeast-1:ACCOUNT-ID:secret:factory-insider/*"
    },
    {
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "arn:aws:kms:ap-southeast-1:ACCOUNT-ID:key/KEY-ID"
    }
  ]
}
```

### 3. Backend Configuration

Update `backend/app/config.py` to load from Secrets Manager:

```python
import json
import boto3
from functools import lru_cache

@lru_cache()
def get_secret(secret_name: str) -> dict:
    """Retrieve secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='ap-southeast-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}")

class Settings(BaseSettings):
    # Load from Secrets Manager in production
    def __init__(self, **data):
        super().__init__(**data)

        if self.ENVIRONMENT == 'production':
            db_secret = get_secret('factory-insider/prod/database')
            self.DATABASE_URL = f"postgresql://{db_secret['username']}:{db_secret['password']}@{db_secret['host']}:{db_secret['port']}/{db_secret['dbname']}"

            anthropic_secret = get_secret('factory-insider/prod/anthropic')
            self.ANTHROPIC_API_KEY = anthropic_secret['api_key']
            # ... load other secrets
```

### 4. Local Development

For local development, continue using `.env.local`:

```bash
# backend/.env.local
ANTHROPIC_API_KEY=sk-ant-xxxxx
HEYGEN_API_KEY=hg-xxxxx
APOLLO_API_KEY=apollo-xxxxx
CLAY_API_KEY=clay-xxxxx
PINECONE_API_KEY=pinecone-xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx
```

**Important:** Never commit `.env.local` to Git!

## API Key Acquisition Guide

### 1. Anthropic Claude API

```bash
# Visit: https://console.anthropic.com
# 1. Sign up for Anthropic account
# 2. Go to Account Settings > API Keys
# 3. Create new API key
# 4. Copy the key starting with "sk-ant-"
# 5. Keep it secure - cannot be retrieved again
```

### 2. HeyGen

```bash
# Visit: https://www.heygen.com/developers
# 1. Sign up for HeyGen account
# 2. Go to Developer > API Keys
# 3. Create new API key
# 4. Save the key securely
```

### 3. Apollo Sales Intelligence

```bash
# Visit: https://www.apollo.io/developers
# 1. Create Apollo account
# 2. Go to Settings > API
# 3. Generate API key
# 4. Note the rate limits (e.g., 100 queries/month)
```

### 4. Clay.com

```bash
# Visit: https://clay.com/api
# 1. Sign up for Clay account
# 2. Go to Settings > API
# 3. Create API key
# 4. Configure data providers for enrichment
```

### 5. Pinecone

```bash
# Visit: https://www.pinecone.io
# 1. Create Pinecone account
# 2. Create organization and project
# 3. Go to API Keys
# 4. Create API key
# 5. Create index with appropriate dimension (e.g., 1536 for OpenAI embeddings)
```

### 6. Stripe

```bash
# Visit: https://dashboard.stripe.com
# 1. Sign up for Stripe account
# 2. Go to Developers > API Keys
# 3. Copy Secret Key (starts with sk_test_ or sk_live_)
# 4. Create webhook endpoint for subscriptions
# 5. Get webhook secret (starts with whsec_)
```

### 7. Slack

```bash
# Visit: https://api.slack.com/apps
# 1. Create New App
# 2. Select "From scratch"
# 3. Name app and select workspace
# 4. Go to Incoming Webhooks
# 5. Click "Add New Webhook to Workspace"
# 6. Select channel for notifications
# 7. Copy webhook URL
```

## Rotation and Updates

### Rotate Keys

```bash
# Update existing secret
aws secretsmanager update-secret \
  --secret-id factory-insider/prod/anthropic \
  --secret-string '{
    "api_key": "sk-ant-new-key"
  }' \
  --region ap-southeast-1

# Force immediate rotation
aws secretsmanager rotate-secret \
  --secret-id factory-insider/prod/anthropic \
  --rotation-rules AutomaticallyAfterDays=30
```

### Invalidate Old Keys

After rotation in Secrets Manager:
1. Invalidate old key in third-party service
2. Verify new key is working
3. Monitor for errors

## Best Practices

1. **Never commit keys** to repository
2. **Use IAM roles** for ECS/Lambda access
3. **Rotate regularly** (quarterly minimum)
4. **Use different keys** for each environment
5. **Enable MFA** on AWS console access
6. **Audit access** via CloudTrail
7. **Monitor usage** of each key
8. **Set spending alerts** on Stripe/AWS
9. **Use webhook signatures** for verification
10. **Document key requirements** for each service

## Troubleshooting

### "Access Denied" Error

1. Check IAM policy attached to role
2. Verify Secrets Manager resource ARN
3. Ensure KMS permissions are granted

### Key Not Found

1. Verify secret name is correct
2. Check secret is in correct AWS region
3. Confirm secret has not been deleted

### Rate Limit Errors

1. Check API usage limits
2. Implement exponential backoff
3. Consider upgrading plan
4. Cache responses where possible

## Monitoring

### CloudWatch Metrics

Monitor API usage:
```bash
# Check Secrets Manager access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --region ap-southeast-1
```

### Set Alerts

Configure CloudWatch alarms for:
- Failed secret retrievals
- Rate limit breaches
- Unusual API usage patterns

## Related Documentation

- [AWS Secrets Manager Guide](https://docs.aws.amazon.com/secretsmanager/)
- [IAM Best Practices](https://docs.aws.amazon.com/iam/latest/userguide/best-practices.html)
- [API Rate Limiting](./RATE_LIMITING.md)
