"""Sprint 5 E2E API flow test (mocked DB)."""

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

    async def _execute(*_args, **_kwargs):
        return queue.pop(0) if queue else _ExecuteResult(items=[])

    def _add(entity):
        if getattr(entity, "id", None) is None:
            entity.id = 1
        if getattr(entity, "created_at", None) is None:
            entity.created_at = datetime.utcnow()
        if getattr(entity, "updated_at", None) is None:
            entity.updated_at = datetime.utcnow()

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock(side_effect=_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def setup_function():
    app.dependency_overrides = {}


def teardown_function():
    app.dependency_overrides = {}


def test_sprint5_e2e_flow_webhook_to_metrics():
    user = SimpleNamespace(id=901, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=19, user_id=901)

    benchmark_events = [
        SimpleNamespace(
            event_data='{"provider":"rb2b"}',
            visitor_email="buyer@acme.com",
            visitor_company="Acme",
            visitor_country="US",
            intent_score=80,
            intent_level="high",
        ),
        SimpleNamespace(
            event_data='{"provider":"leadfeeder"}',
            visitor_email="ops@beta.de",
            visitor_company="Beta",
            visitor_country="DE",
            intent_score=66,
            intent_level="medium",
        ),
    ]

    db = _make_mock_db(
        execute_results=[
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(items=benchmark_events),
            _ExecuteResult(items=[supplier]),
            _ExecuteResult(scalar_value=24),
            _ExecuteResult(scalar_value=4),
            _ExecuteResult(scalar_value=6),
            _ExecuteResult(scalar_value=2),
            _ExecuteResult(scalar_value=63.5),
        ]
    )

    async def _get_user_override():
        return user

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_current_user] = _get_user_override
    app.dependency_overrides[get_db] = _get_db_override

    rb2b_payload = {
        "supplier_id": 19,
        "session_id": "rb2b-e2e-1",
        "event_type": "rfq_page_enter",
        "url": "/suppliers/acme/rfq",
        "email": "buyer@acme.com",
        "company": "Acme",
        "country": "us",
    }
    rb2b_raw = json.dumps(rb2b_payload).encode("utf-8")

    lead_payload = {
        "supplier_id": 19,
        "visit_id": "lead-e2e-1",
        "event_type": "company_identified",
        "company": {"id": "cmp-1", "name": "Beta", "country": "de", "domain": "beta.de"},
        "contact": {"email": "ops@beta.de"},
    }
    lead_raw = json.dumps(lead_payload).encode("utf-8")

    with patch.object(settings, "RB2B_WEBHOOK_SECRET", "rb2b-secret"), \
         patch.object(settings, "LEADFEEDER_WEBHOOK_SECRET", "lead-secret"), \
         patch("app.api.v1.visitor_intent.process_visitor_intent_event.delay") as mock_delay:
        rb2b_sig = hmac.new(b"rb2b-secret", rb2b_raw, hashlib.sha256).hexdigest()
        rb2b_resp = client.post(
            "/api/v1/visitor-intent/webhooks/rb2b",
            data=rb2b_raw,
            headers={"Content-Type": "application/json", "X-RB2B-Signature": f"sha256={rb2b_sig}"},
        )

        lead_sig = hmac.new(b"lead-secret", lead_raw, hashlib.sha256).hexdigest()
        lead_resp = client.post(
            "/api/v1/visitor-intent/webhooks/leadfeeder",
            data=lead_raw,
            headers={"Content-Type": "application/json", "X-Leadfeeder-Signature": lead_sig},
        )

    benchmark_resp = client.get("/api/v1/visitor-intent/benchmark?days=14")
    ops_resp = client.get("/api/v1/visitor-intent/ops-metrics?hours=24")

    assert rb2b_resp.status_code == 202
    assert lead_resp.status_code == 202
    assert benchmark_resp.status_code == 200
    assert ops_resp.status_code == 200

    benchmark_data = benchmark_resp.json()
    ops_data = ops_resp.json()

    assert benchmark_data["supplier_id"] == 19
    assert benchmark_data["quality_gates"]["overall_pass"] is True
    assert ops_data["supplier_id"] == 19
    assert ops_data["total_events"] == 24

    assert mock_delay.call_count == 2
