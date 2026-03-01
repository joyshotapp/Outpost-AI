"""Tests for video CRUD endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.dependencies import get_db
from app.models.base import Base
from app.models import User, Supplier, UserRole
from app.security import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_videos.db"


@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
        email="videouser@example.com",
        password_hash=hash_password("password123"),
        full_name="Video Test User",
        role=UserRole.SUPPLIER,
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_supplier(test_db: AsyncSession, test_user):
    """Create test supplier"""
    supplier = Supplier(
        user_id=test_user.id,
        company_name="Video Supplier Co",
        company_slug="video-supplier-co",
        country="US",
        is_active=True,
        is_verified=False,
        view_count=0,
    )
    test_db.add(supplier)
    await test_db.commit()
    await test_db.refresh(supplier)
    return supplier


@pytest.fixture
def client(test_db, test_user):
    """Create test client"""

    async def override_get_db():
        yield test_db

    from app.dependencies import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client_instance = TestClient(app)
    yield client_instance

    app.dependency_overrides.clear()


class TestVideoCreation:
    """Tests for video creation"""

    def test_create_video_success(self, client, test_supplier):
        """Test successful video creation"""
        response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Product Demo",
                "description": "Our product in action",
                "video_url": "https://s3.example.com/videos/demo.mp4",
                "thumbnail_url": "https://s3.example.com/thumbs/demo.jpg",
                "duration_seconds": 120,
                "video_type": "product",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Product Demo"
        assert data["supplier_id"] == test_supplier.id
        assert data["video_type"] == "product"
        assert data["is_published"] is True
        assert data["view_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_video_with_language_versions(self, client, test_supplier):
        """Test video creation with language versions"""
        response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Product Demo",
                "video_url": "https://s3.example.com/videos/demo.mp4",
                "language_versions": [
                    {
                        "language_code": "en",
                        "title": "Product Demo (English)",
                        "description": "English version",
                    },
                    {
                        "language_code": "zh",
                        "title": "产品演示（中文）",
                        "description": "Chinese version",
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["language_versions"]) == 2
        assert data["language_versions"][0]["language_code"] == "en"
        assert data["language_versions"][1]["language_code"] == "zh"

    def test_create_video_invalid_supplier(self, client):
        """Test video creation with non-existent supplier"""
        response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": 999,
                "title": "Test Video",
                "video_url": "https://s3.example.com/test.mp4",
            },
        )

        assert response.status_code == 404
        assert "Supplier not found" in response.json()["detail"]

    def test_create_video_unauthorized_supplier(self, client, test_db, test_user):
        """Test video creation for supplier owned by different user"""
        import asyncio

        async def create_other_supplier():
            other_user = User(
                email="otheruser@example.com",
                password_hash=hash_password("password123"),
                full_name="Other User",
                role=UserRole.SUPPLIER,
                is_active=True,
                is_verified=True,
            )
            test_db.add(other_user)
            await test_db.commit()

            other_supplier = Supplier(
                user_id=other_user.id,
                company_name="Other Company",
                company_slug="other-company",
                country="US",
                is_active=True,
                is_verified=False,
                view_count=0,
            )
            test_db.add(other_supplier)
            await test_db.commit()
            await test_db.refresh(other_supplier)
            return other_supplier

        loop = asyncio.get_event_loop()
        other_supplier = loop.run_until_complete(create_other_supplier())

        response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": other_supplier.id,
                "title": "Test Video",
                "video_url": "https://s3.example.com/test.mp4",
            },
        )

        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]


class TestVideoListing:
    """Tests for video listing"""

    def test_list_videos(self, client, test_supplier):
        """Test listing videos"""
        # Create videos
        client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video 1",
                "video_url": "https://s3.example.com/video1.mp4",
            },
        )
        client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video 2",
                "video_url": "https://s3.example.com/video2.mp4",
            },
        )

        response = client.get("/api/v1/videos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_videos_filter_by_supplier(self, client, test_supplier):
        """Test filtering videos by supplier"""
        client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video 1",
                "video_url": "https://s3.example.com/video1.mp4",
            },
        )

        response = client.get(f"/api/v1/videos?supplier_id={test_supplier.id}")
        assert response.status_code == 200
        data = response.json()
        assert all(v["supplier_id"] == test_supplier.id for v in data)

    def test_list_videos_filter_by_type(self, client, test_supplier):
        """Test filtering videos by type"""
        client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Product Video",
                "video_url": "https://s3.example.com/video.mp4",
                "video_type": "product",
            },
        )

        response = client.get("/api/v1/videos?video_type=product")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(v["video_type"] == "product" for v in data)

    def test_list_videos_pagination(self, client, test_supplier):
        """Test video list pagination"""
        response = client.get("/api/v1/videos?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10


class TestVideoRetrieval:
    """Tests for getting individual videos"""

    def test_get_video(self, client, test_supplier):
        """Test getting a video by ID"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Test Video",
                "video_url": "https://s3.example.com/test.mp4",
                "duration_seconds": 150,
            },
        )
        video_id = create_response.json()["id"]

        response = client.get(f"/api/v1/videos/{video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        assert data["title"] == "Test Video"
        assert data["duration_seconds"] == 150

    def test_get_video_not_found(self, client):
        """Test getting non-existent video"""
        response = client.get("/api/v1/videos/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestVideoUpdate:
    """Tests for updating videos"""

    def test_update_video(self, client, test_supplier):
        """Test updating video details"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Original Title",
                "video_url": "https://s3.example.com/test.mp4",
            },
        )
        video_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/videos/{video_id}",
            json={
                "title": "Updated Title",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"

    def test_update_video_unauthorized(self, client, test_db, test_user, test_supplier):
        """Test updating video without authorization"""
        import asyncio

        async def create_other_video():
            other_user = User(
                email="otheruser@example.com",
                password_hash=hash_password("password123"),
                full_name="Other User",
                role=UserRole.SUPPLIER,
                is_active=True,
                is_verified=True,
            )
            test_db.add(other_user)
            await test_db.commit()

            other_supplier = Supplier(
                user_id=other_user.id,
                company_name="Other Company",
                company_slug="other-company",
                country="US",
                is_active=True,
                is_verified=False,
                view_count=0,
            )
            test_db.add(other_supplier)
            await test_db.commit()

            from app.models import Video

            video = Video(
                supplier_id=other_supplier.id,
                title="Other Video",
                video_url="https://s3.example.com/other.mp4",
                is_published=True,
                view_count=0,
            )
            test_db.add(video)
            await test_db.commit()
            await test_db.refresh(video)
            return video

        loop = asyncio.get_event_loop()
        other_video = loop.run_until_complete(create_other_video())

        response = client.put(
            f"/api/v1/videos/{other_video.id}",
            json={"title": "Hacked Title"},
        )

        assert response.status_code == 403


class TestVideoLanguageVersions:
    """Tests for language version management"""

    def test_add_language_version(self, client, test_supplier):
        """Test adding a language version"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "English Title",
                "video_url": "https://s3.example.com/test.mp4",
            },
        )
        video_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={
                "language_code": "zh",
                "title": "Chinese Title",
                "description": "Chinese description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language_code"] == "zh"
        assert data["title"] == "Chinese Title"

    def test_list_language_versions(self, client, test_supplier):
        """Test listing language versions"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Test Video",
                "video_url": "https://s3.example.com/test.mp4",
                "language_versions": [
                    {"language_code": "en", "title": "English"},
                    {"language_code": "fr", "title": "French"},
                ],
            },
        )
        video_id = create_response.json()["id"]

        response = client.get(f"/api/v1/videos/{video_id}/language-versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        codes = [v["language_code"] for v in data]
        assert "en" in codes
        assert "fr" in codes

    def test_delete_language_version(self, client, test_supplier):
        """Test deleting a language version"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Test Video",
                "video_url": "https://s3.example.com/test.mp4",
                "language_versions": [
                    {"language_code": "en", "title": "English"},
                    {"language_code": "es", "title": "Spanish"},
                ],
            },
        )
        video_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/videos/{video_id}/language-versions/es")
        assert response.status_code == 200

        # Verify deleted
        list_response = client.get(f"/api/v1/videos/{video_id}/language-versions")
        data = list_response.json()
        codes = [v["language_code"] for v in data]
        assert "es" not in codes
        assert "en" in codes


