"""HeyGen service adapter for Sprint 6 multilingual video generation."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class HeyGenService:
    """Service wrapper around HeyGen translation APIs."""

    def __init__(self):
        self.api_key = settings.HEYGEN_API_KEY
        self.base_url = "https://api.heygen.com/v2"

    async def generate_localized_assets(
        self,
        source_video_url: str,
        source_language: str,
        target_language: str,
        transcript_text: str,
    ) -> dict[str, Any]:
        if not self.api_key:
            return {
                "success": True,
                "skipped": True,
                "reason": "HEYGEN_API_KEY not configured",
                "subtitle_url": None,
                "voice_url": None,
                "provider_job_id": None,
            }

        payload = {
            "video_url": source_video_url,
            "source_language": source_language,
            "target_language": target_language,
            "script": transcript_text,
            "output": {"subtitle": True, "voice": True},
        }

        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/video/translate",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json() if response.content else {}

            return {
                "success": True,
                "subtitle_url": data.get("subtitle_url"),
                "voice_url": data.get("voice_url"),
                "provider_job_id": data.get("job_id"),
                "skipped": False,
            }
        except Exception as exc:
            logger.error("HeyGen localization failed (%s): %s", target_language, str(exc))
            return {
                "success": False,
                "error": str(exc),
                "subtitle_url": None,
                "voice_url": None,
                "provider_job_id": None,
                "skipped": False,
            }


    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Poll the HeyGen job status endpoint.

        Returns a dict with keys:
            status: "pending" | "processing" | "completed" | "failed"
            subtitle_url: optional URL returned on completion
            voice_url: optional URL returned on completion
            error: error string if failed
        """
        if not self.api_key:
            return {"status": "skipped", "skipped": True, "reason": "HEYGEN_API_KEY not configured"}

        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/video/translate/{job_id}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json() if response.content else {}

            raw_status = data.get("status", "pending").lower()
            # Normalise HeyGen status values to our internal values
            status_map = {
                "pending": "pending",
                "processing": "processing",
                "running": "processing",
                "completed": "completed",
                "done": "completed",
                "failed": "failed",
                "error": "failed",
            }
            normalised = status_map.get(raw_status, "processing")

            return {
                "status": normalised,
                "subtitle_url": data.get("subtitle_url"),
                "voice_url": data.get("voice_url"),
                "error": data.get("error"),
                "skipped": False,
            }
        except Exception as exc:
            logger.error("HeyGen job status poll failed (%s): %s", job_id, str(exc))
            return {
                "status": "failed",
                "error": str(exc),
                "subtitle_url": None,
                "voice_url": None,
                "skipped": False,
            }


_heygen_service: HeyGenService | None = None


def get_heygen_service() -> HeyGenService:
    global _heygen_service
    if _heygen_service is None:
        _heygen_service = HeyGenService()
    return _heygen_service
