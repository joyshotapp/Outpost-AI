"""S3 file upload endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    S3PresignedUrlRequest,
    S3PresignedUrlResponse,
    S3UploadStatusRequest,
    S3UploadStatusResponse,
)
from app.services import get_s3_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/presigned-url", response_model=S3PresignedUrlResponse)
async def generate_presigned_url(
    request: S3PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> S3PresignedUrlResponse:
    """
    Generate presigned URL for S3 file upload

    Args:
        request: Upload request with filename, resource_type, content_type, file_size
        current_user: Authenticated user
        db: Database session

    Returns:
        Presigned URL and upload fields

    Raises:
        HTTPException: If validation fails
    """
    s3_service = get_s3_service()

    # Validate MIME type
    if not s3_service.validate_mime_type(request.filename, request.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {request.content_type} is not allowed. "
            f"Allowed types: {', '.join(s3_service.ALLOWED_MIME_TYPES.keys())}",
        )

    # Validate file size
    if request.file_size > s3_service.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {s3_service.MAX_FILE_SIZE} bytes",
        )

    try:
        # Generate object key based on resource type and user ID
        object_key = s3_service.generate_object_key(
            resource_type=request.resource_type,
            resource_id=current_user.id,
            filename=request.filename,
        )

        # Generate presigned URL
        presigned_data = s3_service.generate_presigned_url(
            object_key=object_key,
            expiration_hours=24,
            file_size=request.file_size,
            content_type=request.content_type,
        )

        return S3PresignedUrlResponse(**presigned_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}",
        )


@router.post("/status", response_model=S3UploadStatusResponse)
async def check_upload_status(
    request: S3UploadStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> S3UploadStatusResponse:
    """
    Check if file was successfully uploaded to S3

    Args:
        request: Upload status request with object_key
        current_user: Authenticated user
        db: Database session

    Returns:
        Upload status and download URL if exists

    Raises:
        HTTPException: If check fails
    """
    s3_service = get_s3_service()

    try:
        # Check if object exists
        exists = s3_service.check_object_exists(request.object_key)

        if exists:
            # Get download URL
            download_url = s3_service.get_object_url(
                request.object_key, expiration_hours=24
            )
            return S3UploadStatusResponse(
                exists=True,
                object_key=request.object_key,
                download_url=download_url,
            )
        else:
            return S3UploadStatusResponse(exists=False)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check upload status: {str(e)}",
        )


@router.delete("/{object_key:path}")
async def delete_uploaded_file(
    object_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete uploaded file from S3

    Args:
        object_key: S3 object key to delete
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If deletion fails
    """
    s3_service = get_s3_service()

    try:
        # Delete the object
        success = s3_service.delete_object(object_key)

        if success:
            return {"message": "File deleted successfully", "object_key": object_key}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )
