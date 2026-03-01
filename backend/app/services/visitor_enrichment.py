"""Visitor enrichment service with Clay adapter + fallback heuristics."""

import json
import logging
from typing import Any

try:
    import httpx as _httpx
except ImportError:  # pragma: no cover
    _httpx = None  # type: ignore[assignment]

from app.config import settings
from app.models import VisitorEvent

logger = logging.getLogger(__name__)


class ClayEnrichmentAdapter:
    """Clay enrichment adapter.

    This adapter keeps a stable interface for future live API calls.
    Before live integration is enabled, it falls back to deterministic
    enrichment from currently available event data.
    """

    def _safe_event_data(self, raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _infer_company_from_email(self, email: str | None) -> str | None:
        if not email or "@" not in email:
            return None
        domain = email.split("@", maxsplit=1)[1]
        company_token = domain.split(".", maxsplit=1)[0].strip()
        if not company_token:
            return None
        return company_token.replace("-", " ").title()

    def _call_clay_api(self, email: str | None, company: str | None) -> dict[str, Any]:
        """Call Clay Person/Company lookup API and return normalised attributes."""
        if _httpx is None or not settings.CLAY_API_KEY:
            return {}

        query: dict[str, Any] = {}
        if email:
            query["email"] = email
        if company:
            query["company"] = company
        if not query:
            return {}

        try:
            response = _httpx.post(
                "https://api.clay.com/v1/sources/lookup",
                headers={
                    "Authorization": f"Bearer {settings.CLAY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=query,
                timeout=8.0,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return {}

            attributes: dict[str, Any] = {}
            if data.get("email"):
                attributes["visitor_email"] = data["email"]
            if data.get("company") or data.get("company_name"):
                attributes["visitor_company"] = data.get("company") or data.get("company_name")
            if data.get("country"):
                attributes["visitor_country"] = str(data["country"]).strip().upper()[:2]
            return attributes
        except Exception as exc:
            logger.warning("Clay API call failed: %s", exc)
            return {}

    def enrich(self, event: VisitorEvent) -> dict[str, Any]:
        event_data = self._safe_event_data(event.event_data)
        attributes: dict[str, Any] = {}

        if settings.CLAY_API_KEY:
            attributes = self._call_clay_api(
                email=event.visitor_email,
                company=event.visitor_company,
            )

            if not attributes:
                clay_profile = event_data.get("clay_profile") if isinstance(event_data.get("clay_profile"), dict) else {}
                if clay_profile:
                    if clay_profile.get("email"):
                        attributes["visitor_email"] = clay_profile["email"]
                    if clay_profile.get("company"):
                        attributes["visitor_company"] = clay_profile["company"]
                    if clay_profile.get("country"):
                        attributes["visitor_country"] = str(clay_profile["country"]).strip().upper()[:2]

            status = "enriched" if attributes else "no_match"
            return {
                "provider": "clay",
                "status": status,
                "attributes": attributes,
            }

        if not event.visitor_company:
            inferred_company = self._infer_company_from_email(event.visitor_email)
            if inferred_company:
                attributes["visitor_company"] = inferred_company

        if not event.visitor_country:
            fallback_country = event_data.get("ip_country") or event_data.get("country_code")
            if fallback_country:
                attributes["visitor_country"] = str(fallback_country).strip().upper()[:2]

        return {
            "provider": "fallback",
            "status": "fallback_heuristics",
            "attributes": attributes,
        }


class VisitorEnrichmentService:
    """Facade for visitor enrichment with graceful fallback semantics."""

    def __init__(self, adapter: ClayEnrichmentAdapter | None = None):
        self.adapter = adapter or ClayEnrichmentAdapter()

    def enrich_event(self, event: VisitorEvent) -> dict[str, Any]:
        try:
            return self.adapter.enrich(event)
        except Exception as exc:
            logger.error("visitor enrichment failed for event %s: %s", getattr(event, "id", None), str(exc))
            return {
                "provider": "fallback",
                "status": "error",
                "error": str(exc),
                "attributes": {},
            }


_visitor_enrichment_service: VisitorEnrichmentService | None = None


def get_visitor_enrichment_service() -> VisitorEnrichmentService:
    global _visitor_enrichment_service
    if _visitor_enrichment_service is None:
        _visitor_enrichment_service = VisitorEnrichmentService()
    return _visitor_enrichment_service
