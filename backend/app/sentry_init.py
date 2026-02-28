"""Sentry error tracking initialization"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings


def init_sentry():
    """Initialize Sentry error tracking"""
    if not settings.SENTRY_ENABLED:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        debug=settings.SENTRY_DEBUG,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
            LoggingIntegration(
                level=10,  # DEBUG
                event_level=20,  # INFO
            ),
        ],
        # Performance Monitoring
        enable_tracing=True,
        # Release tracking
        release=settings.APP_VERSION,
        # Ignore specific errors
        ignore_errors=[
            "HTTPException",
        ],
        # Attach stack traces
        attach_stacktrace=True,
        # Include request bodies in error reports
        include_request_body="medium",
    )

    print(f"✓ Sentry initialized (Environment: {settings.SENTRY_ENVIRONMENT})")
