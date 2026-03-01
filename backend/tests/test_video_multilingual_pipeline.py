"""Tests for Sprint 6 multilingual video pipeline and German compression logic."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.tasks.video import (
    generate_multilingual_video_versions_core,
    optimize_german_script_duration,
)


def test_optimize_german_script_duration_compresses_to_ratio_threshold():
    source_text = " ".join(["source"] * 10)
    german_text = " ".join(["deutsch"] * 24)

    result = optimize_german_script_duration(
        source_text=source_text,
        german_text=german_text,
        max_ratio=1.1,
        max_passes=2,
    )

    assert result["applied"] is True
    assert result["original_ratio"] > 1.1
    assert result["final_ratio"] <= 1.1
    assert result["final_words"] <= 11


def test_generate_multilingual_video_versions_core_includes_de_compression_metadata():
    mock_video = SimpleNamespace(
        id=200,
        supplier_id=50,
        title="Factory Introduction",
        video_url="https://s3.example.com/videos/factory.mp4",
        duration_seconds=120.0,
    )

    async def _run_test():
        with patch("app.tasks.video._get_video", new=AsyncMock(return_value=mock_video)), \
             patch("app.tasks.video._upsert_video_language_version", new=AsyncMock(side_effect=[901, 902])), \
             patch("app.tasks.video._log_heygen_usage", new=AsyncMock(return_value=None)), \
             patch("app.tasks.video.get_s3_service") as mock_get_s3, \
             patch("app.tasks.video.get_whisper_service") as mock_get_whisper, \
             patch("app.tasks.video.get_heygen_service") as mock_get_heygen:
            mock_get_s3.return_value = SimpleNamespace(
                get_cdn_url=lambda url: f"https://cdn.example.com/{url.split('/')[-1]}"
            )
            whisper_service = SimpleNamespace(
                transcribe_video_url=AsyncMock(
                    return_value={
                        "success": True,
                        "text": "This is our production process overview.",
                        "language": "en",
                    }
                )
            )
            mock_get_whisper.return_value = whisper_service

            class MockHeyGenService:
                async def generate_localized_assets(self, **kwargs):
                    if kwargs["target_language"] == "de":
                        return {
                            "success": True,
                            "provider_job_id": "job-de-1",
                            "subtitle_url": "https://cdn.example.com/de.vtt",
                            "voice_url": "https://cdn.example.com/de.mp3",
                            "translated_text": " ".join(["deutscher"] * 20),
                            "skipped": False,
                        }

                    return {
                        "success": True,
                        "provider_job_id": "job-ja-1",
                        "subtitle_url": "https://cdn.example.com/ja.vtt",
                        "voice_url": "https://cdn.example.com/ja.mp3",
                        "skipped": False,
                    }

            mock_get_heygen.return_value = MockHeyGenService()

            return await generate_multilingual_video_versions_core(
                video_id=200,
                target_languages=["de", "ja"],
                source_language="en",
            )

    result = asyncio.run(_run_test())

    assert result["success"] is True
    versions = {item["language_code"]: item for item in result["versions"]}

    assert versions["de"]["success"] is True
    assert versions["de"]["compression"] is not None
    assert versions["de"]["compression"]["applied"] is True
    assert versions["de"]["compression"]["final_ratio"] <= 1.1

    assert versions["ja"]["success"] is True
    assert versions["ja"]["compression"] is None


def test_generate_multilingual_video_versions_core_polls_and_persists_cdn_url():
    mock_video = SimpleNamespace(
        id=201,
        supplier_id=51,
        title="Factory Overview",
        video_url="https://s3.example.com/videos/factory2.mp4",
        duration_seconds=100.0,
    )

    upsert_calls = []

    async def fake_upsert(**kwargs):
        upsert_calls.append(kwargs)
        return 910 + len(upsert_calls)

    async def _run_test():
        with patch("app.tasks.video._get_video", new=AsyncMock(return_value=mock_video)), \
             patch("app.tasks.video._upsert_video_language_version", new=AsyncMock(side_effect=fake_upsert)), \
             patch("app.tasks.video._log_heygen_usage", new=AsyncMock(return_value=None)), \
             patch("app.tasks.video.get_s3_service") as mock_get_s3, \
             patch("app.tasks.video.get_whisper_service") as mock_get_whisper, \
             patch("app.tasks.video.get_heygen_service") as mock_get_heygen:
            mock_get_s3.return_value = SimpleNamespace(
                get_cdn_url=lambda url: "https://d123.cloudfront.net/voice/de.mp3"
            )

            mock_get_whisper.return_value = SimpleNamespace(
                transcribe_video_url=AsyncMock(
                    return_value={
                        "success": True,
                        "text": "Factory intro text.",
                        "language": "en",
                    }
                )
            )

            class MockHeyGenService:
                async def generate_localized_assets(self, **kwargs):
                    return {
                        "success": True,
                        "provider_job_id": "job-de-2",
                        "subtitle_url": None,
                        "voice_url": None,
                        "translated_text": "kurzer deutscher text",
                        "skipped": False,
                    }

                async def get_job_status(self, job_id: str):
                    return {
                        "status": "completed",
                        "subtitle_url": "https://s3.example.com/sub/de.vtt",
                        "voice_url": "https://s3.example.com/voice/de.mp3",
                    }

            mock_get_heygen.return_value = MockHeyGenService()

            return await generate_multilingual_video_versions_core(
                video_id=201,
                target_languages=["de"],
                source_language="en",
            )

    result = asyncio.run(_run_test())
    assert result["success"] is True
    assert result["versions"][0]["status"] == "completed"
    assert result["versions"][0]["cdn_url"] == "https://d123.cloudfront.net/voice/de.mp3"

    assert len(upsert_calls) == 2
    assert upsert_calls[0]["localization_status"] == "processing"
    assert upsert_calls[1]["localization_status"] == "completed"
    assert upsert_calls[1]["cdn_url"] == "https://d123.cloudfront.net/voice/de.mp3"
