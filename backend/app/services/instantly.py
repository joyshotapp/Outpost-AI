"""Instantly API v2 service adapter — Sprint 8 (Task 8.1).

Instantly docs: https://developer.instantly.ai/api/v2
Key concepts:
  - Campaign  : Email outreach campaign with multi-step sequences
  - Lead      : A contact within a campaign (email address + metadata)
  - Subsequence: Conditional branching within a campaign (reply detection)
  - Webhook   : Instantly POSTs events (reply, bounce, opt-out) to our endpoint

Authentication: Bearer token via `Authorization: Bearer <API_KEY>` header.

Stub mode: When INSTANTLY_API_KEY is not set, all methods return deterministic
stub objects so the rest of the application can run without a live key.
"""

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class InstantlyService:
    """Wrapper around the Instantly REST API v2."""

    BASE_URL = settings.INSTANTLY_API_BASE_URL

    def __init__(self) -> None:
        self.api_key: str | None = settings.INSTANTLY_API_KEY

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }

    def _available(self) -> bool:
        return bool(self.api_key)

    def _stub_campaign(self, name: str) -> dict[str, Any]:
        return {
            "id": f"stub_campaign_{int(time.time())}",
            "name": name,
            "status": "draft",
            "_stub": True,
        }

    # ── Campaign Management ───────────────────────────────────────────────────

    def create_campaign(
        self,
        name: str,
        from_email: str | None = None,
        daily_limit: int | None = None,
    ) -> dict[str, Any]:
        """Create a new Instantly email campaign.

        Returns campaign dict with ``id``, ``name``, ``status``.
        Falls back to stub if API key not configured.
        """
        if not self._available():
            logger.warning("INSTANTLY_API_KEY not set — returning stub campaign")
            return self._stub_campaign(name)

        payload: dict[str, Any] = {"name": name}
        if from_email:
            payload["from_email"] = from_email
        if daily_limit:
            payload["daily_limit"] = daily_limit

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("Instantly campaign created: %s (id=%s)", name, data.get("id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Instantly create_campaign failed: %s — %s",
                exc.response.status_code,
                exc.response.text,
            )
            return self._stub_campaign(name)

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Retrieve a campaign by ID."""
        if not self._available():
            return {"id": campaign_id, "status": "draft", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/campaigns/{campaign_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly get_campaign failed: %s", exc.response.text)
            return {"id": campaign_id, "status": "unknown", "_error": True}

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Pause an active campaign."""
        if not self._available():
            return {"id": campaign_id, "status": "paused", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/pause",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly pause_campaign failed: %s", exc.response.text)
            return {"id": campaign_id, "status": "unknown", "_error": True}

    def resume_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Resume a paused campaign."""
        if not self._available():
            return {"id": campaign_id, "status": "active", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/resume",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly resume_campaign failed: %s", exc.response.text)
            return {"id": campaign_id, "status": "unknown", "_error": True}

    # ── Lead (Contact) Management ─────────────────────────────────────────────

    def add_leads(
        self,
        campaign_id: str,
        leads: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bulk-add leads to a campaign.

        Each lead dict should contain at minimum:
          ``email``   (required)
          ``first_name``, ``last_name``, ``company_name``,
          ``personalization`` (optional — AI-generated opener)

        Returns ``{"added": N, "skipped": N, "errors": []}``.
        """
        if not self._available():
            logger.warning("INSTANTLY_API_KEY not set — stub add_leads for %d contacts", len(leads))
            return {"added": len(leads), "skipped": 0, "errors": [], "_stub": True}

        # Instantly accepts up to 100 leads per request
        results: dict[str, Any] = {"added": 0, "skipped": 0, "errors": []}
        for batch_start in range(0, len(leads), 100):
            batch = leads[batch_start : batch_start + 100]
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(
                        f"{self.BASE_URL}/campaigns/{campaign_id}/leads",
                        json={"leads": batch},
                        headers=self._headers(),
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results["added"] += data.get("added", len(batch))
                    results["skipped"] += data.get("skipped", 0)
                    results["errors"].extend(data.get("errors", []))
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Instantly add_leads batch failed: %s — %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                results["errors"].append({"batch_start": batch_start, "error": exc.response.text})

        logger.info(
            "Instantly add_leads: campaign=%s added=%d skipped=%d errors=%d",
            campaign_id,
            results["added"],
            results["skipped"],
            len(results["errors"]),
        )
        return results

    def get_lead_status(self, campaign_id: str, email: str) -> dict[str, Any]:
        """Get the current status of a single lead in a campaign."""
        if not self._available():
            return {"email": email, "status": "pending", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/leads/{email}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly get_lead_status failed: %s", exc.response.text)
            return {"email": email, "status": "unknown", "_error": True}

    # ── Analytics ─────────────────────────────────────────────────────────────

    def get_campaign_analytics(self, campaign_id: str) -> dict[str, Any]:
        """Return campaign-level stats: sent, opened, replied, bounced.

        Returns a normalized dict regardless of API availability.
        """
        if not self._available():
            return {
                "campaign_id": campaign_id,
                "sent": 0,
                "opened": 0,
                "replied": 0,
                "bounced": 0,
                "unsubscribed": 0,
                "open_rate": 0.0,
                "reply_rate": 0.0,
                "bounce_rate": 0.0,
                "_stub": True,
            }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/campaigns/{campaign_id}/analytics",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                raw = resp.json()
                sent = raw.get("sent", 0) or 1  # avoid division by zero
                return {
                    "campaign_id": campaign_id,
                    "sent": raw.get("sent", 0),
                    "opened": raw.get("opened", 0),
                    "replied": raw.get("replied", 0),
                    "bounced": raw.get("bounced", 0),
                    "unsubscribed": raw.get("unsubscribed", 0),
                    "open_rate": round(raw.get("opened", 0) / sent, 4),
                    "reply_rate": round(raw.get("replied", 0) / sent, 4),
                    "bounce_rate": round(raw.get("bounced", 0) / sent, 4),
                }
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly get_campaign_analytics failed: %s", exc.response.text)
            return {"campaign_id": campaign_id, "error": exc.response.text}

    def list_campaigns(self, limit: int = 50, skip: int = 0) -> list[dict[str, Any]]:
        """Return a list of all campaigns for the account."""
        if not self._available():
            return []

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/campaigns",
                    params={"limit": limit, "skip": skip},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json().get("campaigns", resp.json() if isinstance(resp.json(), list) else [])
        except httpx.HTTPStatusError as exc:
            logger.error("Instantly list_campaigns failed: %s", exc.response.text)
            return []

    # ── Webhook signature verification ───────────────────────────────────────

    @staticmethod
    def verify_webhook_signature(body: bytes, signature_header: str | None) -> bool:
        """Verify HMAC-SHA256 signature from Instantly webhook.

        Returns True in dev mode (no secret configured).
        """
        import hashlib
        import hmac

        secret = settings.INSTANTLY_WEBHOOK_SECRET
        if not secret:
            return True  # Dev mode — accept all

        if not signature_header:
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)


_instantly_service: InstantlyService | None = None


def get_instantly_service() -> InstantlyService:
    """Module-level singleton factory (compatible with Celery task imports)."""
    global _instantly_service
    if _instantly_service is None:
        _instantly_service = InstantlyService()
    return _instantly_service
