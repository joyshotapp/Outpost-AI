"""Video API endpoints with multi-language support"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Video, VideoLanguageVersion, Supplier
from app.tasks.video import transcribe_video_with_whisper, generate_multilingual_video_versions
from app.schemas import (
    VideoCreateRequest,
    VideoUpdateRequest,
    VideoResponse,
    VideoListResponse,
    VideoLanguageVersionRequest,
    VideoLanguageVersionResponse,
    VideoLocalizationRequest,
    VideoLocalizationTaskResponse,
    LocalizationJobStatusResponse,
    VideoLocalizationStatusSummary,
)

router = APIRouter(prefix="/videos", tags=["videos"])
logger = logging.getLogger(__name__)


def _serialize_language_version_response(version: VideoLanguageVersion) -> VideoLanguageVersionResponse:
    return VideoLanguageVersionResponse(
        id=version.id,
        video_id=version.video_id,
        language_code=version.language_code,
        title=version.title,
        description=version.description,
        subtitle_url=version.subtitle_url,
        voice_url=version.voice_url,
        localization_status=version.localization_status or "pending",
        provider_job_id=version.provider_job_id,
        cdn_url=version.cdn_url,
        compression_ratio=version.compression_ratio,
        error_message=version.error_message,
        created_at=str(version.created_at),
        updated_at=str(version.updated_at),
    )


def _serialize_localization_status(version: VideoLanguageVersion) -> LocalizationJobStatusResponse:
    return LocalizationJobStatusResponse(
        video_id=version.video_id,
        language_code=version.language_code,
        localization_status=version.localization_status or "pending",
        provider_job_id=version.provider_job_id,
        cdn_url=version.cdn_url,
        compression_ratio=version.compression_ratio,
        error_message=version.error_message,
        subtitle_url=version.subtitle_url,
        voice_url=version.voice_url,
    )


def _serialize_video_response(video: Video, language_versions: list[VideoLanguageVersion]) -> VideoResponse:
    return VideoResponse(
        id=video.id,
        supplier_id=video.supplier_id,
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        video_type=video.video_type,
        is_published=video.is_published,
        view_count=video.view_count,
        created_at=str(video.created_at),
        updated_at=str(video.updated_at),
        language_versions=[
            _serialize_language_version_response(version)
            for version in language_versions
        ],
    )


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    request: VideoCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Create a new video"""
    # Verify supplier exists and user owns it
    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == request.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    if supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add videos to this supplier",
        )

    # Create video
    video = Video(
        supplier_id=request.supplier_id,
        title=request.title,
        description=request.description,
        video_url=request.video_url,
        thumbnail_url=request.thumbnail_url,
        duration_seconds=request.duration_seconds,
        video_type=request.video_type,
        is_published=True,
        view_count=0,
    )

    db.add(video)
    await db.flush()  # Get the video ID without committing

    # Add language versions if provided
    if request.language_versions:
        for lang_version in request.language_versions:
            video_lang = VideoLanguageVersion(
                video_id=video.id,
                language_code=lang_version.language_code,
                title=lang_version.title,
                description=lang_version.description,
                subtitle_url=lang_version.subtitle_url,
                voice_url=lang_version.voice_url,
            )
            db.add(video_lang)

    await db.commit()
    await db.refresh(video)

    try:
        transcribe_video_with_whisper.delay(video.id)
    except Exception as exc:
        logger.error("Failed to enqueue Whisper transcription for video %s: %s", video.id, str(exc))

    result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    language_versions = result.scalars().all()

    return _serialize_video_response(video, language_versions)


