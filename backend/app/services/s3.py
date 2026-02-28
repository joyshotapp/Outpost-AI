"""S3 file upload service with Presigned URL and MIME validation"""

import mimetypes
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class S3Service:
    """Service for S3 file operations"""

    ALLOWED_MIME_TYPES = {
        # Videos
        "video/mp4": ["mp4"],
        "video/quicktime": ["mov"],
        "video/x-msvideo": ["avi"],
        "video/x-matroska": ["mkv"],
        "video/webm": ["webm"],
        # Images
        "image/jpeg": ["jpg", "jpeg"],
        "image/png": ["png"],
        "image/webp": ["webp"],
        "image/gif": ["gif"],
        # Documents
        "application/pdf": ["pdf"],
        "application/msword": ["doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
            "docx"
        ],
        "application/vnd.ms-excel": ["xls"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ["xlsx"],
    }

    MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB

    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.AWS_S3_BUCKET

    def validate_mime_type(self, filename: str, mime_type: Optional[str] = None) -> bool:
        """
        Validate if MIME type is allowed

        Args:
            filename: Original filename
            mime_type: MIME type from client (optional, can be inferred from filename)

        Returns:
            True if MIME type is allowed, False otherwise
        """
        # Infer from filename if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)

        if not mime_type:
            return False

        return mime_type in self.ALLOWED_MIME_TYPES

    def get_allowed_extensions(self) -> list[str]:
        """Get list of allowed file extensions"""
        extensions = []
        for exts in self.ALLOWED_MIME_TYPES.values():
            extensions.extend(exts)
        return sorted(set(extensions))

    def generate_presigned_url(
        self,
        object_key: str,
        expiration_hours: int = 24,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        Generate presigned URL for S3 upload

        Args:
            object_key: S3 object key (path)
            expiration_hours: URL expiration in hours
            file_size: Expected file size (optional)
            content_type: MIME type (optional)

        Returns:
            Dict with presigned URL and other metadata

        Raises:
            ValueError: If file size exceeds max allowed
            ValueError: If MIME type is not allowed
        """
        # Validate file size
        if file_size and file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_size} exceeds maximum {self.MAX_FILE_SIZE}"
            )

        # Validate MIME type if provided
        if content_type and content_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type {content_type} is not allowed")

        try:
            # Build request parameters
            params = {
                "Bucket": self.bucket,
                "Key": object_key,
                "Expires": expiration_hours * 3600,
            }

            # Add content type if provided
            if content_type:
                params["ContentType"] = content_type

            # Generate presigned POST (better for browser uploads)
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=object_key,
                ExpiresIn=expiration_hours * 3600,
                Conditions=[
                    ["content-length-range", 0, self.MAX_FILE_SIZE],
                ] + (
                    [["eq", "$Content-Type", content_type]]
                    if content_type
                    else []
                ),
            )

            return {
                "url": response["url"],
                "fields": response["fields"],
                "expires_at": (
                    datetime.utcnow() + timedelta(hours=expiration_hours)
                ).isoformat(),
                "max_file_size": self.MAX_FILE_SIZE,
            }
        except ClientError as e:
            raise ValueError(f"Failed to generate presigned URL: {str(e)}")

    def generate_object_key(
        self,
        resource_type: str,
        resource_id: int,
        filename: str,
    ) -> str:
        """
        Generate S3 object key based on resource type and ID

        Args:
            resource_type: Type of resource (videos, documents, etc.)
            resource_id: Resource ID (supplier_id, user_id, etc.)
            filename: Original filename

        Returns:
            S3 object key path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{resource_type}/{resource_id}/{timestamp}-{filename}"

    def delete_object(self, object_key: str) -> bool:
        """
        Delete object from S3

        Args:
            object_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def get_object_url(self, object_key: str, expiration_hours: int = 24) -> str:
        """
        Get public URL for S3 object

        Args:
            object_key: S3 object key
            expiration_hours: URL expiration in hours

        Returns:
            Presigned URL for downloading/viewing
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiration_hours * 3600,
            )
            return url
        except ClientError:
            return None

    def check_object_exists(self, object_key: str) -> bool:
        """
        Check if object exists in S3

        Args:
            object_key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get or create S3 service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
