"""Tests for visitor intent enrichment + re-score pipeline."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import Notification, VisitorEvent
from app.tasks.visitor_intent import process_visitor_intent_event_core


def test_process_visitor_intent_event_core_rescores_and_notifies_after_enrichment():
    event = SimpleNamespace(
        id=99,
        supplier_id=7,
        visitor_session_id="visitor-99",
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
        event_type="rfq_submit_click",
        page_url="/suppliers/acme/rfq",
        event_data='{"cta_clicked": true}',
        session_duration_seconds=180,
        intent_score=None,
        intent_level=None,
    )

    notifications: list[Notification] = []

    session = AsyncMock()

    async def _get(model, object_id):
        if model is VisitorEvent and object_id == 99:
            return event
        return None

    def _add(entity):
        if isinstance(entity, Notification):
            notifications.append(entity)

    session.get = AsyncMock(side_effect=_get)
    session.add = MagicMock(side_effect=_add)
    session.commit = AsyncMock()

    enrichment_service = MagicMock()
    enrichment_service.enrich_event.return_value = {
        "provider": "clay",
        "status": "enriched",
        "attributes": {
            "visitor_email": "buyer@acme.com",
            "visitor_company": "Acme Inc",
            "visitor_country": "US",
        },
    }

    dispatch_result = {
        "websocket": {"success": True, "attempt": 1},
        "slack": {"success": True, "attempt": 1},
    }

    with patch("app.tasks.visitor_intent.get_visitor_enrichment_service", return_value=enrichment_service), \
         patch("app.tasks.visitor_intent._dispatch_high_intent_alerts_with_retry", new=AsyncMock(return_value=dispatch_result)) as mock_dispatch:
        result = asyncio.run(process_visitor_intent_event_core(session, 99))

    assert result["success"] is True
    assert result["rescored"] is True
    assert result["intent_level"] == "high"
    assert result["notified"] is True
    assert result["alert_dispatch"] == dispatch_result
    mock_dispatch.assert_awaited_once()

    assert len(notifications) == 1
    assert notifications[0].notification_type == "high_intent_visitor"

    event_data = json.loads(event.event_data)
    assert event_data["enrichment"]["provider"] == "clay"
    assert event_data["enrichment"]["applied_attributes"]["visitor_company"] == "Acme Inc"
