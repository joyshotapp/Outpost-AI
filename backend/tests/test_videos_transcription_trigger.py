"""Tests for video transcription trigger on video creation"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app

client = TestClient(app)


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return self._items


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarsResult(self._items)


def _make_mock_db(execute_results=None):
    db = AsyncMock()
    queue = list(execute_results or [])

    async def _execute(*_args, **_kwargs):
        items = queue.pop(0) if queue else []
        return _ExecuteResult(items)

    def _add(entity):
        if getattr(entity, "id", None) is None:
            entity.id = 1
        if getattr(entity, "created_at", None) is None:
            entity.created_at = datetime.utcnow().isoformat()
        if getattr(entity, "updated_at", None) is None:
            entity.updated_at = datetime.utcnow().isoformat()

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock(side_effect=_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


def _override_dependencies(current_user, db):
    async def _get_user_override():
        return current_user

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_current_user] = _get_user_override
    app.dependency_overrides[get_db] = _get_db_override


def setup_function():
    app.dependency_overrides = {}


def teardown_function():
    app.dependency_overrides = {}


def test_create_video_enqueues_whisper_transcription():
    current_user = SimpleNamespace(id=100, role="supplier")
    supplier = SimpleNamespace(id=7, user_id=100)
    db = _make_mock_db(execute_results=[[supplier], []])
    _override_dependencies(current_user, db)

    with patch("app.api.v1.videos.transcribe_video_with_whisper") as mock_task:
        response = client.post(
            "/api/v1/videos",
            json={
                "supplier_id": 7,
                "title": "Video Title",
                "video_url": "https://s3.example.com/video.mp4",
            },
        )

    assert response.status_code == 201
    video_id = response.json()["id"]
    mock_task.delay.assert_called_once_with(video_id)
