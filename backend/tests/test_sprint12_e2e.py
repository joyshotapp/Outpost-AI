"""Sprint 12 E2E / Unit Tests: Analytics, Exhibitions, Business Cards, Remarketing, Nurture

Tests:
  TestAnalyticsModels          — ORM model sanity (Exhibition, BusinessCard, RemarketingSequence, NurtureSequence)
  TestAnalyticsEndpoints       — /analytics/* HTTP behaviour
  TestExhibitionsEndpoints     — /exhibitions/* HTTP behaviour (CRUD + lifecycle)
  TestBusinessCardsEndpoints   — /business-cards/* HTTP behaviour (OCR stub, convert-to-lead)
  TestRemarketingTasks         — Celery task imports and heuristic rescore logic
  TestNurtureTasks             — Email nurture task imports and Claude fallback
  TestDataExportEndpoints      — /analytics/export/* CSV/JSON
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(role: str = "supplier", user_id: int = 1) -> MagicMock:
    u = MagicMock()
    u.id = user_id
    u.role = MagicMock()
    u.role.value = role
    u.is_admin = role == "admin"
    return u


def _make_supplier(sid: int = 10) -> MagicMock:
    s = MagicMock()
    s.id = sid
    s.company_name = "Demo Supplier Ltd"
    s.company_slug = "demo-supplier"
    s.country = "TW"
    s.industry = "Electronics"
    s.is_active = True
    s.subscription_tier = "professional"
    s.created_at = datetime.now(timezone.utc)
    return s


def _make_exhibition(eid: int = 1, supplier_id: int = 10) -> MagicMock:
    ex = MagicMock()
    ex.id = eid
    ex.supplier_id = supplier_id
    ex.name = "Hannover Messe 2025"
    ex.location = "Hannover, Germany"
    ex.booth_number = "Hall 5 / B12"
    ex.start_date = datetime(2025, 4, 1, tzinfo=timezone.utc)
    ex.end_date = datetime(2025, 4, 5, tzinfo=timezone.utc)
    ex.status = "planning"
    ex.icp_criteria = {}
    ex.contacts_count = 0
    ex.notes = None
    ex.created_at = datetime.now(timezone.utc)
    ex.updated_at = datetime.now(timezone.utc)
    return ex


def _make_business_card(cid: int = 1, supplier_id: int = 10) -> MagicMock:
    bc = MagicMock()
    bc.id = cid
    bc.supplier_id = supplier_id
    bc.exhibition_id = None
    bc.image_url = "https://example.com/cards/test.jpg"
    bc.full_name = "Taro Yamada"
    bc.company_name = "ABC Corp"
    bc.job_title = "Purchasing Manager"
    bc.email = "taro@abc.co.jp"
    bc.phone = "+81-3-1234-5678"
    bc.website = None
    bc.address = "1-1 Marunouchi, Tokyo"
    bc.country = "JP"
    bc.linkedin_url = None
    bc.ocr_status = "completed"
    bc.ocr_confidence = 0.92
    bc.raw_ocr_text = "Taro Yamada\nABC Corp\nPurchasing Manager"
    bc.converted_to_contact = False
    bc.contact_id = None
    bc.follow_up_sent = False
    bc.notes = None
    bc.created_at = datetime.now(timezone.utc)
    bc.updated_at = datetime.now(timezone.utc)
    return bc


# ============================================================
# TestAnalyticsModels
# ============================================================

class TestAnalyticsModels:
    def test_exhibition_model_tablename(self):
        from app.models.exhibition import Exhibition
        assert Exhibition.__tablename__ == "exhibitions"

    def test_exhibition_model_columns(self):
        from app.models.exhibition import Exhibition
        cols = {c.name for c in Exhibition.__table__.columns}
        assert "id" in cols
        assert "supplier_id" in cols
        assert "name" in cols
        assert "status" in cols
        assert "start_date" in cols
        assert "end_date" in cols
        assert "contacts_count" in cols

    def test_business_card_model_tablename(self):
        from app.models.business_card import BusinessCard
        assert BusinessCard.__tablename__ == "business_cards"

    def test_business_card_model_columns(self):
        from app.models.business_card import BusinessCard
        cols = {c.name for c in BusinessCard.__table__.columns}
        assert "id" in cols
        assert "supplier_id" in cols
        assert "email" in cols
        assert "ocr_status" in cols
        assert "ocr_confidence" in cols
        assert "converted_to_contact" in cols

    def test_remarketing_sequence_model_tablename(self):
        from app.models.remarketing_sequence import RemarketingSequence
        assert RemarketingSequence.__tablename__ == "remarketing_sequences"

    def test_remarketing_sequence_model_columns(self):
        from app.models.remarketing_sequence import RemarketingSequence
        cols = {c.name for c in RemarketingSequence.__table__.columns}
        assert "trigger_type" in cols
        assert "original_lead_grade" in cols
        assert "rescored_lead_grade" in cols
        assert "sequence_step" in cols
        assert "total_steps" in cols
        assert "next_action_at" in cols

    def test_nurture_sequence_model_tablename(self):
        from app.models.nurture_sequence import NurtureSequence
        assert NurtureSequence.__tablename__ == "nurture_sequences"

    def test_nurture_sequence_model_columns(self):
        from app.models.nurture_sequence import NurtureSequence
        cols = {c.name for c in NurtureSequence.__table__.columns}
        assert "contact_email" in cols
        assert "industry" in cols
        assert "emails_sent" in cols
        assert "unsubscribed" in cols
        assert "next_send_at" in cols

    def test_models_init_exports(self):
        from app.models import Exhibition, BusinessCard, RemarketingSequence, NurtureSequence
        assert Exhibition is not None
        assert BusinessCard is not None
        assert RemarketingSequence is not None
        assert NurtureSequence is not None


# ============================================================
# TestAnalyticsEndpoints
# ============================================================

class TestAnalyticsEndpoints:
    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.analytics import router
        app = FastAPI()
        app.include_router(router)
        return app

    def _client(self):
        from fastapi.testclient import TestClient
        return TestClient(self._make_app())

    def test_kpi_overview_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/kpi")
        assert resp.status_code in (401, 403, 422)

    def test_rfq_trend_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/rfq-trend")
        assert resp.status_code in (401, 403, 422)

    def test_lead_score_distribution_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/lead-score-distribution")
        assert resp.status_code in (401, 403, 422)

    def test_visitor_trend_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/visitor-trend")
        assert resp.status_code in (401, 403, 422)

    def test_outbound_performance_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/outbound-performance")
        assert resp.status_code in (401, 403, 422)

    def test_content_reach_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/content-reach")
        assert resp.status_code in (401, 403, 422)

    def test_analytics_router_exists(self):
        from app.api.v1.analytics import router
        routes = {r.path for r in router.routes}
        assert any("kpi" in r for r in routes)
        assert any("rfq-trend" in r for r in routes)
        assert any("lead-score" in r for r in routes)

    def test_analytics_export_routes_exist(self):
        from app.api.v1.analytics import router
        routes = {r.path for r in router.routes}
        assert any("export" in r for r in routes)


# ============================================================
# TestDataExportEndpoints
# ============================================================

class TestDataExportEndpoints:
    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.analytics import router
        app = FastAPI()
        app.include_router(router)
        return app

    def _client(self):
        from fastapi.testclient import TestClient
        return TestClient(self._make_app())

    def test_export_leads_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/export/leads")
        assert resp.status_code in (401, 403, 422)

    def test_export_rfqs_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/export/rfqs")
        assert resp.status_code in (401, 403, 422)

    def test_export_analytics_requires_auth(self):
        client = self._client()
        resp = client.get("/analytics/export/analytics")
        assert resp.status_code in (401, 403, 422)

    def test_export_leads_invalid_fmt(self):
        """Invalid format query param should be caught before auth, or after (both valid)."""
        client = self._client()
        resp = client.get("/analytics/export/leads?fmt=xlsx")
        # 400 (bad format before auth) or 401/422 (auth guard first) are all acceptable
        assert resp.status_code in (400, 401, 403, 422)

    def test_export_routes_exist(self):
        from app.api.v1.analytics import router
        paths = {r.path for r in router.routes}
        assert "/analytics/export/leads" in paths
        assert "/analytics/export/rfqs" in paths
        assert "/analytics/export/analytics" in paths


# ============================================================
# TestExhibitionsEndpoints
# ============================================================

class TestExhibitionsEndpoints:
    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.exhibitions import router
        app = FastAPI()
        app.include_router(router)
        return app

    def _client(self):
        from fastapi.testclient import TestClient
        return TestClient(self._make_app())

    def test_list_exhibitions_requires_auth(self):
        client = self._client()
        resp = client.get("/exhibitions")
        assert resp.status_code in (401, 403, 422)

    def test_create_exhibition_requires_auth(self):
        client = self._client()
        resp = client.post("/exhibitions", json={
            "name": "Test Fair",
            "location": "Tokyo",
            "start_date": "2025-06-01T00:00:00Z",
            "end_date": "2025-06-05T00:00:00Z",
        })
        assert resp.status_code in (401, 403, 422)

    def test_get_exhibition_requires_auth(self):
        client = self._client()
        resp = client.get("/exhibitions/1")
        assert resp.status_code in (401, 403, 422)

    def test_update_exhibition_requires_auth(self):
        client = self._client()
        resp = client.patch("/exhibitions/1", json={"name": "Updated Name"})
        assert resp.status_code in (401, 403, 422)

    def test_delete_exhibition_requires_auth(self):
        client = self._client()
        resp = client.delete("/exhibitions/1")
        assert resp.status_code in (401, 403, 422)

    def test_advance_status_requires_auth(self):
        client = self._client()
        resp = client.patch("/exhibitions/1/status", json={"status": "active"})
        assert resp.status_code in (401, 403, 422)

    def test_exhibition_contacts_requires_auth(self):
        client = self._client()
        resp = client.get("/exhibitions/1/contacts")
        assert resp.status_code in (401, 403, 422)

    def test_exhibitions_router_routes_count(self):
        from app.api.v1.exhibitions import router
        paths = {r.path for r in router.routes}
        # 4 unique paths: /exhibitions, /exhibitions/{id}, /exhibitions/{id}/status, /exhibitions/{id}/contacts
        assert len(paths) >= 4

    def test_exhibition_lifecycle_valid_transitions(self):
        """Verify the VALID_TRANSITIONS dict in exhibitions module."""
        from app.api.v1.exhibitions import VALID_TRANSITIONS
        assert "planning" in VALID_TRANSITIONS
        assert "active" in VALID_TRANSITIONS["planning"]
        assert "post_show" in VALID_TRANSITIONS["active"]
        assert "completed" in VALID_TRANSITIONS["post_show"]

    def test_exhibition_lifecycle_completed_has_no_transition(self):
        from app.api.v1.exhibitions import VALID_TRANSITIONS
        # 'completed' exists but with empty list (terminal state)
        assert "completed" in VALID_TRANSITIONS
        assert VALID_TRANSITIONS["completed"] == []


# ============================================================
# TestBusinessCardsEndpoints
# ============================================================

class TestBusinessCardsEndpoints:
    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.business_cards import router
        app = FastAPI()
        app.include_router(router)
        return app

    def _client(self):
        from fastapi.testclient import TestClient
        return TestClient(self._make_app())

    def test_scan_requires_auth(self):
        client = self._client()
        resp = client.post("/business-cards/scan")
        assert resp.status_code in (401, 403, 422)

    def test_list_requires_auth(self):
        client = self._client()
        resp = client.get("/business-cards")
        assert resp.status_code in (401, 403, 422)

    def test_get_card_requires_auth(self):
        client = self._client()
        resp = client.get("/business-cards/1")
        assert resp.status_code in (401, 403, 422)

    def test_update_card_requires_auth(self):
        client = self._client()
        resp = client.patch("/business-cards/1", json={"email": "new@test.com"})
        assert resp.status_code in (401, 403, 422)

    def test_delete_card_requires_auth(self):
        client = self._client()
        resp = client.delete("/business-cards/1")
        assert resp.status_code in (401, 403, 422)

    def test_convert_to_lead_requires_auth(self):
        client = self._client()
        resp = client.post("/business-cards/1/convert-to-lead")
        assert resp.status_code in (401, 403, 422)

    def test_business_cards_router_routes_exist(self):
        from app.api.v1.business_cards import router
        paths = {r.path for r in router.routes}
        assert any("scan" in p for p in paths)
        assert any("convert-to-lead" in p for p in paths)

    def test_business_cards_module_has_ocr_endpoint(self):
        """Verify the scan endpoint exists and requires auth (OCR runs server-side)."""
        from app.api.v1.business_cards import router
        paths = {r.path for r in router.routes}
        assert any("scan" in p for p in paths)


# ============================================================
# TestRemarketingTasks
# ============================================================

class TestRemarketingTasks:
    def test_remarketing_module_imports(self):
        from app.tasks import remarketing
        assert hasattr(remarketing, "rescore_c_grade_leads")
        assert hasattr(remarketing, "enrol_b_grade_nurture")
        assert hasattr(remarketing, "advance_remarketing_sequences")

    def test_heuristic_rescore_base_output(self):
        from app.tasks.remarketing import _heuristic_rescore, _score_to_grade
        mock_rfq = MagicMock()
        mock_rfq.lead_score = 50
        mock_rfq.quantity = 500
        mock_rfq.parsed_data = {"product": "CNC machine"}
        mock_rfq.delivery_deadline = datetime(2025, 12, 1, tzinfo=timezone.utc)
        mock_rfq.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        score = _heuristic_rescore(mock_rfq)
        grade = _score_to_grade(score)
        assert isinstance(score, int)
        assert grade in ("A", "B", "C")

    def test_heuristic_rescore_empty_rfq(self):
        from app.tasks.remarketing import _heuristic_rescore, _score_to_grade
        mock_rfq = MagicMock()
        mock_rfq.lead_score = 30
        mock_rfq.quantity = None
        mock_rfq.parsed_data = None
        mock_rfq.delivery_deadline = None
        mock_rfq.created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
        score = _heuristic_rescore(mock_rfq)
        grade = _score_to_grade(score)
        assert isinstance(score, int)
        assert grade in ("A", "B", "C")

    def test_heuristic_rescore_high_quantity_upgrades(self):
        """High quantity + recent deadline should yield higher score."""
        from app.tasks.remarketing import _heuristic_rescore
        mock_rfq_low = MagicMock()
        mock_rfq_low.lead_score = 30
        mock_rfq_low.quantity = None
        mock_rfq_low.parsed_data = None
        mock_rfq_low.delivery_deadline = None
        mock_rfq_low.created_at = datetime(2022, 1, 1, tzinfo=timezone.utc)

        mock_rfq_high = MagicMock()
        mock_rfq_high.lead_score = 30
        mock_rfq_high.quantity = 10000
        mock_rfq_high.parsed_data = {"detail": "lots of data here"}
        mock_rfq_high.delivery_deadline = datetime(2099, 1, 1, tzinfo=timezone.utc)
        mock_rfq_high.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        score_low = _heuristic_rescore(mock_rfq_low)
        score_high = _heuristic_rescore(mock_rfq_high)
        assert score_high > score_low

    def test_grade_thresholds(self):
        """Score → grade mapping should be deterministic."""
        from app.tasks.remarketing import _score_to_grade
        assert _score_to_grade(100) == "A"
        assert _score_to_grade(70) == "A"
        assert _score_to_grade(69) == "B"
        assert _score_to_grade(40) == "B"
        assert _score_to_grade(39) == "C"
        assert _score_to_grade(0) == "C"

    def test_celery_beat_tasks_registered(self):
        from app.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule
        assert "rescore-c-grade-leads-90d" in schedule
        assert "enrol-b-grade-nurture-30d" in schedule
        assert "advance-remarketing-sequences" in schedule
        assert "send-monthly-nurture-emails" in schedule

    def test_advance_sequences_task_is_celery_task(self):
        from app.tasks.remarketing import advance_remarketing_sequences
        assert hasattr(advance_remarketing_sequences, "delay")
        assert hasattr(advance_remarketing_sequences, "apply_async")


# ============================================================
# TestNurtureTasks
# ============================================================

class TestNurtureTasks:
    def test_nurture_module_imports(self):
        from app.tasks import nurture
        assert hasattr(nurture, "send_monthly_nurture_emails")
        assert hasattr(nurture, "generate_nurture_email")

    @pytest.mark.asyncio
    async def test_generate_nurture_email_fallback(self):
        """generate_nurture_email returns dict with subject+body using fallback template."""
        from app.tasks.nurture import generate_nurture_email
        with patch("app.config.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            result = await generate_nurture_email(
                industry="Electronics",
                contact_name=None,
                supplier_name="Demo Corp",
                locale="en"
            )
        assert isinstance(result, dict)
        assert "subject" in result
        assert "body" in result
        assert len(result["subject"]) > 0
        assert len(result["body"]) > 0

    @pytest.mark.asyncio
    async def test_generate_nurture_email_locale_zh(self):
        """generate_nurture_email fallback works for Chinese locale."""
        from app.tasks.nurture import generate_nurture_email
        with patch("app.config.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            result = await generate_nurture_email(
                industry="Automotive",
                contact_name=None,
                supplier_name="台灣精密",
                locale="zh"
            )
        assert isinstance(result, dict)
        assert "subject" in result
        assert "body" in result

    def test_send_monthly_nurture_emails_is_celery_task(self):
        from app.tasks.nurture import send_monthly_nurture_emails
        assert hasattr(send_monthly_nurture_emails, "delay")
        assert hasattr(send_monthly_nurture_emails, "apply_async")

    def test_unsubscribe_helper_exists(self):
        """unsubscribe_contact helper should be importable."""
        from app.tasks.nurture import unsubscribe_contact
        assert callable(unsubscribe_contact)


# ============================================================
# TestExhibitionLifecycle (integration-style unit tests)
# ============================================================

class TestExhibitionLifecycle:
    def test_status_transitions_are_sequential(self):
        from app.api.v1.exhibitions import VALID_TRANSITIONS
        # Verify full chain by following first element in each list
        assert "active" in VALID_TRANSITIONS["planning"]
        assert "post_show" in VALID_TRANSITIONS["active"]
        assert "completed" in VALID_TRANSITIONS["post_show"]
        assert VALID_TRANSITIONS["completed"] == []

    def test_exhibition_status_enum_coverage(self):
        """All expected statuses are covered in transitions or as terminal state."""
        from app.api.v1.exhibitions import VALID_TRANSITIONS
        all_statuses = set(VALID_TRANSITIONS.keys())
        for targets in VALID_TRANSITIONS.values():
            all_statuses.update(targets)
        assert "planning" in all_statuses
        assert "active" in all_statuses
        assert "post_show" in all_statuses
        assert "completed" in all_statuses


# ============================================================
# TestSprint12RouterRegistration
# ============================================================

class TestSprint12RouterRegistration:
    """Verify all Sprint 12 routers are included in the main v1 router."""

    def test_analytics_router_registered(self):
        from app.api.v1 import router
        routes = {r.path for r in router.routes}
        assert any("analytics" in r for r in routes)

    def test_exhibitions_router_registered(self):
        from app.api.v1 import router
        routes = {r.path for r in router.routes}
        assert any("exhibitions" in r for r in routes)

    def test_business_cards_router_registered(self):
        from app.api.v1 import router
        routes = {r.path for r in router.routes}
        assert any("business-cards" in r for r in routes)


# ============================================================
# TestCeleryBeatSchedule
# ============================================================

class TestCeleryBeatSchedule:
    def test_rescore_task_schedule(self):
        from app.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["rescore-c-grade-leads-90d"]
        assert "task" in entry
        assert "remarketing" in entry["task"]

    def test_enrol_nurture_schedule(self):
        from app.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["enrol-b-grade-nurture-30d"]
        assert "task" in entry
        assert "remarketing" in entry["task"]

    def test_advance_sequences_schedule(self):
        from app.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["advance-remarketing-sequences"]
        assert "task" in entry
        assert "remarketing" in entry["task"]

    def test_send_nurture_emails_schedule(self):
        from app.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["send-monthly-nurture-emails"]
        assert "task" in entry
        assert "nurture" in entry["task"]

    def test_all_four_sprint12_tasks_present(self):
        from app.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule
        sprint12_tasks = [
            "rescore-c-grade-leads-90d",
            "enrol-b-grade-nurture-30d",
            "advance-remarketing-sequences",
            "send-monthly-nurture-emails",
        ]
        for task_name in sprint12_tasks:
            assert task_name in schedule, f"Beat task '{task_name}' not found in beat_schedule"