class TestVideoDelete:
    """Tests for video deletion"""

    def test_delete_video(self, client, test_supplier):
        """Test deleting a video"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video to Delete",
                "video_url": "https://s3.example.com/delete.mp4",
            },
        )
        video_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/videos/{video_id}")
        assert response.status_code == 204

        # Verify soft-deleted (unpublished)
        get_response = client.get(f"/api/v1/videos/{video_id}")
        # Video should not appear in published list
        assert get_response.status_code == 404 or not get_response.json().get(
            "is_published", True
        )


class TestVideoLocalization:
    """Tests for multilingual localization task enqueue"""

    def test_localize_video_enqueue_success(self, client, test_supplier, monkeypatch):
        """Test enqueueing multilingual localization task"""

        class FakeTaskResult:
            id = "task-123"

        class FakeTask:
            @staticmethod
            def delay(**kwargs):
                assert kwargs["video_id"] > 0
                assert kwargs["source_language"] == "en"
                assert kwargs["target_languages"] == ["de", "ja"]
                return FakeTaskResult()

        monkeypatch.setattr("app.api.v1.videos.generate_multilingual_video_versions", FakeTask)

        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video to Localize",
                "video_url": "https://s3.example.com/localize.mp4",
            },
        )
        video_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/videos/{video_id}/localize",
            json={
                "source_language": "en",
                "target_languages": ["ja", "de", "ja"],
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "queued"
        assert data["video_id"] == video_id
        assert data["source_language"] == "en"
        assert data["target_languages"] == ["de", "ja"]

    def test_localize_video_empty_target_languages(self, client, test_supplier):
        """Test validation for empty target_languages"""
        create_response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Video to Validate",
                "video_url": "https://s3.example.com/validate.mp4",
            },
        )
        video_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/videos/{video_id}/localize",
            json={
                "source_language": "en",
                "target_languages": [],
            },
        )

        assert response.status_code == 422


class TestLocalizationStatus:
    """Tests for GET /videos/{id}/localization-status endpoints"""

    def test_get_localization_status_empty(self, client, test_supplier):
        """Newly created video has no language versions → returns empty list"""
        create_resp = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Status Test Video",
                "video_url": "https://s3.example.com/status.mp4",
            },
        )
        assert create_resp.status_code in (200, 201)
        video_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/videos/{video_id}/localization-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["video_id"] == video_id
        assert data["versions"] == []
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["failed"] == 0
        assert data["pending"] == 0

    def test_get_localization_status_with_versions(self, client, test_supplier):
        """Language versions created via the language-versions API are visible in status"""
        create_resp = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Status With Versions",
                "video_url": "https://s3.example.com/status2.mp4",
            },
        )
        video_id = create_resp.json()["id"]

        # Add a language version manually
        client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={
                "language_code": "de",
                "title": "Status Test DE",
                "description": "Deutsche Version",
            },
        )

        resp = client.get(f"/api/v1/videos/{video_id}/localization-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        version = data["versions"][0]
        assert version["language_code"] == "de"
        assert version["localization_status"] == "pending"

    def test_get_single_language_status(self, client, test_supplier):
        """Single language version status endpoint returns correct entry"""
        create_resp = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "Single Lang Status",
                "video_url": "https://s3.example.com/single.mp4",
            },
        )
        video_id = create_resp.json()["id"]

        client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={
                "language_code": "ja",
                "title": "Japanese Version",
            },
        )

        resp = client.get(f"/api/v1/videos/{video_id}/localization-status/ja")
        assert resp.status_code == 200
        data = resp.json()
        assert data["language_code"] == "ja"
        assert data["localization_status"] == "pending"
        assert data["video_id"] == video_id

    def test_get_single_language_status_not_found(self, client, test_supplier):
        """404 returned for non-existent language version"""
        create_resp = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": test_supplier.id,
                "title": "No Lang Video",
                "video_url": "https://s3.example.com/nolang.mp4",
            },
        )
        video_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/videos/{video_id}/localization-status/fr")
        assert resp.status_code == 404

    def test_localization_status_video_not_found(self, client):
        """404 returned when video_id doesn't exist"""
        resp = client.get("/api/v1/videos/99999/localization-status")
        assert resp.status_code == 404
