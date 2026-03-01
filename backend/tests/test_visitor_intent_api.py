"""Tests for visitor intent API endpoints."""

import hashlib
import hmac
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.config import settings
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
    def __init__(self, items=None, scalar_value=None):
        self._items = items or []
        self._scalar_value = scalar_value

    def scalars(self):
        return _ScalarsResult(self._items)

    def scalar(self):
        return self._scalar_value


def _make_mock_db(execute_results=None):
    db = AsyncMock()
    queue = list(execute_results or [])
    added_entities = []

    async def _execute(*_args, **_kwargs):
        item = queue.pop(0) if queue else _ExecuteResult(items=[])
        return item

    def _add(entity):
        if getattr(entity, "id", None) is None:
            entity.id = 1
        if getattr(entity, "created_at", None) is None:
            entity.created_at = datetime.utcnow()
        if getattr(entity, "updated_at", None) is None:
            entity.updated_at = datetime.utcnow()
        added_entities.append(entity)

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock(side_effect=_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db._added_entities = added_entities
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


def test_ingest_visitor_event_success():
    db = _make_mock_db()

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override

    with patch("app.api.v1.visitor_intent.process_visitor_intent_event") as mock_task:
        response = client.post(
            "/api/v1/visitor-intent/events",
            json={
                "supplier_id": 7,
                "visitor_session_id": "visitor-123",
                "event_type": "page_view",
                "page_url": "/suppliers/acme",
                "event_data": {"source": "test"},
                "session_duration_seconds": 42,
                "consent_given": True,
            },
        )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] is True
    assert data["queued_for_scoring"] is True
    mock_task.delay.assert_called_once_with(1)


