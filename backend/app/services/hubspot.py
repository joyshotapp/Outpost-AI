"""HubSpot CRM service adapter — Sprint 8 (Task 8.9).

HubSpot docs: https://developers.hubspot.com/docs/api/crm
Authentication: Private App Token (Bearer)

Entities synced:
  Contact  →  Buyer / outbound contact
  Deal     →  High-intent lead (Grade A)
  Activity →  Lead events (RFQ submitted, replied, scored)

Stub mode: When HUBSPOT_PRIVATE_APP_TOKEN is not set all methods return
deterministic stub objects so the application runs without a live key.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotService:
    """Wrapper around HubSpot CRM REST API v3."""

    def __init__(
        self,
        api_token: str | None = None,
        pipeline_id: str | None = None,
    ) -> None:
        self.token: str | None = api_token if api_token is not None else settings.HUBSPOT_PRIVATE_APP_TOKEN
        self.pipeline_id: str | None = pipeline_id if pipeline_id is not None else settings.HUBSPOT_PIPELINE_ID
        self.stub_mode: bool = not bool(self.token)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token or ''}",
            "Content-Type": "application/json",
        }

    def _available(self) -> bool:
        return not self.stub_mode

    # ── Contacts ──────────────────────────────────────────────────────────────

    def upsert_contact(
        self,
        email: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a HubSpot contact by email.

        ``properties`` maps HubSpot property names to values, e.g.:
          {"firstname": "John", "lastname": "Doe", "company": "ACME"}

        Returns ``{"id": "...", "properties": {...}}``.
        """
        if not self._available():
            logger.warning("HUBSPOT_PRIVATE_APP_TOKEN not set — stub upsert_contact")
            return {"id": f"stub_contact_{hash(email) % 100000}", "email": email, "_stub": True}

        payload = {"properties": {"email": email, **properties}}
        try:
            with httpx.Client(timeout=30) as client:
                # Try create first; fall back to update on 409 (already exists)
                resp = client.post(
                    f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts",
                    json=payload,
                    headers=self._headers(),
                )
                if resp.status_code == 409:
                    # Contact already exists — use search to get ID, then patch
                    existing = self._search_contact_by_email(email)
                    if existing:
                        contact_id = existing["id"]
                        patch_resp = client.patch(
                            f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}",
                            json={"properties": properties},
                            headers=self._headers(),
                        )
                        patch_resp.raise_for_status()
                        return patch_resp.json()
                resp.raise_for_status()
                data = resp.json()
                logger.info("HubSpot contact upserted: %s (id=%s)", email, data.get("id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HubSpot upsert_contact failed for %s: %s — %s",
                email,
                exc.response.status_code,
                exc.response.text,
            )
            return {"email": email, "_error": True}

    def _search_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Search for an existing HubSpot contact by email."""
        payload = {
            "filterGroups": [
                {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
            ],
            "properties": ["email", "firstname", "lastname"],
            "limit": 1,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts/search",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                return results[0] if results else None
        except httpx.HTTPStatusError:
            return None

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Retrieve a HubSpot contact record by ID."""
        if not self._available():
            return {"id": contact_id, "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{_HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("HubSpot get_contact failed: %s", exc.response.text)
            return {"id": contact_id, "_error": True}

    # ── Deals ─────────────────────────────────────────────────────────────────

    def create_deal(
        self,
        deal_name: str,
        contact_id: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a HubSpot Deal (for Grade-A leads).

        Optionally associates the deal with a contact by HubSpot contact ID.
        """
        if not self._available():
            logger.warning("HUBSPOT_PRIVATE_APP_TOKEN not set — stub create_deal")
            return {"id": f"stub_deal_{hash(deal_name) % 100000}", "name": deal_name, "_stub": True}

        props: dict[str, Any] = {"dealname": deal_name, **(properties or {})}
        if self.pipeline_id:
            props["pipeline"] = self.pipeline_id

        payload: dict[str, Any] = {"properties": props}
        if contact_id:
            payload["associations"] = [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
                }
            ]

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{_HUBSPOT_API_BASE}/crm/v3/objects/deals",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("HubSpot deal created: %s (id=%s)", deal_name, data.get("id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HubSpot create_deal failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            return {"name": deal_name, "_error": True}

    # ── Activities / Notes ────────────────────────────────────────────────────

    def log_activity(
        self,
        contact_id: str,
        note_body: str,
    ) -> dict[str, Any]:
        """Attach a note (engagement) to a HubSpot contact.

        Used to record lead events: RFQ submitted, scored, email replied, etc.
        """
        if not self._available():
            return {"contact_id": contact_id, "_stub": True}

        payload = {
            "properties": {
                "hs_note_body": note_body,
                "hs_timestamp": str(int(__import__("time").time() * 1000)),
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
                }
            ],
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{_HUBSPOT_API_BASE}/crm/v3/objects/notes",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("HubSpot log_activity failed: %s", exc.response.text)
            return {"contact_id": contact_id, "_error": True}

    # ── Bulk sync helper ──────────────────────────────────────────────────────

    def sync_lead_to_hubspot(
        self,
        *,
        email: str,
        first_name: str = "",
        last_name: str = "",
        company: str = "",
        lead_grade: str = "",
        lead_score: int = 0,
        source: str = "",
        supplier_id: int = 0,
        rfq_id: int | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        """Convenience method: upsert contact + optionally create deal + log activity.

        Grade A → also creates a Deal.
        Always logs an activity note.

        Returns:
            {"contact_id": str, "deal_id": str | None, "note_id": str | None}
        """
        contact_props = {
            "firstname": first_name,
            "lastname": last_name,
            "company": company,
            "lead_grade__c": lead_grade,        # Custom HubSpot property
            "lead_score__c": str(lead_score),   # Custom HubSpot property
            "lead_source": source,
            "supplier_id__c": str(supplier_id), # Custom HubSpot property
        }
        contact_data = self.upsert_contact(email, contact_props)
        contact_id = contact_data.get("id", "")

        deal_id: str | None = None
        if lead_grade == "A" and contact_id and not contact_data.get("_stub"):
            deal_name = f"[{lead_grade}] {company or email} — RFQ #{rfq_id or 'new'}"
            deal_data = self.create_deal(
                deal_name,
                contact_id=contact_id,
                properties={"amount": "0", "dealstage": "appointmentscheduled"},
            )
            deal_id = deal_data.get("id")

        note_id: str | None = None
        if contact_id and not contact_data.get("_stub"):
            activity_text = (
                f"Source: {source} | Grade: {lead_grade} | Score: {lead_score}\n"
                f"Supplier ID: {supplier_id}\n"
                f"{notes}"
            )
            note_data = self.log_activity(contact_id, activity_text)
            note_id = note_data.get("id")

        return {"contact_id": contact_id, "deal_id": deal_id, "note_id": note_id}


_hubspot_service: HubSpotService | None = None


def get_hubspot_service() -> HubSpotService:
    """Module-level singleton factory."""
    global _hubspot_service
    if _hubspot_service is None:
        _hubspot_service = HubSpotService()
    return _hubspot_service
