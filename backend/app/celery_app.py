"""Celery application configuration and initialization"""

import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "factory_insider",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task configuration
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    # Result backend configuration
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True,
    },
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Task routing
    task_routes={
        "app.tasks.rfq_pipeline.process_rfq_complete_pipeline": {"queue": "rfq_pipeline"},
        "app.tasks.rfq_pipeline.parse_rfq_text_task": {"queue": "rfq_analysis"},
        "app.tasks.rfq_pipeline.analyze_rfq_pdf_task": {"queue": "rfq_analysis"},
        "app.tasks.rfq_pipeline.enrich_buyer_company_task": {"queue": "rfq_analysis"},
        "app.tasks.rfq_pipeline.calculate_lead_score_task": {"queue": "rfq_scoring"},
        "app.tasks.rfq_pipeline.generate_draft_reply_task": {"queue": "rfq_generation"},
        "app.tasks.knowledge_base.ingest_knowledge_document": {"queue": "knowledge_ingestion"},
        "app.tasks.video.transcribe_video_with_whisper": {"queue": "video_transcription"},
        # Sprint 7 — Outbound engine
        "app.tasks.outbound.enrich_contacts_pipeline": {"queue": "outbound_enrichment"},
        "app.tasks.outbound.generate_openers_batch": {"queue": "outbound_enrichment"},
        "app.tasks.outbound.import_contacts_to_heyreach": {"queue": "outbound_sequences"},
        "app.tasks.outbound.enforce_linkedin_safety": {"queue": "outbound_sequences"},
        "app.tasks.outbound.reset_daily_linkedin_counters": {"queue": "outbound_maintenance"},
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "monitor-pipeline-health": {
            "task": "app.tasks.rfq_pipeline.monitor_pipeline_health",
            "schedule": 300.0,  # Every 5 minutes
        },
        "reset-daily-linkedin-counters": {
            "task": "app.tasks.outbound.reset_daily_linkedin_counters",
            "schedule": 86400.0,  # Every 24 hours (midnight UTC)
        },
        "enforce-linkedin-safety-all": {
            "task": "app.tasks.outbound.enforce_linkedin_safety",
            "schedule": 3600.0,  # Hourly safety check (requires campaign_id; use signals in production)
        },
        # ── Sprint 12: Remarketing & Nurture ─────────────────────────────────
        "rescore-c-grade-leads-90d": {
            "task": "app.tasks.remarketing.rescore_c_grade_leads",
            "schedule": 86400.0,  # Daily at midnight UTC
        },
        "enrol-b-grade-nurture-30d": {
            "task": "app.tasks.remarketing.enrol_b_grade_nurture",
            "schedule": 86400.0,  # Daily at 02:00 UTC
        },
        "advance-remarketing-sequences": {
            "task": "app.tasks.remarketing.advance_remarketing_sequences",
            "schedule": 3600.0,  # Every hour
        },
        "send-monthly-nurture-emails": {
            "task": "app.tasks.nurture.send_monthly_nurture_emails",
            "schedule": 86400.0,  # Daily
        },
    },
)

# Auto-discover tasks from app modules
celery_app.autodiscover_tasks(["app.tasks"])

logger.info(f"Celery configured with broker: {settings.CELERY_BROKER_URL}")
