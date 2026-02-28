"""Video API endpoints with multi-language support"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Video, VideoLanguageVersion, Supplier
from app.schemas import (
    VideoCreateRequest,
    VideoUpdateRequest,
    VideoResponse,
    VideoListResponse,
    VideoLanguageVersionRequest,
    VideoLanguageVersionResponse,
)

router = APIRouter(prefix="/videos", tags=["videos"])


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

    # Load language versions
    result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    video.language_versions = result.scalars().all()

    return VideoResponse.model_validate(video)


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

    return [VideoListResponse.model_validate(v) for v in videos]


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

    # Load language versions
    lang_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    video.language_versions = lang_result.scalars().all()

    return VideoResponse.model_validate(video)


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

    # Load language versions
    lang_result = await db.execute(
        select(VideoLanguageVersion).filter(
            VideoLanguageVersion.video_id == video.id
        )
    )
    video.language_versions = lang_result.scalars().all()

    return VideoResponse.model_validate(video)


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

    return VideoLanguageVersionResponse.model_validate(lang_version)


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

    return [VideoLanguageVersionResponse.model_validate(v) for v in versions]


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
