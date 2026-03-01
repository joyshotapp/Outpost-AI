"""Tests for visitor intent scoring service."""

from app.services.visitor_intent import VisitorIntentService


def test_score_event_high_intent_for_rfq_with_company_identity():
    service = VisitorIntentService()

    result = service.score_event(
        event_type="rfq_submit_click",
        session_duration_seconds=180,
        event_data_raw='{"cta_clicked": true}',
        visitor_email="buyer@example.com",
        visitor_company="Acme Inc",
        visitor_country="US",
    )

    assert result["intent_score"] >= 75
    assert result["intent_level"] == "high"


def test_score_event_low_intent_for_short_page_view():
    service = VisitorIntentService()

    result = service.score_event(
        event_type="page_view",
        session_duration_seconds=5,
        event_data_raw='{}',
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
    )

    assert result["intent_score"] < 45
    assert result["intent_level"] == "low"


def test_score_event_none_event_type_falls_back_to_page_view():
    service = VisitorIntentService()
    result = service.score_event(
        event_type=None,
        session_duration_seconds=30,
        event_data_raw="{}",
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
    )
    assert result["intent_score"] >= 0
    assert result["breakdown"]["event_type"] == "page_view"


def test_score_event_negative_duration_clamped_to_zero():
    service = VisitorIntentService()
    result_neg = service.score_event(
        event_type="page_view",
        session_duration_seconds=-999,
        event_data_raw="{}",
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
    )
    result_zero = service.score_event(
        event_type="page_view",
        session_duration_seconds=0,
        event_data_raw="{}",
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
    )
    assert result_neg["intent_score"] == result_zero["intent_score"]


def test_score_event_all_identity_fields_gives_highest_identity_score():
    service = VisitorIntentService()
    result_full = service.score_event(
        event_type="page_view",
        session_duration_seconds=10,
        event_data_raw="{}",
        visitor_email="a@b.com",
        visitor_company="ACME",
        visitor_country="US",
    )
    result_none = service.score_event(
        event_type="page_view",
        session_duration_seconds=10,
        event_data_raw="{}",
        visitor_email=None,
        visitor_company=None,
        visitor_country=None,
    )
    assert result_full["intent_score"] > result_none["intent_score"]
