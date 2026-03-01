"""Clay API service adapter (Sprint 7 — 7.1 ICP list building & waterfall enrichment).

Clay docs: https://docs.clay.com/reference
Key concepts:
  - Table  : Clay worksheet; each row = one contact to enrich
  - Waterfall : sequential enrichment providers; stops on first match
  - Run    : triggers enrichment for rows lacking target data
"""

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Max contacts per Clay API call
_BULK_IMPORT_CHUNK = 100
# Polling interval/max-retries for enrichment completion
_POLL_INTERVAL_S = 5
_POLL_MAX_RETRIES = 36  # 3 minutes total


class ClayService:
    """Wrapper around Clay REST API v3."""

    BASE_URL = "https://api.clay.com/v3"

    def __init__(self) -> None:
        self.api_key: str | None = settings.CLAY_API_KEY

    # ── helpers ─────────────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _available(self) -> bool:
        return bool(self.api_key)

    # ── Table management ────────────────────────────────────────────────────

    def create_table(self, name: str) -> dict[str, Any]:
        """Create a new Clay Table and return its metadata (including `id`).

        Returns a stub dict when API key is not configured (dev/test mode).
        """
        if not self._available():
            logger.warning("CLAY_API_KEY not set — returning stub table")
            return {"id": f"stub_table_{int(time.time())}", "name": name, "_stub": True}

        payload = {"name": name}
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/tables",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("Clay table created: %s (id=%s)", name, data.get("id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error("Clay create_table failed: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Clay create_table network error: %s", exc)
            raise

    # ── ICP import ──────────────────────────────────────────────────────────

    def import_icp_criteria(
        self,
        table_id: str,
        icp: dict[str, Any],
    ) -> dict[str, Any]:
        """Upload ICP criteria (industries, countries, titles, company_sizes) to a Clay table.

        Clay's "search" row type lets Clay auto-find matching contacts.
        Returns Clay's response payload.
        """
        if not self._available():
            return {"table_id": table_id, "rows_queued": 0, "_stub": True}

        payload = {
            "table_id": table_id,
            "search_criteria": {
                "industries": icp.get("industries", []),
                "countries": icp.get("countries", []),
                "job_titles": icp.get("job_titles", []),
                "company_sizes": icp.get("company_sizes", []),
                "seniority_levels": icp.get("seniority_levels", []),
            },
            "limit": icp.get("limit", 500),
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/tables/{table_id}/search",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(
                    "Clay ICP import → table %s queued %d rows",
                    table_id,
                    data.get("rows_queued", 0),
                )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error("Clay import_icp_criteria failed: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Clay import_icp_criteria network error: %s", exc)
            raise

    # ── Waterfall enrichment ─────────────────────────────────────────────────

    def trigger_waterfall_enrichment(self, table_id: str) -> dict[str, Any]:
        """Trigger Clay's waterfall enrichment run for all pending rows in a table.

        Returns `{"run_id": "...", "status": "running"}` or stub equivalent.
        """
        if not self._available():
            return {"run_id": f"stub_run_{int(time.time())}", "status": "running", "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.BASE_URL}/tables/{table_id}/runs",
                    json={"enrichment_type": "waterfall"},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("Clay waterfall run started: %s", data.get("run_id"))
                return data
        except httpx.HTTPStatusError as exc:
            logger.error("Clay trigger_waterfall_enrichment failed: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Clay trigger_waterfall_enrichment network error: %s", exc)
            raise

    # ── Run status ───────────────────────────────────────────────────────────

    def get_run_status(self, table_id: str, run_id: str) -> dict[str, Any]:
        """Poll a Clay enrichment run's status.

        Returns `{"status": "completed"|"running"|"failed", "rows_enriched": N}`.
        """
        if not self._available():
            return {"status": "completed", "rows_enriched": 0, "_stub": True}

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/tables/{table_id}/runs/{run_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Clay get_run_status failed: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Clay get_run_status network error: %s", exc)
            raise

    # ── Fetch enriched contacts ──────────────────────────────────────────────

    def fetch_enriched_contacts(
        self,
        table_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Retrieve enriched rows from a Clay table (paginated).

        Returns:
            {
                "contacts": [...],   # list of enriched contact dicts
                "total": N,
                "page": N,
                "page_size": N,
                "has_more": bool,
            }
        """
        if not self._available():
            return {
                "contacts": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_more": False,
                "_stub": True,
            }

        params = {"page": page, "page_size": page_size, "status": "enriched"}
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    f"{self.BASE_URL}/tables/{table_id}/rows",
                    params=params,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                raw = resp.json()
                contacts = [self._normalise_row(r) for r in raw.get("rows", [])]
                return {
                    "contacts": contacts,
                    "total": raw.get("total", len(contacts)),
                    "page": page,
                    "page_size": page_size,
                    "has_more": raw.get("has_more", False),
                }
        except httpx.HTTPStatusError as exc:
            logger.error("Clay fetch_enriched_contacts failed: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.RequestError as exc:
            logger.error("Clay fetch_enriched_contacts network error: %s", exc)
            raise

    # ── Row normaliser ───────────────────────────────────────────────────────

    @staticmethod
    def _normalise_row(row: dict[str, Any]) -> dict[str, Any]:
        """Map Clay row fields to our internal contact schema."""
        data = row.get("data", row)
        return {
            "clay_row_id": row.get("id") or data.get("id"),
            "first_name": data.get("first_name") or data.get("firstName"),
            "last_name": data.get("last_name") or data.get("lastName"),
            "full_name": (
                data.get("full_name")
                or data.get("name")
                or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
            ),
            "email": data.get("email") or data.get("work_email"),
            "linkedin_url": data.get("linkedin_url") or data.get("linkedinProfile"),
            "phone": data.get("phone"),
            "company_name": data.get("company") or data.get("company_name"),
            "company_domain": data.get("company_domain") or data.get("domain"),
            "company_industry": data.get("industry"),
            "company_size": data.get("company_size") or data.get("employees"),
            "company_country": data.get("country") or data.get("location_country"),
            "job_title": data.get("title") or data.get("job_title"),
            "seniority": data.get("seniority"),
            "department": data.get("department"),
            "enriched_data": row,  # store raw Clay payload for debugging
        }


_clay_service: ClayService | None = None


def get_clay_service() -> ClayService:
    """Return a module-level singleton ClayService instance."""
    global _clay_service
    if _clay_service is None:
        _clay_service = ClayService()
    return _clay_service
