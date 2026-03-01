"""Visitor intent scoring service for Sprint 5."""

import json
from typing import Any


class VisitorIntentService:
    """Heuristic scoring for visitor intent analysis."""

    HIGH_INTENT_THRESHOLD = 75
    MEDIUM_INTENT_THRESHOLD = 45

    EVENT_BASE_SCORES: dict[str, int] = {
        "rfq_page_enter": 35,
        "rfq_submit_click": 40,
        "contact_click": 30,
        "video_watch": 25,
        "download_catalog": 30,
        "page_view": 8,
    }

    def _safe_event_data(self, raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload
            return {}
        except Exception:
            return {}

    def _behavior_score(
        self,
        event_type: str,
        session_duration_seconds: int | None,
        event_data: dict[str, Any],
    ) -> int:
        score = self.EVENT_BASE_SCORES.get(event_type, 5)

        if session_duration_seconds:
            score += min(25, max(0, int(session_duration_seconds / 30) * 3))

        if event_type == "video_watch":
            watched_seconds = int(event_data.get("watched_seconds", 0) or 0)
            score += min(20, int(watched_seconds / 20))

        if event_data.get("cta_clicked") is True:
            score += 15

        if event_data.get("return_visitor") is True:
            score += 10

        return min(100, max(0, score))

    def _identity_score(
        self,
        visitor_email: str | None,
        visitor_company: str | None,
        visitor_country: str | None,
    ) -> int:
        score = 0
        if visitor_company:
            score += 45
        if visitor_email:
            score += 35
        if visitor_country:
            score += 20
        return min(100, score)

    def _intent_level(self, score: int) -> str:
        if score >= self.HIGH_INTENT_THRESHOLD:
            return "high"
        if score >= self.MEDIUM_INTENT_THRESHOLD:
            return "medium"
        return "low"

    def score_event(
        self,
        event_type: str | None,
        session_duration_seconds: int | None,
        event_data_raw: str | None,
        visitor_email: str | None,
        visitor_company: str | None,
        visitor_country: str | None,
    ) -> dict[str, Any]:
        safe_event_type = (event_type or "page_view").strip() or "page_view"
        safe_duration = max(0, session_duration_seconds) if isinstance(session_duration_seconds, int) else None
        event_data = self._safe_event_data(event_data_raw)
        behavior = self._behavior_score(safe_event_type, safe_duration, event_data)
        identity = self._identity_score(visitor_email, visitor_company, visitor_country)

        final_score = int(round((behavior * 0.7) + (identity * 0.3)))
        level = self._intent_level(final_score)

        return {
            "intent_score": final_score,
            "intent_level": level,
            "breakdown": {
                "behavior_score": behavior,
                "identity_score": identity,
                "event_type": safe_event_type,
            },
        }


_visitor_intent_service: VisitorIntentService | None = None


def get_visitor_intent_service() -> VisitorIntentService:
    global _visitor_intent_service
    if _visitor_intent_service is None:
        _visitor_intent_service = VisitorIntentService()
    return _visitor_intent_service
