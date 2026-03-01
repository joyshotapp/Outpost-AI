"""HeyReach API service adapter (Sprint 7 — 7.2 LinkedIn outreach sequences).

HeyReach docs: https://app.heyreach.io (v1 REST API)
Key concepts:
  - Campaign : LinkedIn outreach campaign (sequence of steps)
  - Lead List : uploaded contact list bound to a campaign
  - Sequence  : Day 1–25 step chain; connection + follow-up messages
  - Webhook   : HeyReach POSTs events (reply, accept, etc.) to our endpoint
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class HeyReachService:
    """Wrapper around HeyReach REST API."""

    BASE_URL = "https://api.heyreach.io/api/public/v1"

    def __init__(self) -> None:
        self.api_key: str | None = settings.HEYREACH_API_KEY

    # ── helpers ─────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self.api_key or "",
            "Content-Type": "application/json",
        }

    def _available(self) -> bool:
        return bool(self.api_key)

    # ── Campaign management ─────────────────────────────────────────────────

    def create_campaign(
        self,
        name: str,
        linkedin_account_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new HeyReach LinkedIn campaign.

        Returns `{"id": "...", "name": "...", "status": "draft"}` or stub.
        """
        if not self._available():
            import time
            logger.warning("HEYREACH_API_KEY not set — returning stub campaign")
            return {
                "id": f"stub_campaign_{int(time.time())}",
                "name": name,
                "status": "draft",
                "_stub": True,
            }

        payload: dict[str, Any] = {"name": name}
        if linkedin_account_id:
            payload["linkedin_account_id"] = linkedin_account_id

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("HeyReach campaign created: %s (id=%s)", name, data.get("id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach create_campaign failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach create_campaign network error: %s", exc)
            raise

    # ── Contact import ───────────────────────────────────────────────────────

    def import_contacts(
        self,
        campaign_id: str,
        contacts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Import a list of contacts into a HeyReach campaign.

        Each contact dict should have at minimum: `linkedin_url` and optionally
        `first_name`, `last_name`, `email`, `custom_variables` (dict).

        Returns summary: `{"imported": N, "skipped": N, "contact_ids": [...]}`.
        """
        if not self._available():
            return {
                "imported": len(contacts),
                "skipped": 0,
                "contact_ids": [f"stub_{i}" for i in range(len(contacts))],
                "_stub": True,
            }

        payload = {
            "campaign_id": campaign_id,
            "leads": [
                {
                    "linkedin_url": c.get("linkedin_url", ""),
                    "first_name": c.get("first_name", ""),
                    "last_name": c.get("last_name", ""),
                    "email": c.get("email", ""),
                    "custom_variables": c.get("custom_variables", {}),
                }
                for c in contacts
            ],
        }

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/leads",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(
                    "HeyReach import_contacts → campaign %s: imported=%d skipped=%d",
                    campaign_id,
                    data.get("imported", 0),
                    data.get("skipped", 0),
                )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach import_contacts failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach import_contacts network error: %s", exc)
            raise

    # ── Sequence control ─────────────────────────────────────────────────────

    def start_sequence(self, campaign_id: str) -> dict[str, Any]:
        """Activate a HeyReach campaign (starts the Day 1–25 sequence).

        Returns `{"campaign_id": "...", "status": "active"}`.
        """
        if not self._available():
            return {"campaign_id": campaign_id, "status": "active", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/activate",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("HeyReach campaign %s activated", campaign_id)
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach start_sequence failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach start_sequence network error: %s", exc)
            raise

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Pause a running HeyReach campaign (safety or manual)."""
        if not self._available():
            return {"campaign_id": campaign_id, "status": "paused", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/pause",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach pause_campaign failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach pause_campaign network error: %s", exc)
            raise

    def resume_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Resume a paused HeyReach campaign."""
        if not self._available():
            return {"campaign_id": campaign_id, "status": "active", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/resume",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach resume_campaign failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach resume_campaign network error: %s", exc)
            raise

    # ── Sequence status ──────────────────────────────────────────────────────

    def get_sequence_status(
        self,
        campaign_id: str,
        contact_id: str | None = None,
    ) -> dict[str, Any]:
        """Fetch sequence progress for a campaign or a single contact.

        Returns campaign-level stats or contact-level `current_day` / `status`.
        """
        if not self._available():
            return {
                "campaign_id": campaign_id,
                "status": "active",
                "contacts_total": 0,
                "contacts_replied": 0,
                "_stub": True,
            }

        url = f"{self.BASE_URL}/campaigns/{campaign_id}"
        if contact_id:
            url += f"/leads/{contact_id}"

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(url, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach get_sequence_status failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach get_sequence_status network error: %s", exc)
            raise

    # ── Daily stats ──────────────────────────────────────────────────────────

    def get_daily_stats(self, campaign_id: str) -> dict[str, Any]:
        """Return today's connection request and message counts for safety checks."""
        if not self._available():
            return {
                "connections_sent_today": 0,
                "messages_sent_today": 0,
                "_stub": True,
            }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/stats/daily",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HeyReach get_daily_stats failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HeyReach get_daily_stats network error: %s", exc)
            raise


_heyreach_service: HeyReachService | None = None


def get_heyreach_service() -> HeyReachService:
    """Return a module-level singleton HeyReachService instance."""
    global _heyreach_service
    if _heyreach_service is None:
        _heyreach_service = HeyReachService()
    return _heyreach_service
