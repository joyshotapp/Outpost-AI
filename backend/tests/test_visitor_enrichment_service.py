"""Tests for visitor enrichment service."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.config import settings
from app.services.visitor_enrichment import ClayEnrichmentAdapter, VisitorEnrichmentService


def test_enrich_event_fallback_infers_company_and_country():
    event = SimpleNamespace(
        id=1,
        visitor_email="buyer@acme-tools.com",
        visitor_company=None,
        visitor_country=None,
        event_data='{"ip_country":"de"}',
    )

    with patch.object(settings, "CLAY_API_KEY", None):
        service = VisitorEnrichmentService()
        result = service.enrich_event(event)

    assert result["provider"] == "fallback"
    assert result["status"] == "fallback_heuristics"
    assert result["attributes"]["visitor_company"] == "Acme Tools"
    assert result["attributes"]["visitor_country"] == "DE"


def test_enrich_event_clay_profile_preferred_when_api_key_exists():
    event = SimpleNamespace(
        id=2,
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
        event_data=(
            '{"clay_profile": {'
            '"email":"procurement@beta.de",'
            '"company":"Beta GmbH",'
            '"country":"de"'
            "}}"
        ),
    )

    with patch.object(settings, "CLAY_API_KEY", "clay-live-key"):
        service = VisitorEnrichmentService()
        result = service.enrich_event(event)

    assert result["provider"] == "clay"
    assert result["status"] == "enriched"
    assert result["attributes"]["visitor_email"] == "procurement@beta.de"
    assert result["attributes"]["visitor_company"] == "Beta GmbH"
    assert result["attributes"]["visitor_country"] == "DE"


def test_clay_adapter_live_api_call_returns_attributes():
    """When CLAY_API_KEY is set and Clay API responds, attributes are populated."""
    clay_api_response = {"email": "vip@acme.com", "company": "Acme Corp", "country": "US"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = clay_api_response
    mock_response.raise_for_status = MagicMock()

    event = SimpleNamespace(
        id=10,
        visitor_email="buyer@acme.com",
        visitor_company=None,
        visitor_country=None,
        event_data="{}",
    )

    import app.services.visitor_enrichment as enrichment_module

    fake_httpx = MagicMock()
    fake_httpx.post.return_value = mock_response

    with patch.object(settings, "CLAY_API_KEY", "live-clay-key"), \
         patch.object(enrichment_module, "_httpx", fake_httpx):
        adapter = ClayEnrichmentAdapter()
        result = adapter.enrich(event)

    assert result["provider"] == "clay"
    assert result["status"] == "enriched"
    assert result["attributes"]["visitor_email"] == "vip@acme.com"
    assert result["attributes"]["visitor_company"] == "Acme Corp"
    assert result["attributes"]["visitor_country"] == "US"
    fake_httpx.post.assert_called_once()


def test_clay_adapter_api_failure_returns_fallback():
    """When Clay API fails, service returns fallback gracefully."""
    event = SimpleNamespace(
        id=11,
        visitor_email="buyer@beta.de",
        visitor_company=None,
        visitor_country=None,
        event_data="{}",
    )

    import app.services.visitor_enrichment as enrichment_module

    fake_httpx = MagicMock()
    fake_httpx.post.side_effect = Exception("connection timeout")

    with patch.object(settings, "CLAY_API_KEY", "live-clay-key"), \
         patch.object(enrichment_module, "_httpx", fake_httpx):
        service = VisitorEnrichmentService()
        result = service.enrich_event(event)

    assert result["provider"] == "clay"
    assert result["status"] == "no_match"
