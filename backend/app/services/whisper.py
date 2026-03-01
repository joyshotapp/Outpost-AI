"""Whisper API service for video transcription"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhisperService:
    """Service for Whisper transcription API integration"""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for Whisper transcription")
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_API_BASE_URL.rstrip("/")
        self.model = settings.WHISPER_MODEL

    async def _download_video(self, video_url: str) -> Path:
        suffix = Path(video_url.split("?")[0]).suffix or ".mp4"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = Path(temp_file.name)
        temp_file.close()

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            temp_path.write_bytes(response.content)

        return temp_path

    async def transcribe_video_url(self, video_url: str, language: Optional[str] = None) -> dict:
        temp_path: Optional[Path] = None
        try:
            temp_path = await self._download_video(video_url)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }

            data = {
                "model": self.model,
                "response_format": "verbose_json",
            }
            if language:
                data["language"] = language

            with temp_path.open("rb") as media_file:
                files = {
                    "file": (temp_path.name, media_file, "application/octet-stream"),
                }
                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.post(
                        f"{self.base_url}/audio/transcriptions",
                        headers=headers,
                        data=data,
                        files=files,
                    )
                    response.raise_for_status()
                    payload = response.json()

            return {
                "success": True,
                "text": payload.get("text", ""),
                "language": payload.get("language", language or "unknown"),
                "duration": payload.get("duration"),
                "segments": payload.get("segments", []),
            }
        except Exception as exc:
            logger.error("Whisper transcription failed: %s", str(exc))
            return {
                "success": False,
                "error": str(exc),
            }
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)


_whisper_service: Optional[WhisperService] = None


def get_whisper_service() -> WhisperService:
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service
