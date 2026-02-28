# Sentry Error Tracking Setup

Factory Insider uses Sentry for real-time error tracking, performance monitoring, and issue management.

## Overview

Sentry automatically captures:
- Unhandled exceptions and errors
- Performance metrics (response times, slow transactions)
- User interactions that led to errors
- Breadcrumb trail (console logs, HTTP requests)
- Source maps for debugging

## Configuration

### 1. Create Sentry Account

1. Go to [sentry.io](https://sentry.io)
2. Create a free account
3. Create a new project for "Python / Django" (similar to FastAPI)
4. Copy your DSN (Data Source Name)

### 2. Set Environment Variables

In `.env.local`:

```env
# Sentry Configuration
SENTRY_DSN=https://XXXX@YYYY.ingest.sentry.io/ZZZZZ
SENTRY_ENVIRONMENT=development  # or staging, production
SENTRY_TRACES_SAMPLE_RATE=0.1   # Capture 10% of transactions for performance monitoring
```

### 3. Automatic Initialization

Sentry automatically initializes when the application starts:

```python
# app/main.py
from app.sentry_init import init_sentry

init_sentry()  # Called on startup
```

## Features

### Error Tracking

Sentry automatically captures:

```python
# Any unhandled exception is automatically caught
def my_endpoint():
    1 / 0  # ZeroDivisionError captured automatically
```

### Performance Monitoring

Track request performance:

```
# Sentry tracks:
- Request duration
- Database query time
- Cache hits/misses
- Slow transactions (>1000ms)
```

### Custom Error Reporting

Manually report errors:

```python
import sentry_sdk

try:
    # Some operation
    pass
except Exception as e:
    sentry_sdk.capture_exception(e)
```

### Breadcrumbs

Automatic breadcrumb tracking for debugging:

```
# Sentry tracks:
- HTTP requests made
- Database queries
- Console logs
- User interactions
- Custom breadcrumbs
```

### Custom Breadcrumbs

Add custom debugging context:

```python
import sentry_sdk

sentry_sdk.add_breadcrumb(
    category="supplier",
    message="Fetching supplier data",
    level="info",
    data={"supplier_id": 123}
)
```

### User Context

Track which user experienced an error:

```python
import sentry_sdk

sentry_sdk.set_user({
    "id": user.id,
    "email": user.email,
    "username": user.full_name,
})
```

### Release Tracking

Track which version of your app has errors:

```
# Set in environment
SENTRY_RELEASE=0.1.0

# Or in code
sentry_sdk.set_tag("release", "0.1.0")
```

## Integration Points

### 1. FastAPI Integration

Automatically tracks:
- All HTTP requests
- Response codes
- Query parameters
- Request headers (sanitized)
- Exception details

### 2. Database Integration (SQLAlchemy)

Tracks:
- Database connection errors
- Slow queries
- Query parameters (sanitized)
- Transaction durations

### 3. Redis Integration

Monitors:
- Redis connection errors
- Cache operations
- Connection pool issues

### 4. Celery Integration

Captures:
- Task failures
- Task duration
- Task retries
- Queue issues

### 5. Logging Integration

Automatically captures:
- WARNING level logs and above
- Log context and parameters
- Structured logging

## Environment-Specific Behavior

### Development

```python
# In development:
SENTRY_ENABLED=False  # Set via ENVIRONMENT != "development"

# Sentry is disabled - no data sent
# Useful for avoiding noise during development
```

### Staging/Production

```python
# In staging/production:
SENTRY_ENABLED=True

# All errors captured and sent to Sentry
# Traces sampled at 10% (configurable)
```

## Dashboard Usage

### Viewing Issues

1. Go to [sentry.io](https://sentry.io)
2. Click on your project
3. View Issues tab shows all captured errors

### Issue Details

For each issue, see:
- **Error type and message**
- **Stack trace with source code**
- **Breadcrumb trail** (what happened before error)
- **User context** (which user affected)
- **Release information** (which version)
- **Frequency** (how many occurrences)

### Filtering Issues

Filter by:
- Environment
- Release version
- User
- Status (Unresolved, Resolved, Ignored)
- Priority
- Date range

### Setting Alerts

Configure alerts for:
- New issues
- Spike in error rate
- Performance degradation
- Specific error types

## Performance Monitoring

### Transaction Tracing

Sentry automatically creates transactions for:
- HTTP requests
- Database queries
- External API calls

### Viewing Performance

1. Go to **Performance** tab in Sentry
2. See slow requests and transactions
3. Identify bottlenecks
4. View timeline of operations

### Performance Thresholds

Configure in Sentry dashboard:
- Transaction threshold (default: 200ms for web)
- Slow span threshold (default: 500ms)

## Best Practices

### 1. Set User Context

```python
from fastapi import Request
import sentry_sdk

@app.middleware("http")
async def set_user_context(request: Request, call_next):
    if request.state.user:
        sentry_sdk.set_user({
            "id": request.state.user.id,
            "email": request.state.user.email,
        })
    response = await call_next(request)
    return response
```

### 2. Add Custom Context

```python
import sentry_sdk

sentry_sdk.set_context("supplier", {
    "id": supplier.id,
    "name": supplier.company_name,
    "country": supplier.country,
})
```

### 3. Tag Important Events

```python
import sentry_sdk

sentry_sdk.set_tag("video_format", "mp4")
sentry_sdk.set_tag("upload_method", "s3")
```

### 4. Track Custom Metrics

```python
import sentry_sdk

def process_video():
    with sentry_sdk.start_transaction(op="video", name="process_video"):
        # Processing code
        pass
```

### 5. Ignore Unimportant Errors

In `app/sentry_init.py`:
```python
ignore_errors=[
    "ValueError",  # Unimportant validation errors
]
```

## Troubleshooting

### Sentry Not Capturing Errors

1. Check `SENTRY_DSN` is set correctly
2. Verify environment is not "development"
3. Check network connectivity
4. Review Sentry dashboard for project settings

### Too Many Errors Being Captured

1. Reduce `SENTRY_TRACES_SAMPLE_RATE` (default: 0.1)
2. Add more errors to `ignore_errors` list
3. Use `before_send` hook to filter events

### Performance Impact

Sentry has minimal impact:
- Error capture: <1ms per request
- Transaction tracing: ~5-10ms per request
- Network: Async, doesn't block responses

## Related Documentation

- [Sentry Documentation](https://docs.sentry.io/)
- [Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
