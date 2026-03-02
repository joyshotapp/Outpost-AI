"""Sprint 8 smoke/integration tests.

These tests validate the implemented contracts for:
- Instantly service adapter
- HubSpot service adapter
- Unified lead grading helpers
- Instantly webhook event handlers
"""

import hashlib
import hmac
from unittest.mock import AsyncMock, patch

import pytest


class TestInstantlyService:
    def test_stub_mode_when_api_key_missing(self):
        from app.services.instantly import InstantlyService

        service = InstantlyService(api_key="")
        assert service.stub_mode is True

    def test_create_campaign_returns_stub_in_stub_mode(self):
        from app.services.instantly import InstantlyService

        service = InstantlyService(api_key="")
        result = service.create_campaign(name="Sprint8 Campaign", daily_limit=50)

        assert result.get("_stub") is True
        assert result.get("name") == "Sprint8 Campaign"
        assert result.get("status") == "draft"

    def test_verify_webhook_signature_accepts_both_signature_formats(self):
        from app.services.instantly import InstantlyService

        payload = b'{"event_type":"email_replied"}'
        secret = "test-secret"
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

        assert InstantlyService.verify_webhook_signature(payload, digest, secret=secret) is True
        assert InstantlyService.verify_webhook_signature(payload, f"sha256={digest}", secret=secret) is True


class TestHubSpotService:
    def test_stub_mode_when_token_missing(self):
        from app.services.hubspot import HubSpotService

        service = HubSpotService(api_token="")
        assert service.stub_mode is True

    def test_upsert_contact_stub_shape(self):
        from app.services.hubspot import HubSpotService

        service = HubSpotService(api_token="")
        result = service.upsert_contact("buyer@example.com", {"firstname": "Buyer"})

        assert result.get("_stub") is True
        assert "id" in result

    def test_sync_lead_to_hubspot_stub_shape(self):
        from app.services.hubspot import HubSpotService

        service = HubSpotService(api_token="")
        result = service.sync_lead_to_hubspot(
            email="a@example.com",
            first_name="A",
            last_name="Lead",
            company="Acme",
            lead_grade="A",
            lead_score=92,
            source="email",
            supplier_id=1,
        )

        assert "contact_id" in result
        assert result.get("deal_id") is None


class TestLeadPipelineHelpers:
    def test_grade_thresholds(self):
        from app.services.lead_pipeline import _compute_grade

        assert _compute_grade(85) == "A"
        assert _compute_grade(60) == "B"
        assert _compute_grade(20) == "C"

    def test_recommended_action_for_email_a_grade(self):
        from app.services.lead_pipeline import _recommended_action

        assert _recommended_action("A", "email") == "hot_lead_sequence_a"
        assert _recommended_action("B", "email") == "draft_reply_b"

    @pytest.mark.asyncio
    async def test_heuristic_scoring_path(self):
        from app.services.lead_pipeline import LeadPipelineService

        service = LeadPipelineService()
        score, breakdown = await service._score_inbound_signal(
            source="email",
            company_name="Acme",
            company_domain="acme.com",
            raw_payload={"job_title": "Procurement Manager"},
        )

        assert 0 <= score <= 100
        assert breakdown.get("source") == "heuristic"


class TestInstantlyWebhookHandlers:
    @pytest.mark.asyncio
    async def test_opened_handler_increments_open_count(self):
        from app.api.v1.webhooks import _instantly_handle_opened

        seq = type("Seq", (), {"emails_opened": 0, "status": "imported", "campaign_id": 1})()
        db = AsyncMock()

        with patch("app.api.v1.webhooks._get_email_seq", new=AsyncMock(return_value=seq)):
            await _instantly_handle_opened(db, "inst-campaign", "buyer@example.com", {})

        assert seq.emails_opened == 1
        assert seq.status == "active"
        assert db.commit.await_count >= 1

    @pytest.mark.asyncio
    async def test_bounced_handler_marks_bounce(self):
        from app.api.v1.webhooks import _instantly_handle_bounced

        seq = type(
            "Seq",
            (),
            {
                "is_bounced": False,
                "bounce_type": None,
                "bounced_at": None,
                "status": "active",
                "campaign_id": 1,
                "id": 10,
            },
        )()
        db = AsyncMock()

        with patch("app.api.v1.webhooks._get_email_seq", new=AsyncMock(return_value=seq)):
            await _instantly_handle_bounced(
                db,
                "inst-campaign",
                "bounce@example.com",
                {"bounce_type": "hard"},
            )

        assert seq.is_bounced is True
        assert seq.bounce_type == "hard"
        assert seq.status == "bounced"

    @pytest.mark.asyncio
    async def test_replied_handler_marks_hot_lead(self):
        from app.api.v1.webhooks import _instantly_handle_replied

        seq = type(
            "Seq",
            (),
            {
                "reply_received": False,
                "reply_text": None,
                "replied_at": None,
                "is_hot_lead": False,
                "hot_lead_reason": None,
                "status": "active",
                "campaign_id": 1,
                "supplier_id": 1,
                "full_name": "Buyer",
                "company_name": "Acme",
                "email": "buyer@example.com",
                "id": 11,
            },
        )()
        db = AsyncMock()

        with (
            patch("app.api.v1.webhooks._get_email_seq", new=AsyncMock(return_value=seq)),
            patch("app.api.v1.webhooks._push_instantly_hot_lead_slack", new=AsyncMock(return_value=None)),
        ):
            await _instantly_handle_replied(
                db,
                "inst-campaign",
                "buyer@example.com",
                {"reply_content": "Interested", "step": 2},
            )

        assert seq.reply_received is True
        assert seq.is_hot_lead is True
        assert seq.status == "replied"