@router.get("", response_model=List[VideoListResponse])
async def list_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    supplier_id: int = Query(None),
    video_type: str = Query(None),
    is_published: bool = Query(None),
    db: AsyncSession = Depends(get_db),
) -> List[VideoListResponse]:
    """List videos with filtering"""
    query = select(Video)

    if supplier_id:
        query = query.filter(Video.supplier_id == supplier_id)
    if video_type:
        query = query.filter(Video.video_type == video_type)
    if is_published is not None:
        query = query.filter(Video.is_published == is_published)
    else:
        # Only show published videos by default in public list
        query = query.filter(Video.is_published == True)

    result = await db.execute(
        query.order_by(Video.created_at.desc()).offset(skip).limit(limit)
    )
    videos = result.scalars().all()

    return [
        VideoListResponse(
            id=video.id,
            supplier_id=video.supplier_id,
            title=video.title,
            video_type=video.video_type,
            thumbnail_url=video.thumbnail_url,
            is_published=video.is_published,
            view_count=video.view_count,
            created_at=str(video.created_at),
        )
        for video in videos
    ]


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Get video by ID with all language versions"""
    result = await db.execute(
        select(Video).filter(Video.id == video_id)
    )
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    lang_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    language_versions = lang_result.scalars().all()

    return _serialize_video_response(video, language_versions)


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    request: VideoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """Update video details"""
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Verify authorization
    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this video",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)

    await db.commit()
    await db.refresh(video)

    lang_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    language_versions = lang_result.scalars().all()

    return _serialize_video_response(video, language_versions)


@router.post("/{video_id}/language-versions", response_model=VideoLanguageVersionResponse)
async def add_language_version(
    video_id: int,
    request: VideoLanguageVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoLanguageVersionResponse:
    """Add or update language version for a video"""
    # Get video and verify authorization
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this video",
        )

    # Check if language version already exists
    existing = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video_id,
            VideoLanguageVersion.language_code == request.language_code,
        )
    )
    lang_version = existing.scalars().first()

    if lang_version:
        # Update existing
        lang_version.title = request.title
        lang_version.description = request.description
        lang_version.subtitle_url = request.subtitle_url
        lang_version.voice_url = request.voice_url
    else:
        # Create new
        lang_version = VideoLanguageVersion(
            video_id=video_id,
            language_code=request.language_code,
            title=request.title,
            description=request.description,
            subtitle_url=request.subtitle_url,
            voice_url=request.voice_url,
        )
        db.add(lang_version)

    await db.commit()
    await db.refresh(lang_version)

    return _serialize_language_version_response(lang_version)


@router.get("/{video_id}/language-versions", response_model=List[VideoLanguageVersionResponse])
async def list_language_versions(
    video_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[VideoLanguageVersionResponse]:
    """List all language versions for a video"""
    # Verify video exists
    result = await db.execute(select(Video).filter(Video.id == video_id))
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    lang_result = await db.execute(
        select(VideoLanguageVersion)
        .filter(VideoLanguageVersion.video_id == video_id)
        .order_by(VideoLanguageVersion.language_code)
    )
    versions = lang_result.scalars().all()

    return [_serialize_language_version_response(v) for v in versions]


@router.delete("/{video_id}/language-versions/{language_code}")
async def delete_language_version(
    video_id: int,
    language_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a language version"""
    # Get video and verify authorization
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this video",
        )

    # Delete language version
    lang_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video_id,
            VideoLanguageVersion.language_code == language_code,
        )
    )
    lang_version = lang_result.scalars().first()

    if not lang_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language version not found",
        )

    await db.delete(lang_version)
    await db.commit()

    return {"message": "Language version deleted successfully"}


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video (soft delete by unpublishing)"""
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Verify authorization
    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this video",
        )

    # Soft delete by unpublishing
    video.is_published = False
    await db.commit()


@router.post("/{video_id}/localize", response_model=VideoLocalizationTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def localize_video(
    video_id: int,
    request: VideoLocalizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoLocalizationTaskResponse:
    """Enqueue multilingual localization task for a video"""
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to localize this video",
        )

    try:
        task = generate_multilingual_video_versions.delay(
            video_id=video_id,
            target_languages=request.target_languages,
            source_language=request.source_language,
        )
    except Exception as exc:
        logger.error("Failed to enqueue multilingual localization for video %s: %s", video_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue localization task",
        )

    return VideoLocalizationTaskResponse(
        task_id=str(task.id),
        status="queued",
        video_id=video_id,
        source_language=request.source_language,
        target_languages=request.target_languages,
    )


@router.get("/{video_id}/localization-status", response_model=VideoLocalizationStatusSummary)
async def get_localization_status(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoLocalizationStatusSummary:
    """Return localization status for all language versions of a video"""
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this video",
        )

    versions_result = await db.execute(
        select(VideoLanguageVersion).filter(VideoLanguageVersion.video_id == video_id)
    )
    versions = list(versions_result.scalars().all())

    serialized = [_serialize_localization_status(v) for v in versions]
    completed = sum(1 for v in serialized if v.localization_status == "completed")
    failed = sum(1 for v in serialized if v.localization_status == "failed")
    pending = sum(1 for v in serialized if v.localization_status in ("pending", "processing"))

    return VideoLocalizationStatusSummary(
        video_id=video_id,
        versions=serialized,
        total=len(serialized),
        completed=completed,
        failed=failed,
        pending=pending,
    )


@router.get("/{video_id}/localization-status/{language_code}", response_model=LocalizationJobStatusResponse)
async def get_single_language_status(
    video_id: int,
    language_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LocalizationJobStatusResponse:
    """Return localization status for a single language version"""
    result = await db.execute(select(Video).filter(Video.id == video_id))
    video = result.scalars().first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == video.supplier_id)
    )
    supplier = supplier_result.scalars().first()

    if not supplier or supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this video",
        )

    version_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video_id,
            VideoLanguageVersion.language_code == language_code,
        )
    )
    version = version_result.scalars().first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language version '{language_code}' not found for this video",
        )

    return _serialize_localization_status(version)
