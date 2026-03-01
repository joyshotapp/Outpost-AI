import logging
import asyncio
import concurrent.futures
import re
import math
from typing import Optional

from celery import shared_task
from sqlalchemy import select

from app.database import async_session_maker
from app.config import settings
from app.models import KnowledgeDocument, Video, VideoLanguageVersion
from app.models.heygen_usage import HeyGenUsageRecord
from app.services.heygen import get_heygen_service
from app.services.pinecone_knowledge import get_pinecone_knowledge_service
from app.services.s3 import get_s3_service
from app.services.whisper import get_whisper_service

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# HeyGen cost logging helper  — Sprint 6
# ------------------------------------------------------------------

async def _log_heygen_usage(
    video_id: int,
    language_code: str,
    job_status: str,
    provider_job_id: Optional[str] = None,
    source_duration_seconds: Optional[float] = None,
    error_message: Optional[str] = None,
) -> None:
    """Write a HeyGenUsageRecord to the database.

    Cost estimate:  minutes = duration_seconds / 60
                    cost_usd = minutes * HEYGEN_COST_PER_MINUTE_USD
    """
    try:
        minutes: Optional[float] = None
        cost_usd: Optional[float] = None
        if job_status == "skipped":
            minutes = 0.0
            cost_usd = 0.0
        elif source_duration_seconds is not None and source_duration_seconds > 0:
            minutes = source_duration_seconds / 60.0
            cost_usd = minutes * settings.HEYGEN_COST_PER_MINUTE_USD

        async with async_session_maker() as session:
            record = HeyGenUsageRecord(
                video_id=video_id,
                language_code=language_code,
                provider_job_id=provider_job_id,
                job_status=job_status,
                source_duration_seconds=source_duration_seconds,
                minutes_processed=minutes,
                cost_usd=cost_usd,
                error_message=error_message,
            )
            session.add(record)
            await session.commit()
            logger.info(
                "HeyGen usage logged: video=%s lang=%s status=%s cost_usd=%s",
                video_id, language_code, job_status, cost_usd,
            )
    except Exception as exc:
        logger.warning("Failed to log HeyGen usage record: %s", exc)


_GERMAN_FILLER_WORDS_PATTERN = re.compile(
    r"\b(?:eigentlich|gewissermaßen|sozusagen|tatsächlich|wirklich|insbesondere|grundsätzlich)\b",
    flags=re.IGNORECASE,
)


