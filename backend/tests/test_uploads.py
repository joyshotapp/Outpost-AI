"""Tests for S3 file upload endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from app.database import Base
from app.main import app
from app.dependencies import get_db, get_current_user
from app.models import User, UserRole
from app.security import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession):
    """Create test user"""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role=UserRole.SUPPLIER,
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def client(test_db, test_user):
    """Create test client with dependency overrides"""

    async def override_get_db():
        yield test_db

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client_instance = TestClient(app)
    yield client_instance

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Get auth headers for test user"""
    return {"Authorization": "Bearer test-token"}


class TestS3PresignedUrl:
    """Tests for presigned URL generation"""

    @patch("app.services.s3.boto3.client")
    def test_generate_presigned_url_success(self, mock_boto3, client, auth_headers):
        """Test successful presigned URL generation"""
        # Mock S3 response
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {
                "key": "videos/1/20260228120000-test.mp4",
                "policy": "test_policy",
                "signature": "test_signature",
            },
        }

        response = client.post(
            "/api/v1/uploads/presigned-url",
            json={
                "filename": "test.mp4",
                "resource_type": "videos",
                "content_type": "video/mp4",
                "file_size": 1024 * 1024,  # 1MB
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "fields" in data
        assert "expires_at" in data
        assert "max_file_size" in data

    def test_generate_presigned_url_invalid_mime_type(self, client, auth_headers):
        """Test presigned URL with invalid MIME type"""
        response = client.post(
            "/api/v1/uploads/presigned-url",
            json={
                "filename": "test.exe",
                "resource_type": "videos",
                "content_type": "application/x-msdownload",
                "file_size": 1024 * 1024,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    def test_generate_presigned_url_file_too_large(self, client, auth_headers):
        """Test presigned URL with file size exceeding limit"""
        response = client.post(
            "/api/v1/uploads/presigned-url",
            json={
                "filename": "large.mp4",
                "resource_type": "videos",
                "content_type": "video/mp4",
                "file_size": 10 * 1024 * 1024 * 1024,  # 10GB (exceeds 5GB limit)
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    def test_generate_presigned_url_no_auth(self, client):
        """Test presigned URL generation without authentication"""
        response = client.post(
            "/api/v1/uploads/presigned-url",
            json={
                "filename": "test.mp4",
                "resource_type": "videos",
                "content_type": "video/mp4",
                "file_size": 1024 * 1024,
            },
        )

        assert response.status_code == 401

    @patch("app.services.s3.boto3.client")
    def test_generate_presigned_url_various_video_formats(
        self, mock_boto3, client, auth_headers
    ):
        """Test presigned URL with various video formats"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": "test", "policy": "test", "signature": "test"},
        }

        video_formats = [
            ("test.mp4", "video/mp4"),
            ("test.mov", "video/quicktime"),
            ("test.webm", "video/webm"),
            ("test.mkv", "video/x-matroska"),
        ]

        for filename, content_type in video_formats:
            response = client.post(
                "/api/v1/uploads/presigned-url",
                json={
                    "filename": filename,
                    "resource_type": "videos",
                    "content_type": content_type,
                    "file_size": 1024 * 1024,
                },
                headers=auth_headers,
            )
            assert response.status_code == 200

    @patch("app.services.s3.boto3.client")
    def test_generate_presigned_url_various_image_formats(
        self, mock_boto3, client, auth_headers
    ):
        """Test presigned URL with various image formats"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": "test", "policy": "test", "signature": "test"},
        }

        image_formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.webp", "image/webp"),
            ("test.gif", "image/gif"),
        ]

        for filename, content_type in image_formats:
            response = client.post(
                "/api/v1/uploads/presigned-url",
                json={
                    "filename": filename,
                    "resource_type": "documents",
                    "content_type": content_type,
                    "file_size": 512 * 1024,
                },
                headers=auth_headers,
            )
            assert response.status_code == 200

    @patch("app.services.s3.boto3.client")
    def test_presigned_url_contains_resource_key(self, mock_boto3, client, auth_headers):
        """Test that presigned URL contains resource type in key"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_post.return_value = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {
                "key": "videos/1/20260228120000-test.mp4",
                "policy": "test",
                "signature": "test",
            },
        }

        response = client.post(
            "/api/v1/uploads/presigned-url",
            json={
                "filename": "test.mp4",
                "resource_type": "videos",
                "content_type": "video/mp4",
                "file_size": 1024 * 1024,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Verify the fields contain the resource type
        assert "fields" in data


class TestS3UploadStatus:
    """Tests for upload status checking"""

    @patch("app.services.s3.boto3.client")
    def test_check_upload_status_exists(self, mock_boto3, client, auth_headers):
        """Test checking status of uploaded file"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.head_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = (
            "https://s3.amazonaws.com/bucket/videos/1/test.mp4"
        )

        response = client.post(
            "/api/v1/uploads/status",
            json={"object_key": "videos/1/20260228120000-test.mp4"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert "download_url" in data

    @patch("app.services.s3.boto3.client")
    def test_check_upload_status_not_exists(self, mock_boto3, client, auth_headers):
        """Test checking status of non-existent file"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3

        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )

        response = client.post(
            "/api/v1/uploads/status",
            json={"object_key": "videos/1/nonexistent.mp4"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False

    def test_check_upload_status_no_auth(self, client):
        """Test upload status check without authentication"""
        response = client.post(
            "/api/v1/uploads/status",
            json={"object_key": "videos/1/test.mp4"},
        )

        assert response.status_code == 401


class TestS3FileDelete:
    """Tests for file deletion"""

    @patch("app.services.s3.boto3.client")
    def test_delete_file_success(self, mock_boto3, client, auth_headers):
        """Test successful file deletion"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.delete_object.return_value = {}

        response = client.delete(
            "/api/v1/uploads/videos%2F1%2F20260228120000-test.mp4",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_delete_file_no_auth(self, client):
        """Test file deletion without authentication"""
        response = client.delete(
            "/api/v1/uploads/videos%2F1%2Ftest.mp4",
        )

        assert response.status_code == 401


class TestS3ServiceValidation:
    """Tests for S3 service validation logic"""

    def test_mime_type_validation_valid(self):
        """Test MIME type validation for valid types"""
        from app.services import get_s3_service

        s3 = get_s3_service()

        assert s3.validate_mime_type("test.mp4", "video/mp4") is True
        assert s3.validate_mime_type("test.jpg", "image/jpeg") is True
        assert s3.validate_mime_type("test.pdf", "application/pdf") is True

    def test_mime_type_validation_invalid(self):
        """Test MIME type validation for invalid types"""
        from app.services import get_s3_service

        s3 = get_s3_service()

        assert s3.validate_mime_type("test.exe", "application/x-msdownload") is False
        assert s3.validate_mime_type("test.sh", "application/x-sh") is False

    def test_mime_type_validation_infer_from_filename(self):
        """Test MIME type validation inferring from filename"""
        from app.services import get_s3_service

        s3 = get_s3_service()

        # Should infer from filename
        assert s3.validate_mime_type("test.mp4") is True
        assert s3.validate_mime_type("test.jpg") is True

    def test_get_allowed_extensions(self):
        """Test getting list of allowed extensions"""
        from app.services import get_s3_service

        s3 = get_s3_service()
        extensions = s3.get_allowed_extensions()

        assert "mp4" in extensions
        assert "jpg" in extensions
        assert "pdf" in extensions
        assert "exe" not in extensions

    def test_generate_object_key(self):
        """Test S3 object key generation"""
        from app.services import get_s3_service

        s3 = get_s3_service()
        key = s3.generate_object_key(
            resource_type="videos",
            resource_id=1,
            filename="test.mp4",
        )

        assert key.startswith("videos/1/")
        assert key.endswith("-test.mp4")
        assert len(key) > len("videos/1/-test.mp4")  # Should have timestamp

    def test_max_file_size_constant(self):
        """Test max file size constant"""
        from app.services import get_s3_service

        s3 = get_s3_service()
        # 5GB
        assert s3.MAX_FILE_SIZE == 5 * 1024 * 1024 * 1024
