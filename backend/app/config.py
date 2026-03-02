"""Application Configuration"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Factory Insider API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/factory_insider",
    )
    POSTGRES_ECHO: bool = DEBUG

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Elasticsearch
    ELASTICSEARCH_URL: str = os.getenv(
        "ELASTICSEARCH_URL", "http://localhost:9200"
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-super-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost",
    ]

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    HEYGEN_API_KEY: Optional[str] = os.getenv("HEYGEN_API_KEY")
    # HeyGen billing: $0.08 per minute of source video (adjust to match your plan)
    HEYGEN_COST_PER_MINUTE_USD: float = float(os.getenv("HEYGEN_COST_PER_MINUTE_USD", "0.08"))
    # Monthly budget alert threshold in USD (0 = disabled)
    HEYGEN_MONTHLY_BUDGET_USD: float = float(os.getenv("HEYGEN_MONTHLY_BUDGET_USD", "0"))
    CLAY_API_KEY: Optional[str] = os.getenv("CLAY_API_KEY")
    HEYREACH_API_KEY: Optional[str] = os.getenv("HEYREACH_API_KEY")
    HEYREACH_WEBHOOK_SECRET: Optional[str] = os.getenv("HEYREACH_WEBHOOK_SECRET")
    # LinkedIn safety limits (HeyReach)
    LINKEDIN_DAILY_CONNECTION_LIMIT: int = int(os.getenv("LINKEDIN_DAILY_CONNECTION_LIMIT", "25"))
    LINKEDIN_DAILY_MESSAGE_LIMIT: int = int(os.getenv("LINKEDIN_DAILY_MESSAGE_LIMIT", "30"))
    RB2B_API_KEY: Optional[str] = os.getenv("RB2B_API_KEY")
    RB2B_WEBHOOK_SECRET: Optional[str] = os.getenv("RB2B_WEBHOOK_SECRET")
    LEADFEEDER_API_TOKEN: Optional[str] = os.getenv("LEADFEEDER_API_TOKEN")
    LEADFEEDER_WEBHOOK_SECRET: Optional[str] = os.getenv("LEADFEEDER_WEBHOOK_SECRET")
    APOLLO_API_KEY: Optional[str] = os.getenv("APOLLO_API_KEY")
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "factory-insider-knowledge")
    PINECONE_DIMENSION: int = int(os.getenv("PINECONE_DIMENSION", "1024"))
    PINECONE_METRIC: str = os.getenv("PINECONE_METRIC", "cosine")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_EMBED_MODEL: str = os.getenv("PINECONE_EMBED_MODEL", "multilingual-e5-large")

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # OpenAI / Whisper
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE_URL: str = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")
    GERMAN_TRANSLATION_MAX_RATIO: float = float(os.getenv("GERMAN_TRANSLATION_MAX_RATIO", "1.1"))
    GERMAN_COMPRESSION_MAX_PASSES: int = int(os.getenv("GERMAN_COMPRESSION_MAX_PASSES", "3"))

    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "factory-insider-dev")
    # CDN (CloudFront) — if set, get_cdn_url() returns CloudFront URLs instead of S3 URLs
    CLOUDFRONT_DOMAIN: Optional[str] = os.getenv("CLOUDFRONT_DOMAIN")  # e.g. "d1234abcd.cloudfront.net"

    # Instantly (Email outreach — Sprint 8)
    INSTANTLY_API_KEY: Optional[str] = os.getenv("INSTANTLY_API_KEY")
    INSTANTLY_API_BASE_URL: str = os.getenv("INSTANTLY_API_BASE_URL", "https://api.instantly.ai/api/v2")
    INSTANTLY_WEBHOOK_SECRET: Optional[str] = os.getenv("INSTANTLY_WEBHOOK_SECRET")
    # Email safety limits
    EMAIL_DAILY_SEND_LIMIT: int = int(os.getenv("EMAIL_DAILY_SEND_LIMIT", "50"))
    EMAIL_BOUNCE_RATE_THRESHOLD: float = float(os.getenv("EMAIL_BOUNCE_RATE_THRESHOLD", "0.02"))  # 2%

    # HubSpot CRM (Sprint 8 — 8.9)
    HUBSPOT_PRIVATE_APP_TOKEN: Optional[str] = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
    HUBSPOT_PIPELINE_ID: Optional[str] = os.getenv("HUBSPOT_PIPELINE_ID")
    HUBSPOT_PORTAL_ID: Optional[str] = os.getenv("HUBSPOT_PORTAL_ID")

    # OpusClip (Sprint 9 — 9.1: short-video generation)
    OPUSCLIP_API_KEY: Optional[str] = os.getenv("OPUSCLIP_API_KEY")
    OPUSCLIP_API_BASE_URL: str = os.getenv("OPUSCLIP_API_BASE_URL", "https://api.opus.pro/v1")
    OPUSCLIP_WEBHOOK_SECRET: Optional[str] = os.getenv("OPUSCLIP_WEBHOOK_SECRET")
    # Number of short clips to request per source video
    OPUSCLIP_CLIPS_PER_VIDEO: int = int(os.getenv("OPUSCLIP_CLIPS_PER_VIDEO", "10"))

    # Repurpose.io (Sprint 9 — 9.5: multi-channel scheduler)
    REPURPOSE_API_KEY: Optional[str] = os.getenv("REPURPOSE_API_KEY")
    REPURPOSE_API_BASE_URL: str = os.getenv("REPURPOSE_API_BASE_URL", "https://api.repurpose.io/v1")
    REPURPOSE_WEBHOOK_SECRET: Optional[str] = os.getenv("REPURPOSE_WEBHOOK_SECRET")

    # Content generation limits (Sprint 9 — 9.2)
    CONTENT_MAX_LINKEDIN_POSTS: int = int(os.getenv("CONTENT_MAX_LINKEDIN_POSTS", "30"))
    CONTENT_MAX_SEO_ARTICLES: int = int(os.getenv("CONTENT_MAX_SEO_ARTICLES", "10"))
    # AI quality guard — comma-separated banned phrases (9.3)
    CONTENT_AI_BANNED_PHRASES: str = os.getenv(
        "CONTENT_AI_BANNED_PHRASES",
        "as an ai,as a language model,i cannot,i'm unable to,certainly!,absolutely!,"
        "delve,leverage,harness,game-changer,cutting-edge,synergy,revolutionize,"
        "in today's fast-paced,it's important to note,it's worth noting",
    )

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", f"{REDIS_URL.rstrip('0')}1"
    )

    # Sentry Error Tracking
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_ENABLED: bool = SENTRY_DSN is not None and ENVIRONMENT != "development"
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", ENVIRONMENT)
    SENTRY_TRACES_SAMPLE_RATE: float = float(
        os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    SENTRY_DEBUG: bool = DEBUG

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Application settings singleton
settings = get_settings()