def test_ingest_visitor_event_without_consent_is_skipped():
    db = _make_mock_db()

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override

    response = client.post(
        "/api/v1/visitor-intent/events",
        json={
            "supplier_id": 7,
            "visitor_session_id": "visitor-123",
            "event_type": "page_view",
            "consent_given": False,
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] is False
    assert data["queued_for_scoring"] is False


def test_ingest_rb2b_webhook_success_with_valid_signature():
    db = _make_mock_db()

    async def _get_db_override():
        yield db

    payload = {
        "supplier_id": 7,
        "session_id": "rb2b-session-1",
        "event_type": "rfq_page_enter",
        "url": "/suppliers/acme",
        "email": "buyer@acme.com",
        "company": "Acme",
        "country": "us",
    }
    raw = json.dumps(payload).encode("utf-8")

    app.dependency_overrides[get_db] = _get_db_override

    with patch.object(settings, "RB2B_WEBHOOK_SECRET", "rb2b-secret"), \
         patch("app.api.v1.visitor_intent.process_visitor_intent_event") as mock_task:
        signature = hmac.new(b"rb2b-secret", raw, hashlib.sha256).hexdigest()
        response = client.post(
            "/api/v1/visitor-intent/webhooks/rb2b",
            data=raw,
            headers={
                "Content-Type": "application/json",
                "X-RB2B-Signature": f"sha256={signature}",
            },
        )

    assert response.status_code == 202
    assert response.json()["accepted"] is True
    mock_task.delay.assert_called_once_with(1)
    created_event = db._added_entities[0]
    assert created_event.event_type == "rfq_page_enter"
    assert created_event.visitor_country == "US"


def test_ingest_leadfeeder_webhook_success_with_valid_signature():
    db = _make_mock_db()

    async def _get_db_override():
        yield db

    payload = {
        "supplier_id": 8,
        "visit_id": "leadfeeder-visit-2",
        "event_type": "company_identified",
        "company": {
            "id": "cmp-1",
            "name": "Beta GmbH",
            "country": "de",
            "domain": "beta.de",
        },
        "contact": {
            "email": "procurement@beta.de",
        },
    }
    raw = json.dumps(payload).encode("utf-8")

    app.dependency_overrides[get_db] = _get_db_override

    with patch.object(settings, "LEADFEEDER_WEBHOOK_SECRET", "lead-secret"), \
         patch("app.api.v1.visitor_intent.process_visitor_intent_event") as mock_task:
        signature = hmac.new(b"lead-secret", raw, hashlib.sha256).hexdigest()
        response = client.post(
            "/api/v1/visitor-intent/webhooks/leadfeeder",
            data=raw,
            headers={
                "Content-Type": "application/json",
                "X-Leadfeeder-Signature": signature,
            },
        )

    assert response.status_code == 202
    assert response.json()["accepted"] is True
    mock_task.delay.assert_called_once_with(1)
    created_event = db._added_entities[0]
    assert created_event.visitor_company == "Beta GmbH"
    assert created_event.visitor_country == "DE"


def test_ingest_rb2b_webhook_rejects_invalid_signature():
    db = _make_mock_db()

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override

    payload = {
        "supplier_id": 7,
        "session_id": "rb2b-session-1",
        "event_type": "page_view",
    }

    with patch.object(settings, "RB2B_WEBHOOK_SECRET", "rb2b-secret"):
        response = client.post(
            "/api/v1/visitor-intent/webhooks/rb2b",
            json=payload,
            headers={"X-RB2B-Signature": "invalid-signature"},
        )

    assert response.status_code == 401


def test_list_visitor_events_for_supplier_success():
    user = SimpleNamespace(id=100, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=9, user_id=100)
    event = SimpleNamespace(
        id=11,
        supplier_id=9,
        visitor_session_id="visitor-abc",
        visitor_email=None,
        visitor_company="ACME",
        visitor_country="US",
        event_type="video_watch",
        page_url="/suppliers/acme",
        session_duration_seconds=88,
        intent_score=76,
        intent_level="high",
        created_at=datetime.utcnow(),
    )

    db = _make_mock_db(
        execute_results=[
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(items=[event]),
        ]
    )
    _override_dependencies(user, db)

    response = client.get("/api/v1/visitor-intent/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["intent_level"] == "high"


def test_get_visitor_intent_summary_success():
    user = SimpleNamespace(id=101, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=10, user_id=101)
    latest_event = SimpleNamespace(created_at=datetime.utcnow())

    db = _make_mock_db(
        execute_results=[
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(scalar_value=25),
            _ExecuteResult(scalar_value=4),
            _ExecuteResult(scalar_value=8),
            _ExecuteResult(scalar_value=61.2),
            _ExecuteResult(items=[latest_event]),
        ]
    )
    _override_dependencies(user, db)

    response = client.get("/api/v1/visitor-intent/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == 10
    assert data["total_events"] == 25
    assert data["high_intent_count"] == 4
    assert data["medium_intent_count"] == 8


def test_get_visitor_intent_benchmark_success():
    user = SimpleNamespace(id=102, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=11, user_id=102)

    events = [
        SimpleNamespace(
            event_data='{"provider":"rb2b"}',
            visitor_email="buyer@acme.com",
            visitor_company="Acme",
            visitor_country="US",
            intent_score=82,
            intent_level="high",
        ),
        SimpleNamespace(
            event_data='{"provider":"leadfeeder"}',
            visitor_email="ops@beta.de",
            visitor_company="Beta GmbH",
            visitor_country="DE",
            intent_score=61,
            intent_level="medium",
        ),
        SimpleNamespace(
            event_data='{"provider":"rb2b"}',
            visitor_email=None,
            visitor_company="Gamma",
            visitor_country="JP",
            intent_score=45,
            intent_level="low",
        ),
    ]

    db = _make_mock_db(
        execute_results=[
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(items=events),
        ]
    )
    _override_dependencies(user, db)

    response = client.get("/api/v1/visitor-intent/benchmark?days=14")

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == 11
    assert data["total_events"] == 3
    assert data["provider_breakdown"]["rb2b_events"] == 2
    assert data["provider_breakdown"]["leadfeeder_events"] == 1
    assert data["provider_breakdown"]["unidentified_provider_events"] == 0
    assert data["quality_gates"]["provider_coverage_pass"] is True
    assert data["quality_gates"]["identification_pass"] is True
    assert data["quality_gates"]["scoring_pass"] is True
    assert data["quality_gates"]["overall_pass"] is True


def test_get_visitor_intent_ops_metrics_success():
    user = SimpleNamespace(id=103, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=12, user_id=103)

    db = _make_mock_db(
        execute_results=[
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(scalar_value=100),
            _ExecuteResult(scalar_value=12),
            _ExecuteResult(scalar_value=20),
            _ExecuteResult(scalar_value=16),
            _ExecuteResult(scalar_value=68.75),
        ]
    )
    _override_dependencies(user, db)

    response = client.get("/api/v1/visitor-intent/ops-metrics?hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == 12
    assert data["window_hours"] == 24
    assert data["total_events"] == 100
    assert data["high_intent_events"] == 12
    assert data["medium_intent_events"] == 20
    assert data["unread_high_intent_notifications"] == 16
    assert data["alert_high_intent_spike"] is True
    assert data["alert_unread_backlog"] is True
