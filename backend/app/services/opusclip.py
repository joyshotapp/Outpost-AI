"""OpusClip API service adapter — Sprint 9 (Task 9.1).

OpusClip docs: https://docs.opus.pro/api
Key concepts:
  - Clip job : Submit a long video URL → OpusClip processes and returns N short clips
  - Each clip has a score (0-100) indicating highlight quality
  - Webhook POST fires when clip job completes (event: "clips.completed")

Authentication: Bearer token in Authorization header.

Stub mode: When OPUSCLIP_API_KEY is not set all methods return deterministic
stub objects so the pipeline can run fully without a live key.
"""

import hashlib
import hmac
import logging
import time
from typing import Any
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpusClipService:
    """Wrapper around the OpusClip REST API."""

    BASE_URL = settings.OPUSCLIP_API_BASE_URL

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key: str | None = api_key if api_key is not None else settings.OPUSCLIP_API_KEY
        self.base_url: str = base_url or self.BASE_URL
        self.stub_mode: bool = not bool(self.api_key)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }

    def _stub_job(self, video_url: str, n_clips: int) -> dict[str, Any]:
        job_id = f"stub_opusclip_{int(time.time())}"
        return {
            "job_id": job_id,
            "status": "processing",
            "video_url": video_url,
            "n_clips_requested": n_clips,
            "_stub": True,
        }

    def _stub_clips(self, job_id: str, n: int) -> list[dict[str, Any]]:
        clips = []
        for i in range(n):
            clips.append({
                "clip_id": f"{job_id}_clip_{i+1}",
                "url": f"https://stub.opusclip.com/clips/{job_id}_{i+1}.mp4",
                "duration_s": 45 + i * 5,
                "highlights_score": max(95 - i * 5, 40),
                "start_time_s": i * 60,
                "end_time_s": i * 60 + 45 + i * 5,
                "transcript_excerpt": f"[stub clip {i+1} transcript excerpt]",
                "_stub": True,
            })
        return clips

    # ── Job Management ────────────────────────────────────────────────────────

    def create_clip_job(
        self,
        video_url: str,
        *,
        n_clips: int | None = None,
        language: str = "en",
        target_duration_s: int = 60,
    ) -> dict[str, Any]:
        """Submit a long video for AI highlight clipping.

        Returns a job dict with ``job_id`` and ``status`` == "processing".
        """
        n_clips = n_clips or settings.OPUSCLIP_CLIPS_PER_VIDEO

        if self.stub_mode:
            logger.info("OpusClip stub: create_clip_job video_url=%s", video_url)
            return self._stub_job(video_url, n_clips)

        payload: dict[str, Any] = {
            "video_url": video_url,
            "num_clips": n_clips,
            "language": language,
            "target_duration_seconds": target_duration_s,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/clips",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("OpusClip create_clip_job HTTP error: %s", exc)
            raise

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Poll clip job status. Returns dict with ``status`` field:
        ``processing`` | ``completed`` | ``failed``.
        """
        if self.stub_mode:
            return {
                "job_id": job_id,
                "status": "completed",
                "_stub": True,
            }

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(
                    f"{self.base_url}/clips/{job_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("OpusClip get_job_status HTTP error: %s", exc)
            raise

    def get_clips(self, job_id: str) -> list[dict[str, Any]]:
        """Retrieve completed clips for a job.

        Returns a list of clip dicts, each with ``clip_id``, ``url``,
        ``duration_s``, ``highlights_score`` (0-100), ``transcript_excerpt``.
        """
        if self.stub_mode:
            return self._stub_clips(job_id, settings.OPUSCLIP_CLIPS_PER_VIDEO)

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(
                    f"{self.base_url}/clips/{job_id}/results",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("clips", [])
        except httpx.HTTPStatusError as exc:
            logger.error("OpusClip get_clips HTTP error: %s", exc)
            raise

    # ── Webhook Verification ──────────────────────────────────────────────────

    @staticmethod
    def verify_webhook_signature(
        body: bytes,
        signature_header: str,
        secret: str | None = None,
    ) -> bool:
        """Verify ``X-OpusClip-Signature`` HMAC-SHA256.

        Header format: ``sha256=<hex_digest>``
        """
        key = (secret or settings.OPUSCLIP_WEBHOOK_SECRET or "").encode()
        if not key:
            logger.warning("OpusClip webhook secret not set — skipping signature check")
            return True

        raw_sig = signature_header.removeprefix("sha256=")
        expected = hmac.new(key, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, raw_sig)
