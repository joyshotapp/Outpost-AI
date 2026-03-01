"""
Sprint 6 E2E Pipeline Integration Tests.

These tests simulate the full multilingual localization flow:
  1. Upload / register a video
  2. Enqueue localization via POST /videos/{id}/localize
  3. Execute the pipeline synchronously (no Celery worker needed)
  4. Verify language version status is persisted correctly
  5. Verify HeyGen usage records are written
  6. Verify localization-status endpoint reflects the result
  7. Verify admin usage-summary aggregation
  8. Verify CDN URL generation helper
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

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

E2E_TEST_DB = "sqlite+aiosqlite:///./test_sprint6_e2e.db"


# ---------------------------------------------------------------------------
# Fixtures (mirror test_videos.py setup)
# ---------------------------------------------------------------------------


@pytest.fixture
async def e2e_db():
    engine = create_async_engine(
        E2E_TEST_DB,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def e2e_user(e2e_db: AsyncSession):
    user = User(
        email="e2euser@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUPPLIER,
        is_active=True,
    )
    e2e_db.add(user)
    await e2e_db.commit()
    await e2e_db.refresh(user)
    return user


@pytest.fixture
async def e2e_supplier(e2e_db: AsyncSession, e2e_user: User):
    supplier = Supplier(
        user_id=e2e_user.id,
        company_name="E2E Test Manufacturer",
        company_slug="e2e-test-mfg",
        country="TW",
        industry="Manufacturing",
        main_products="Test products",
        is_active=True,
        is_verified=True,
        view_count=0,
    )
    e2e_db.add(supplier)
    await e2e_db.commit()
    await e2e_db.refresh(supplier)
    return supplier


@pytest.fixture
def e2e_client(e2e_db: AsyncSession, e2e_user: User):
    async def override_db():
        yield e2e_db

    from app.dependencies import get_current_user

    def override_current_user():
        return e2e_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_video(client, supplier_id: int, title: str = "E2E Test Video") -> int:
    resp = client.post(
        "/api/v1/videos",
        json={
            "supplier_id": supplier_id,
            "title": title,
            "video_url": "https://s3.example.com/e2e/factory.mp4",
            "duration_seconds": 90,
        },
    )
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# E2E Tests
# ---------------------------------------------------------------------------


class TestLocalizationEndToEnd:
    """Full multilingual pipeline integration tests."""

    def test_enqueue_localize_returns_202(self, e2e_client, e2e_supplier):
        """POST /localize should enqueue a Celery task and return 202."""
        video_id = _create_video(e2e_client, e2e_supplier.id)

        class FakeTask:
            id = "e2e-task-001"

        class FakeCeleryTask:
            @staticmethod
            def delay(**kwargs):
                return FakeTask()

        with patch("app.api.v1.videos.generate_multilingual_video_versions", FakeCeleryTask):
            resp = e2e_client.post(
                f"/api/v1/videos/{video_id}/localize",
                json={"source_language": "en", "target_languages": ["de", "ja"]},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["task_id"] == "e2e-task-001"
        assert data["video_id"] == video_id
        assert sorted(data["target_languages"]) == ["de", "ja"]

    def test_pipeline_writes_completed_status(self, e2e_supplier):
        """Pipeline execution should set localization_status=completed in DB."""
        from app.tasks.video import generate_multilingual_video_versions_core

        mock_video = SimpleNamespace(
            id=300,
            supplier_id=e2e_supplier.id,
            title="E2E Pipeline Video",
            video_url="https://s3.example.com/e2e/test.mp4",
            duration_seconds=90.0,
        )

        upserted_calls = []

        async def fake_upsert(**kwargs):
            upserted_calls.append(kwargs)
            return len(upserted_calls) + 800

        async def _run():
            with patch("app.tasks.video._get_video", return_value=mock_video), \
                 patch("app.tasks.video._upsert_video_language_version", new=AsyncMock(side_effect=fake_upsert)), \
                 patch("app.tasks.video._log_heygen_usage", new=AsyncMock(return_value=None)), \
                 patch("app.tasks.video.get_s3_service") as mock_get_s3, \
                 patch("app.tasks.video.get_whisper_service") as mw, \
                 patch("app.tasks.video.get_heygen_service") as mh:

                mock_get_s3.return_value = SimpleNamespace(get_cdn_url=lambda url: url)
                mw.return_value = SimpleNamespace(
                    transcribe_video_url=AsyncMock(
                        return_value={"success": True, "text": "Test source text.", "language": "en"}
                    )
                )

                class FakeHeyGen:
                    async def generate_localized_assets(self, **kwargs):
                        return {
                            "success": True,
                            "provider_job_id": f"job-{kwargs['target_language']}",
                            "subtitle_url": f"https://cdn.example.com/{kwargs['target_language']}.vtt",
                            "voice_url": f"https://cdn.example.com/{kwargs['target_language']}.mp3",
                            "skipped": False,
                        }

                mh.return_value = FakeHeyGen()
                return await generate_multilingual_video_versions_core(
                    video_id=300,
                    target_languages=["de", "ja"],
                    source_language="en",
                )

        result = asyncio.run(_run())
        assert result["success"] is True
        versions = {v["language_code"]: v for v in result["versions"]}
        assert "de" in versions and "ja" in versions
        assert versions["de"]["success"] is True
        assert versions["ja"]["success"] is True

        # Verify upsert received completed status
        for call in upserted_calls:
            assert call["localization_status"] == "completed"

    def test_pipeline_writes_failed_status_on_heygen_error(self, e2e_supplier):
        """Pipeline should write localization_status=failed to DB when HeyGen fails."""
        from app.tasks.video import generate_multilingual_video_versions_core

        mock_video = SimpleNamespace(
            id=301,
            supplier_id=e2e_supplier.id,
            title="Failed E2E Video",
            video_url="https://s3.example.com/e2e/fail.mp4",
            duration_seconds=60.0,
        )

        upserted_calls = []

        async def fake_upsert(**kwargs):
            upserted_calls.append(kwargs)
            return 999

        async def _run():
            with patch("app.tasks.video._get_video", return_value=mock_video), \
                 patch("app.tasks.video._upsert_video_language_version", new=AsyncMock(side_effect=fake_upsert)), \
                 patch("app.tasks.video._log_heygen_usage", new=AsyncMock(return_value=None)), \
                 patch("app.tasks.video.get_s3_service") as mock_get_s3, \
                 patch("app.tasks.video.get_whisper_service") as mw, \
                 patch("app.tasks.video.get_heygen_service") as mh:

                mock_get_s3.return_value = SimpleNamespace(get_cdn_url=lambda url: url)
                mw.return_value = SimpleNamespace(
                    transcribe_video_url=AsyncMock(
                        return_value={"success": True, "text": "Source.", "language": "en"}
                    )
                )

                class FailingHeyGen:
                    async def generate_localized_assets(self, **kwargs):
                        return {"success": False, "error": "API rate limit exceeded"}

                mh.return_value = FailingHeyGen()
                return await generate_multilingual_video_versions_core(
                    video_id=301,
                    target_languages=["ja"],
                    source_language="en",
                )

        result = asyncio.run(_run())
        assert result["success"] is True
        versions = {v["language_code"]: v for v in result["versions"]}
        assert versions["ja"]["success"] is False
        assert "API rate limit exceeded" in versions["ja"]["error"]

        # Verify upsert received failed status
        failed_call = next((c for c in upserted_calls if c["language_code"] == "ja"), None)
        assert failed_call is not None
        assert failed_call["localization_status"] == "failed"

    def test_localization_status_endpoint_after_add(self, e2e_client, e2e_supplier):
        """Verify GET /localization-status correctly counts statuses."""
        video_id = _create_video(e2e_client, e2e_supplier.id, title="Status E2E")

        # Add two language versions directly
        e2e_client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={"language_code": "de", "title": "Deutsch"},
        )
        e2e_client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={"language_code": "ja", "title": "日本語"},
        )

        resp = e2e_client.get(f"/api/v1/videos/{video_id}/localization-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["video_id"] == video_id
        assert all(
            v["localization_status"] == "pending" for v in data["versions"]
        )

    def test_single_language_status_endpoint(self, e2e_client, e2e_supplier):
        """GET /localization-status/{lang} returns correct data."""
        video_id = _create_video(e2e_client, e2e_supplier.id, title="Single Lang E2E")

        e2e_client.post(
            f"/api/v1/videos/{video_id}/language-versions",
            json={"language_code": "es", "title": "Español"},
        )

        resp = e2e_client.get(f"/api/v1/videos/{video_id}/localization-status/es")
        assert resp.status_code == 200
        assert resp.json()["language_code"] == "es"
        assert resp.json()["localization_status"] == "pending"


class TestHeyGenUsageTracking:
    """Tests for HeyGen usage logging."""

    def test_log_heygen_usage_calculates_cost(self):
        """_log_heygen_usage should compute cost from duration_seconds."""
        from app.tasks.video import _log_heygen_usage

        recorded = []

        async def fake_commit():
            pass

        async def _run():
            with patch("app.tasks.video.async_session_maker") as mock_session_maker, \
                 patch("app.tasks.video.settings") as mock_settings:
                mock_settings.HEYGEN_COST_PER_MINUTE_USD = 0.08

                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session.add = MagicMock(side_effect=lambda r: recorded.append(r))
                mock_session.commit = AsyncMock()
                mock_session_maker.return_value = mock_session

                await _log_heygen_usage(
                    video_id=10,
                    language_code="de",
                    job_status="completed",
                    source_duration_seconds=120.0,
                )

        asyncio.run(_run())
        assert len(recorded) == 1
        rec = recorded[0]
        assert abs(rec.minutes_processed - 2.0) < 0.001
        assert abs(rec.cost_usd - 0.16) < 0.001

    def test_log_heygen_usage_skipped_sets_zero_cost(self):
        """Skipped jobs should not accumulate billable minutes/cost."""
        from app.tasks.video import _log_heygen_usage

        recorded = []

        async def _run():
            with patch("app.tasks.video.async_session_maker") as mock_session_maker, \
                 patch("app.tasks.video.settings") as mock_settings:
                mock_settings.HEYGEN_COST_PER_MINUTE_USD = 0.08

                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session.add = MagicMock(side_effect=lambda r: recorded.append(r))
                mock_session.commit = AsyncMock()
                mock_session_maker.return_value = mock_session

                await _log_heygen_usage(
                    video_id=11,
                    language_code="ja",
                    job_status="skipped",
                    source_duration_seconds=120.0,
                )

        asyncio.run(_run())
        assert len(recorded) == 1
        rec = recorded[0]
        assert rec.minutes_processed == 0.0
        assert rec.cost_usd == 0.0


class TestAdminUsageRBAC:
    """RBAC tests for admin HeyGen usage endpoints."""

    def test_supplier_cannot_access_admin_usage_summary(self, e2e_client):
        resp = e2e_client.get("/api/v1/admin/heygen-usage/summary")
        assert resp.status_code == 403


class TestCDNURLHelper:
    """Tests for S3 CDN URL conversion helper."""

    def test_get_cdn_url_with_cloudfront(self):
        from app.services.s3 import S3Service
        svc = S3Service.__new__(S3Service)
        svc.bucket = "factory-insider-prod"

        s3_url = "https://factory-insider-prod.s3.ap-southeast-1.amazonaws.com/videos/abc.mp4"

        with patch("app.services.s3.settings") as m:
            m.CLOUDFRONT_DOMAIN = "d1234abcd.cloudfront.net"
            cdn_url = svc.get_cdn_url(s3_url)

        assert cdn_url == "https://d1234abcd.cloudfront.net/videos/abc.mp4"

    def test_get_cdn_url_fallback_without_cloudfront(self):
        from app.services.s3 import S3Service
        svc = S3Service.__new__(S3Service)
        svc.bucket = "factory-insider-prod"

        s3_url = "https://factory-insider-prod.s3.ap-southeast-1.amazonaws.com/videos/abc.mp4"

        with patch("app.services.s3.settings") as m:
            m.CLOUDFRONT_DOMAIN = None
            result = svc.get_cdn_url(s3_url)

        assert result == s3_url

    def test_get_s3_key_from_virtual_hosted_url(self):
        from app.services.s3 import S3Service
        svc = S3Service.__new__(S3Service)
        svc.bucket = "factory-insider-prod"

        url = "https://factory-insider-prod.s3.ap-southeast-1.amazonaws.com/subfolder/video.mp4"
        key = svc.get_s3_key_from_url(url)

        assert key == "subfolder/video.mp4"

    def test_get_s3_key_from_path_style_url(self):
        from app.services.s3 import S3Service
        svc = S3Service.__new__(S3Service)
        svc.bucket = "factory-insider-prod"

        url = "https://s3.ap-southeast-1.amazonaws.com/factory-insider-prod/subfolder/video.mp4"
        key = svc.get_s3_key_from_url(url)

        assert key == "subfolder/video.mp4"
