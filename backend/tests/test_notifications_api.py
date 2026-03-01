"""Tests for notifications API endpoints"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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

    db.execute = AsyncMock(side_effect=_execute)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
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


def test_list_notifications_success():
    user = SimpleNamespace(id=101, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=9, user_id=101)
    notification = SimpleNamespace(
        id=1,
        supplier_id=9,
        conversation_id=30,
        notification_type="ai_handoff",
        title="Need handoff",
        message="Please review",
        is_read=0,
        metadata_json='{"a":1}',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db = _make_mock_db(execute_results=[[supplier], [notification]])
    _override_dependencies(user, db)

    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["notification_type"] == "ai_handoff"


def test_mark_notification_as_read_success():
    user = SimpleNamespace(id=102, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=10, user_id=102)
    notification = SimpleNamespace(
        id=2,
        supplier_id=10,
        conversation_id=44,
        notification_type="ai_handoff",
        title="Need handoff",
        message="Please review",
        is_read=0,
        metadata_json='{"a":2}',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db = _make_mock_db(execute_results=[[supplier], [notification]])
    _override_dependencies(user, db)

    response = client.post("/api/v1/notifications/2/read")
    assert response.status_code == 200
    assert response.json()["is_read"] == 1