def _word_count(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _compress_german_once(text: str) -> str:
    compacted = re.sub(r"\([^)]*\)", "", text)
    compacted = _GERMAN_FILLER_WORDS_PATTERN.sub("", compacted)
    compacted = compacted.replace("zum Beispiel", "z. B.")
    compacted = compacted.replace("unter anderem", "u. a.")
    return _normalize_text(compacted)


def optimize_german_script_duration(
    source_text: str,
    german_text: str,
    max_ratio: float = 1.1,
    max_passes: int = 3,
) -> dict:
    source_words = _word_count(source_text)
    german_words = _word_count(german_text)

    if source_words == 0 or german_words == 0:
        return {
            "applied": False,
            "passes": 0,
            "source_words": source_words,
            "original_words": german_words,
            "final_words": german_words,
            "original_ratio": 1.0,
            "final_ratio": 1.0,
            "text": _normalize_text(german_text),
        }

    original_ratio = german_words / source_words
    compressed_text = _normalize_text(german_text)
    passes = 0

    while passes < max_passes:
        current_ratio = _word_count(compressed_text) / source_words
        if current_ratio <= max_ratio:
            break
        compressed_text = _compress_german_once(compressed_text)
        passes += 1

    final_words = _word_count(compressed_text)
    final_ratio = final_words / source_words if source_words else 1.0

    if final_ratio > max_ratio:
        target_words = max(1, math.floor(source_words * max_ratio))
        words = compressed_text.split()
        compressed_text = " ".join(words[:target_words])
        final_words = _word_count(compressed_text)
        final_ratio = final_words / source_words if source_words else 1.0
        passes += 1

    return {
        "applied": final_ratio < original_ratio,
        "passes": passes,
        "source_words": source_words,
        "original_words": german_words,
        "final_words": final_words,
        "original_ratio": round(original_ratio, 3),
        "final_ratio": round(final_ratio, 3),
        "text": compressed_text,
    }


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _get_video(video_id: int) -> Optional[Video]:
    async with async_session_maker() as session:
        return await session.get(Video, video_id)


async def _save_transcript_document(
    video: Video,
    transcript_text: str,
    language: str,
    chunk_count: int,
    pinecone_document_id: str,
    namespace: str,
) -> int:
    async with async_session_maker() as session:
        doc = KnowledgeDocument(
            supplier_id=video.supplier_id,
            title=f"Video Transcript - {video.title}",
            source_type="transcript",
            source_s3_key=video.video_url,
            language=language,
            content_text=transcript_text,
            status="indexed",
            chunk_count=chunk_count,
            pinecone_namespace=namespace,
            pinecone_document_id=pinecone_document_id,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc.id


async def _upsert_video_language_version(
    video_id: int,
    language_code: str,
    title: str,
    description: str | None,
    subtitle_url: str | None,
    voice_url: str | None,
    cdn_url: str | None = None,
    localization_status: str = "pending",
    provider_job_id: str | None = None,
    compression_ratio: float | None = None,
    error_message: str | None = None,
) -> int:
    async with async_session_maker() as session:
        query = await session.execute(
            select(VideoLanguageVersion).where(
                VideoLanguageVersion.video_id == video_id,
                VideoLanguageVersion.language_code == language_code,
            )
        )
        record = query.scalars().first()

        if record:
            record.title = title
            record.description = description
            record.subtitle_url = subtitle_url
            record.voice_url = voice_url
            record.cdn_url = cdn_url
            record.localization_status = localization_status
            if provider_job_id is not None:
                record.provider_job_id = provider_job_id
            if compression_ratio is not None:
                record.compression_ratio = compression_ratio
            if error_message is not None:
                record.error_message = error_message
            await session.commit()
            return record.id

        record = VideoLanguageVersion(
            video_id=video_id,
            language_code=language_code,
            title=title,
            description=description,
            subtitle_url=subtitle_url,
            voice_url=voice_url,
            cdn_url=cdn_url,
            localization_status=localization_status,
            provider_job_id=provider_job_id,
            compression_ratio=compression_ratio,
            error_message=error_message,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record.id


@shared_task(name="app.tasks.video.process_video_metadata")
def process_video_metadata(video_id: int, video_url: str) -> dict:
    """
    Process video metadata asynchronously

    Args:
        video_id: ID of the video in database
        video_url: S3 URL of the video

    Returns:
        Task result with extracted metadata
    """
    try:
        logger.info(f"Processing metadata for video {video_id}: {video_url}")

        result = {
            "status": "processed",
            "video_id": video_id,
            "duration_seconds": 120,
            "width": 1920,
            "height": 1080,
            "codec": "h264",
            "bitrate": "5000k",
        }

        return result
    except Exception as e:
        logger.error(f"Failed to process video metadata for {video_id}: {str(e)}")
        raise


@shared_task(name="app.tasks.video.generate_thumbnails")
def generate_thumbnails(video_id: int, video_url: str, timestamps: list = None) -> dict:
    """
    Generate video thumbnails at specific timestamps

    Args:
        video_id: ID of the video in database
        video_url: S3 URL of the video
        timestamps: List of timestamps in seconds (default: [10, 30, 60])

    Returns:
        Task result with thumbnail URLs
    """
    if timestamps is None:
        timestamps = [10, 30, 60]

    try:
        logger.info(
            f"Generating thumbnails for video {video_id} at {timestamps}"
        )

        thumbnails = []
        for ts in timestamps:
            thumbnails.append({
                "timestamp": ts,
                "url": f"https://s3.example.com/thumbnails/video_{video_id}_{ts}.jpg",
            })

        result = {
            "status": "generated",
            "video_id": video_id,
            "thumbnails": thumbnails,
        }

        return result
    except Exception as e:
        logger.error(f"Failed to generate thumbnails for video {video_id}: {str(e)}")
        raise


@shared_task(bind=True, max_retries=3, name="app.tasks.video.transcribe_video_with_whisper")
def transcribe_video_with_whisper(self, video_id: int) -> dict:
    try:
        video = _run_async(_get_video(video_id))
        if not video:
            return {
                "success": False,
                "error": "Video not found",
            }

        whisper_service = get_whisper_service()
        transcript_result = _run_async(whisper_service.transcribe_video_url(video.video_url))

        if not transcript_result.get("success"):
            raise ValueError(transcript_result.get("error", "Whisper transcription failed"))

        transcript_text = transcript_result.get("text", "").strip()
        if not transcript_text:
            raise ValueError("Whisper returned empty transcript")

        language = transcript_result.get("language", "en")

        pinecone_service = get_pinecone_knowledge_service()
        pinecone_service.ensure_supplier_namespace(video.supplier_id)
        indexing_result = pinecone_service.upsert_document_chunks(
            supplier_id=video.supplier_id,
            title=f"Video Transcript - {video.title}",
            source_type="transcript",
            language=language,
            text=transcript_text,
        )

        knowledge_document_id = _run_async(
            _save_transcript_document(
                video=video,
                transcript_text=transcript_text,
                language=language,
                chunk_count=indexing_result["chunk_count"],
                pinecone_document_id=indexing_result["document_id"],
                namespace=indexing_result["namespace"],
            )
        )

        return {
            "success": True,
            "video_id": video_id,
            "knowledge_document_id": knowledge_document_id,
            "chunk_count": indexing_result["chunk_count"],
            "language": language,
        }
    except Exception as exc:
        logger.error("Video transcription failed for %s: %s", video_id, str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def generate_multilingual_video_versions_core(
    video_id: int,
    target_languages: list[str],
    source_language: str = "en",
) -> dict:
    video = await _get_video(video_id)
    if not video:
        return {"success": False, "error": "Video not found", "video_id": video_id}

    whisper_service = get_whisper_service()
    transcript_result = await whisper_service.transcribe_video_url(video.video_url, language=source_language)
    if not transcript_result.get("success"):
        return {
            "success": False,
            "error": transcript_result.get("error", "Transcription failed"),
            "video_id": video_id,
        }

    transcript_text = (transcript_result.get("text") or "").strip()
    if not transcript_text:
        return {"success": False, "error": "Empty transcript", "video_id": video_id}

    heygen_service = get_heygen_service()
    s3_service = get_s3_service()
    created_versions: list[dict] = []

    normalized_targets = sorted({lang.strip().lower() for lang in target_languages if lang and lang.strip()})
    for language_code in normalized_targets:
        if language_code == source_language.lower():
            continue

        result = await heygen_service.generate_localized_assets(
            source_video_url=video.video_url,
            source_language=source_language,
            target_language=language_code,
            transcript_text=transcript_text,
        )

        if not result.get("success"):
            error_msg = result.get("error", "Localization failed")
            # Persist failed status to DB so status API can reflect it
            await _upsert_video_language_version(
                video_id=video.id,
                language_code=language_code,
                title=f"{video.title} ({language_code.upper()})",
                description=None,
                subtitle_url=None,
                voice_url=None,
                cdn_url=None,
                localization_status="failed",
                error_message=error_msg,
            )
            await _log_heygen_usage(
                video_id=video.id,
                language_code=language_code,
                job_status="failed",
                provider_job_id=result.get("provider_job_id"),
                source_duration_seconds=video.duration_seconds,
                error_message=error_msg,
            )
            created_versions.append({
                "language_code": language_code,
                "success": False,
                "error": error_msg,
            })
            continue

        title = f"{video.title} ({language_code.upper()})"
        compression_info = None

        translated_text = (
            result.get("translated_text")
            or result.get("translated_script")
            or ""
        )

        if language_code == "de" and translated_text:
            compression_info = optimize_german_script_duration(
                source_text=transcript_text,
                german_text=translated_text,
                max_ratio=settings.GERMAN_TRANSLATION_MAX_RATIO,
                max_passes=settings.GERMAN_COMPRESSION_MAX_PASSES,
            )

        is_skipped = bool(result.get("skipped"))
        status = "pending" if is_skipped else "completed"
        subtitle_url = result.get("subtitle_url")
        voice_url = result.get("voice_url")
        cdn_url = None

        if not is_skipped:
            provider_job_id = result.get("provider_job_id")

            if provider_job_id and hasattr(heygen_service, "get_job_status"):
                await _upsert_video_language_version(
                    video_id=video.id,
                    language_code=language_code,
                    title=title,
                    description=f"Localization in progress ({language_code.upper()})",
                    subtitle_url=subtitle_url,
                    voice_url=voice_url,
                    cdn_url=None,
                    localization_status="processing",
                    provider_job_id=provider_job_id,
                )

                poll_result = {"status": "processing"}
                for _ in range(3):
                    poll_result = await heygen_service.get_job_status(provider_job_id)
                    polled_status = (poll_result.get("status") or "processing").lower()
                    if polled_status in ("completed", "failed"):
                        break
                    await asyncio.sleep(2)

                polled_status = (poll_result.get("status") or "processing").lower()
                if polled_status == "failed":
                    error_msg = poll_result.get("error") or "HeyGen localization job failed"
                    await _upsert_video_language_version(
                        video_id=video.id,
                        language_code=language_code,
                        title=title,
                        description=None,
                        subtitle_url=subtitle_url,
                        voice_url=voice_url,
                        cdn_url=None,
                        localization_status="failed",
                        provider_job_id=provider_job_id,
                        error_message=error_msg,
                    )
                    await _log_heygen_usage(
                        video_id=video.id,
                        language_code=language_code,
                        job_status="failed",
                        provider_job_id=provider_job_id,
                        source_duration_seconds=video.duration_seconds,
                        error_message=error_msg,
                    )
                    created_versions.append({
                        "language_code": language_code,
                        "success": False,
                        "error": error_msg,
                        "provider_job_id": provider_job_id,
                    })
                    continue

                if polled_status == "completed":
                    subtitle_url = poll_result.get("subtitle_url") or subtitle_url
                    voice_url = poll_result.get("voice_url") or voice_url
                    status = "completed"
                else:
                    status = "processing"

        if voice_url:
            cdn_url = s3_service.get_cdn_url(voice_url)

        description = (
            f"Auto-localized from {source_language.upper()} via HeyGen"
            if not is_skipped
            else f"Localization requested ({language_code.upper()}) — waiting for HeyGen key"
        )
        if compression_info and compression_info.get("applied"):
            description = (
                f"{description}; DE compression {compression_info['original_ratio']}→"
                f"{compression_info['final_ratio']}"
            )

        version_id = await _upsert_video_language_version(
            video_id=video.id,
            language_code=language_code,
            title=title,
            description=description,
            subtitle_url=subtitle_url,
            voice_url=voice_url,
            cdn_url=cdn_url,
            localization_status=status,
            provider_job_id=result.get("provider_job_id"),
            compression_ratio=(
                compression_info.get("final_ratio") if compression_info else None
            ),
        )

        created_versions.append({
            "language_code": language_code,
            "success": status in ("completed", "processing", "pending"),
            "skipped": is_skipped,
            "status": status,
            "provider_job_id": result.get("provider_job_id"),
            "video_language_version_id": version_id,
            "compression": compression_info,
            "cdn_url": cdn_url,
        })

        # Log HeyGen usage for cost tracking only when status is final
        if status in ("completed", "skipped"):
            await _log_heygen_usage(
                video_id=video.id,
                language_code=language_code,
                job_status=status,
                provider_job_id=result.get("provider_job_id"),
                source_duration_seconds=video.duration_seconds,
            )

    return {
        "success": True,
        "video_id": video_id,
        "source_language": source_language,
        "target_languages": normalized_targets,
        "versions": created_versions,
    }


@shared_task(bind=True, max_retries=2, name="app.tasks.video.generate_multilingual_video_versions")
def generate_multilingual_video_versions(
    self,
    video_id: int,
    target_languages: list[str] | None = None,
    source_language: str = "en",
) -> dict:
    if target_languages is None:
        target_languages = ["de", "ja", "es", "zh"]

    try:
        return _run_async(
            generate_multilingual_video_versions_core(
                video_id=video_id,
                target_languages=target_languages,
                source_language=source_language,
            )
        )
    except Exception as exc:
        logger.error("Multilingual generation failed for %s: %s", video_id, str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
