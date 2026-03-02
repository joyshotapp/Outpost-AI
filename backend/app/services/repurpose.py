"""Repurpose.io API service adapter — Sprint 9 (Task 9.5).

Repurpose.io docs: https://repurpose.io/developers/api
Key concepts:
  - Workflow : A pre-configured cross-posting pipeline (e.g. LinkedIn → YouTube)
  - Post     : Scheduled or immediate content item sent via a workflow
  - Webhook  : Repurpose.io POSTs events when posts are published or fail

Authentication: Bearer token in Authorization header.

Stub mode: When REPURPOSE_API_KEY is not set all methods return deterministic
stub objects so the rest of the application can run without a live key.
"""

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class RepurposeService:
    """Wrapper around the Repurpose.io REST API."""

    BASE_URL = settings.REPURPOSE_API_BASE_URL

    # Supported platform identifiers
    PLATFORM_LINKEDIN = "linkedin"
    PLATFORM_YOUTUBE = "youtube"
    PLATFORM_INSTAGRAM = "instagram"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key: str | None = api_key if api_key is not None else settings.REPURPOSE_API_KEY
        self.base_url: str = base_url or self.BASE_URL
        self.stub_mode: bool = not bool(self.api_key)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }

    def _stub_post(self, title: str, platform: str, scheduled_at: str | None) -> dict[str, Any]:
        return {
            "job_id": f"stub_repurpose_{int(time.time())}",
            "title": title,
            "platform": platform,
            "status": "scheduled" if scheduled_at else "queued",
            "scheduled_at": scheduled_at,
            "_stub": True,
        }

    # ── Workflow Management ───────────────────────────────────────────────────

    def list_workflows(self) -> list[dict[str, Any]]:
        """Return available workflows configured in Repurpose.io account."""
        if self.stub_mode:
            return [
                {"id": "stub_wf_linkedin", "name": "LinkedIn Publisher", "platform": "linkedin"},
                {"id": "stub_wf_youtube", "name": "YouTube Publisher", "platform": "youtube"},
            ]

        with httpx.Client(timeout=20) as client:
            resp = client.get(f"{self.base_url}/workflows", headers=self._headers())
            resp.raise_for_status()
            return resp.json().get("workflows", [])

    # ── Post Scheduling ───────────────────────────────────────────────────────

    def schedule_text_post(
        self,
        workflow_id: str,
        title: str,
        body: str,
        *,
        platform: str = PLATFORM_LINKEDIN,
        scheduled_at: str | None = None,
        hashtags: list[str] | None = None,
        image_url: str | None = None,
    ) -> dict[str, Any]:
        """Schedule a text (LinkedIn post / SEO teaser) via a Repurpose.io workflow.

        Args:
            workflow_id:  ID of the target workflow from :meth:`list_workflows`.
            title:        Post headline / subject.
            body:         Full text body.
            platform:     Target platform identifier (default: linkedin).
            scheduled_at: ISO-8601 datetime string; if None, posts immediately.
            hashtags:     Optional list of hashtag strings without ``#``.
            image_url:    Optional header image URL.

        Returns:
            Dict with ``job_id``, ``status``, ``scheduled_at``.
        """
        if self.stub_mode:
            logger.info("Repurpose stub: schedule_text_post platform=%s", platform)
            return self._stub_post(title, platform, scheduled_at)

        payload: dict[str, Any] = {
            "workflow_id": workflow_id,
            "content": {
                "title": title,
                "body": body,
                "hashtags": hashtags or [],
            },
        }
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at
        if image_url:
            payload["content"]["image_url"] = image_url

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/posts",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Repurpose schedule_text_post HTTP error: %s", exc)
            raise

    def schedule_video_post(
        self,
        workflow_id: str,
        title: str,
        video_url: str,
        *,
        platform: str = PLATFORM_YOUTUBE,
        description: str = "",
        scheduled_at: str | None = None,
        hashtags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Schedule a video (short clip) for upload to YouTube / LinkedIn."""
        if self.stub_mode:
            logger.info("Repurpose stub: schedule_video_post platform=%s", platform)
            return self._stub_post(title, platform, scheduled_at)

        payload: dict[str, Any] = {
            "workflow_id": workflow_id,
            "content": {
                "title": title,
                "video_url": video_url,
                "description": description,
                "hashtags": hashtags or [],
            },
        }
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/posts",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Repurpose schedule_video_post HTTP error: %s", exc)
            raise

    def get_post_status(self, job_id: str) -> dict[str, Any]:
        """Check scheduling / publishing status for a post."""
        if self.stub_mode:
            return {"job_id": job_id, "status": "published", "_stub": True}

        with httpx.Client(timeout=20) as client:
            resp = client.get(f"{self.base_url}/posts/{job_id}", headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    # ── Webhook Verification ──────────────────────────────────────────────────

    @staticmethod
    def verify_webhook_signature(
        body: bytes,
        signature_header: str,
        secret: str | None = None,
    ) -> bool:
        """Verify ``X-Repurpose-Signature`` HMAC-SHA256.

        Header format: ``sha256=<hex_digest>``
        """
        key = (secret or settings.REPURPOSE_WEBHOOK_SECRET or "").encode()
        if not key:
            logger.warning("Repurpose webhook secret not set — skipping signature check")
            return True

        raw_sig = signature_header.removeprefix("sha256=")
        expected = hmac.new(key, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, raw_sig)
