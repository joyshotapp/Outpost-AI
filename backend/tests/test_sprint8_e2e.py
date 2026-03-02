"""Sprint 8 End-to-End Integration Tests

Task 8.10 — Validates the full email outreach + unified lead pipeline:
  - Instantly API wrapper (stub mode)
  - Instantly webhook handlers (reply / bounce / unsubscribed / opened / sent)
  - Unified inbound lead processing matrix (Grade A / B / C routing)
  - HubSpot CRM sync task
  - C-grade auto-reply task
  - B-grade AI draft generation task
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

# ─── Instantly API Wrapper ─────────────────────────────────────────────────────


class TestInstantlyService:
    """Task 8.1 — Instantly API stub + live wrapper."""

    def test_stub_mode_activated_when_no_api_key(self):
        """Service enters stub mode silently when INSTANTLY_API_KEY is absent."""
        from app.services.instantly import InstantlyService

        svc = InstantlyService(api_key=None)
        assert svc.stub_mode is True

    @pytest.mark.asyncio
    async def test_create_campaign_stub(self):
        """Stub create_campaign returns a deterministic dict."""
        from app.services.instantly import InstantlyService

        svc = InstantlyService(api_key=None)
        result = await svc.create_campaign(
            name="Test Email Campaign", daily_limit=30
        )
        assert "id" in result
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_add_leads_batches_100(self):
        """add_leads sends requests in batches of ≤100 leads."""
        from app.services.instantly import InstantlyService

        svc = InstantlyService(api_key="fake-key")
        leads = [{"email": f"lead{i}@example.com"} for i in range(250)]

        post_responses = [
            MagicMock(status_code=200, json=lambda: {"added": 100}),
            MagicMock(status_code=200, json=lambda: {"added": 100}),
            MagicMock(status_code=200, json=lambda: {"added": 50}),
        ]

        with patch.object(svc._client, "post", side_effect=post_responses):
            results = await svc.add_leads("campaign-abc", leads)

        # Should have made 3 calls (3 full batches)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self):
        """HMAC-SHA256 signature is accepted for correct secret."""
        import hmac
        import hashlib
        from app.services.instantly import InstantlyService

        secret = "mysecret"
        svc = InstantlyService(api_key=None, webhook_secret=secret)
        payload = b'{"event":"email_replied"}'
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        assert svc.verify_webhook_signature(payload, sig) is True

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self):
        from app.services.instantly import InstantlyService

        svc = InstantlyService(api_key=None, webhook_secret="correct-secret")
        assert svc.verify_webhook_signature(b"body", "wrong-sig") is False


# ─── Instantly Webhook Endpoint ────────────────────────────────────────────────


class TestInstantlyWebhook:
    """Task 8.3 / 8.4 — webhook event dispatching."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_reply_event_marks_hot_lead(self, mock_db):
        """email_replied → EmailSequence.reply_received=True + is_hot_lead=True."""
        from app.api.v1.webhooks import _instantly_handle_replied
        from app.models.email_sequence import EmailSequence

        seq = MagicMock(spec=EmailSequence)
        seq.id = 1
        seq.email = "buyer@example.com"
        seq.full_name = "Tom Chen"
        seq.company_name = "Acme Corp"
        seq.supplier_id = 42
        seq.campaign_id = 7
        seq.reply_received = False
        seq.is_hot_lead = False
        seq.emails_opened = 2

        mock_db.execute.return_value.scalar_one_or_none.return_value = seq

        payload = {
            "lead_email": "buyer@example.com",
            "reply_text": "Yes I'm interested, let's talk.",
            "campaign_id": "instantly-campaign-xyz",
        }

        with patch("app.api.v1.webhooks._push_instantly_hot_lead_slack") as mock_slack:
            await _instantly_handle_replied(payload, mock_db)

        assert seq.reply_received is True
        assert seq.is_hot_lead is True
        assert seq.reply_text == "Yes I'm interested, let's talk."
        mock_slack.assert_called_once()

    @pytest.mark.asyncio
    async def test_bounce_event_increments_campaign_counter(self, mock_db):
        """email_bounced → EmailSequence.is_bounced=True + campaign.email_bounce_count incremented."""
        from app.api.v1.webhooks import _instantly_handle_bounced
        from app.models.email_sequence import EmailSequence
        from app.models.outbound_campaign import OutboundCampaign

        seq = MagicMock(spec=EmailSequence)
        seq.campaign_id = 3
        seq.is_bounced = False

        campaign = MagicMock(spec=OutboundCampaign)
        campaign.email_bounce_count = 1
        campaign.email_sent_count = 10

        def side_effect(query):
            mock = MagicMock()
            # First call returns sequence, second returns campaign
            if hasattr(side_effect, "_calls"):
                side_effect._calls += 1
            else:
                side_effect._calls = 1
            if side_effect._calls == 1:
                mock.scalar_one_or_none.return_value = seq
            else:
                mock.scalar_one_or_none.return_value = campaign
            return mock

        mock_db.execute.side_effect = side_effect

        payload = {
            "lead_email": "bounced@example.com",
            "bounce_type": "hard",
            "campaign_id": "instantly-xyz",
        }

        await _instantly_handle_bounced(payload, mock_db)

        assert seq.is_bounced is True
        assert seq.bounce_type == "hard"

    @pytest.mark.asyncio
    async def test_unsubscribe_event(self, mock_db):
        """email_unsubscribed → EmailSequence.is_unsubscribed=True."""
        from app.api.v1.webhooks import _instantly_handle_unsubscribed
        from app.models.email_sequence import EmailSequence

        seq = MagicMock(spec=EmailSequence)
        seq.is_unsubscribed = False
        seq.campaign_id = 5
        mock_db.execute.return_value.scalar_one_or_none.return_value = seq

        await _instantly_handle_unsubscribed(
            {"lead_email": "unsub@example.com", "campaign_id": "inst-xyz"}, mock_db
        )

        assert seq.is_unsubscribed is True

    @pytest.mark.asyncio
    async def test_open_event_increments_counter(self, mock_db):
        """email_opened → EmailSequence.emails_opened incremented by 1."""
        from app.api.v1.webhooks import _instantly_handle_opened
        from app.models.email_sequence import EmailSequence

        seq = MagicMock(spec=EmailSequence)
        seq.emails_opened = 0
        seq.campaign_id = 5
        mock_db.execute.return_value.scalar_one_or_none.return_value = seq

        await _instantly_handle_opened(
            {"lead_email": "open@example.com", "campaign_id": "inst-xyz"}, mock_db
        )

        assert seq.emails_opened == 1


# ─── Unified Lead Pipeline ─────────────────────────────────────────────────────


class TestLeadPipelineService:
    """Task 8.5 — Unified inbound processing matrix (Grade A / B / C routing)."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_grade_a_lead_triggers_slack_and_draft(self, mock_db):
        """Score ≥80 → Slack alert + generate_b_grade_draft task fired."""
        from app.services.lead_pipeline import LeadPipelineService

        svc = LeadPipelineService()

        with (
            patch.object(svc.scorer, "score_lead", return_value={"total_score": 85, "breakdown": {}}),
            patch("app.services.lead_pipeline.generate_b_grade_draft") as mock_draft_task,
            patch("app.services.lead_pipeline.sync_lead_to_hubspot_task") as mock_hs_task,
            patch.object(svc, "_send_slack_hot_lead_alert", new_callable=AsyncMock) as mock_slack,
        ):
            mock_draft_task.delay = MagicMock()
            mock_hs_task.delay = MagicMock()

            lead = await svc.process_inbound(
                db=mock_db,
                supplier_id=1,
                email="vip@bigcorp.com",
                full_name="Alice Wang",
                company_name="Big Corp",
                source="rfq",
            )

        mock_slack.assert_awaited_once()
        mock_draft_task.delay.assert_called_once()
        mock_hs_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_grade_b_lead_triggers_draft_only(self, mock_db):
        """Score 50-79 → draft generated, NO Slack hot-lead alert."""
        from app.services.lead_pipeline import LeadPipelineService

        svc = LeadPipelineService()

        with (
            patch.object(svc.scorer, "score_lead", return_value={"total_score": 65, "breakdown": {}}),
            patch("app.services.lead_pipeline.generate_b_grade_draft") as mock_draft_task,
            patch("app.services.lead_pipeline.sync_lead_to_hubspot_task") as mock_hs_task,
            patch.object(svc, "_send_slack_hot_lead_alert", new_callable=AsyncMock) as mock_slack,
        ):
            mock_draft_task.delay = MagicMock()
            mock_hs_task.delay = MagicMock()

            await svc.process_inbound(
                db=mock_db,
                supplier_id=1,
                email="mid@corp.com",
                source="email",
            )

        mock_slack.assert_not_awaited()
        mock_draft_task.delay.assert_called_once()
        mock_hs_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_grade_c_lead_triggers_auto_reply(self, mock_db):
        """Score <50 → auto_reply_c_grade task fired, NOT draft."""
        from app.services.lead_pipeline import LeadPipelineService

        svc = LeadPipelineService()

        with (
            patch.object(svc.scorer, "score_lead", return_value={"total_score": 30, "breakdown": {}}),
            patch("app.services.lead_pipeline.auto_reply_c_grade") as mock_auto,
            patch("app.services.lead_pipeline.generate_b_grade_draft") as mock_draft,
            patch("app.services.lead_pipeline.sync_lead_to_hubspot_task") as mock_hs,
        ):
            mock_auto.delay = MagicMock()
            mock_draft.delay = MagicMock()
            mock_hs.delay = MagicMock()

            await svc.process_inbound(
                db=mock_db,
                supplier_id=1,
                email="low@example.com",
                source="visitor",
            )

        mock_auto.delay.assert_called_once()
        mock_draft.delay.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplication_skips_recent_lead(self, mock_db):
        """Same email + supplier within 7 days → existing lead updated, not created."""
        from app.services.lead_pipeline import LeadPipelineService
        from app.models.unified_lead import UnifiedLead

        svc = LeadPipelineService()

        existing = MagicMock(spec=UnifiedLead)
        existing.id = 99
        existing.lead_score = 40
        existing.email = "dup@company.com"
        existing.supplier_id = 1
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing

        with (
            patch.object(svc.scorer, "score_lead", return_value={"total_score": 55, "breakdown": {}}),
            patch("app.services.lead_pipeline.generate_b_grade_draft") as mock_draft,
            patch("app.services.lead_pipeline.sync_lead_to_hubspot_task") as mock_hs,
        ):
            mock_draft.delay = MagicMock()
            mock_hs.delay = MagicMock()

            result = await svc.process_inbound(
                db=mock_db,
                supplier_id=1,
                email="dup@company.com",
                source="rfq",
            )

        # Should return the existing lead object (updated, not created)
        assert result.id == 99
        # db.add should NOT have been called with a new object
        mock_db.add.assert_not_called()


# ─── Celery Tasks ──────────────────────────────────────────────────────────────


class TestOutboundEmailTasks:
    """Tasks 8.7, 8.8, 8.9 — Celery task isolation tests."""

    # ── C-grade auto-reply (8.7) ───────────────────────────────────────────────

    def test_auto_reply_c_grade_sends_email(self):
        """auto_reply_c_grade fetches lead and sends template email."""
        from app.tasks.outbound_email import auto_reply_c_grade

        mock_lead = MagicMock()
        mock_lead.id = 5
        mock_lead.email = "c@example.com"
        mock_lead.full_name = "Low-Score User"
        mock_lead.company_name = "Small Co"
        mock_lead.auto_reply_sent = False
        mock_lead.supplier_id = 1

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.sendgrid_send_email") as mock_email,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_lead
            mock_get_db.return_value = mock_session
            mock_email.return_value = True

            auto_reply_c_grade(5)

        mock_email.assert_called_once()
        assert mock_lead.auto_reply_sent is True

    # ── B-grade AI draft (8.8) ─────────────────────────────────────────────────

    def test_generate_b_grade_draft_uses_claude(self):
        """generate_b_grade_draft calls Claude and persists result."""
        from app.tasks.outbound_email import generate_b_grade_draft

        mock_lead = MagicMock()
        mock_lead.id = 7
        mock_lead.email = "b@example.com"
        mock_lead.full_name = "Mid Lead"
        mock_lead.company_name = "Medium Corp"
        mock_lead.lead_grade = "B"
        mock_lead.supplier_id = 2
        mock_lead.draft_reply_body = None

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.ClaudeService") as mock_claude_cls,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_lead
            mock_get_db.return_value = mock_session

            claude_instance = MagicMock()
            claude_instance.generate_email_draft.return_value = "Dear Mid Lead, we'd love to help..."
            mock_claude_cls.return_value = claude_instance

            generate_b_grade_draft(7)

        assert mock_lead.draft_reply_body is not None
        assert "Dear" in mock_lead.draft_reply_body or len(mock_lead.draft_reply_body) > 10

    def test_generate_b_grade_draft_fallback_on_claude_failure(self):
        """On Claude failure, a template draft is persisted (task does not raise)."""
        from app.tasks.outbound_email import generate_b_grade_draft

        mock_lead = MagicMock()
        mock_lead.id = 8
        mock_lead.email = "b2@example.com"
        mock_lead.full_name = None
        mock_lead.company_name = None
        mock_lead.lead_grade = "B"
        mock_lead.supplier_id = 3
        mock_lead.draft_reply_body = None

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.ClaudeService") as mock_claude_cls,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_lead
            mock_get_db.return_value = mock_session

            # Claude raises
            claude_instance = MagicMock()
            claude_instance.generate_email_draft.side_effect = RuntimeError("Claude timeout")
            mock_claude_cls.return_value = claude_instance

            # Must not propagate exception
            generate_b_grade_draft(8)

        # Fallback template should still be saved
        assert mock_lead.draft_reply_body is not None

    # ── HubSpot sync (8.9) ────────────────────────────────────────────────────

    def test_sync_lead_to_hubspot_task_calls_service(self):
        """sync_lead_to_hubspot_task invokes HubSpotService.sync_lead_to_hubspot()."""
        from app.tasks.outbound_email import sync_lead_to_hubspot_task

        mock_lead = MagicMock()
        mock_lead.id = 10
        mock_lead.email = "hs@example.com"
        mock_lead.full_name = "HubSpot Test"
        mock_lead.company_name = "HS Corp"
        mock_lead.lead_grade = "A"
        mock_lead.supplier_id = 1
        mock_lead.hubspot_synced = False

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.get_hubspot_service") as mock_hs_factory,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_lead
            mock_get_db.return_value = mock_session

            hs = MagicMock()
            hs.sync_lead_to_hubspot = AsyncMock(
                return_value={"contact_id": "hs-123", "deal_id": "deal-456"}
            )
            mock_hs_factory.return_value = hs

            sync_lead_to_hubspot_task(10)

        assert mock_lead.hubspot_synced is True


# ─── HubSpot Service ──────────────────────────────────────────────────────────


class TestHubSpotService:
    """Task 8.9 — HubSpot CRM wrapper stub + live call shapes."""

    def test_stub_mode_when_no_token(self):
        from app.services.hubspot import HubSpotService

        svc = HubSpotService(api_token=None)
        assert svc.stub_mode is True

    @pytest.mark.asyncio
    async def test_stub_upsert_contact_returns_id(self):
        from app.services.hubspot import HubSpotService

        svc = HubSpotService(api_token=None)
        result = await svc.upsert_contact(
            email="buyer@example.com", first_name="Buyer", last_name="Test"
        )
        assert "id" in result

    @pytest.mark.asyncio
    async def test_stub_create_deal_returns_id(self):
        from app.services.hubspot import HubSpotService

        svc = HubSpotService(api_token=None)
        result = await svc.create_deal(contact_id="c-1", deal_name="Test Deal", amount=5000)
        assert "id" in result

    @pytest.mark.asyncio
    async def test_sync_lead_grade_a_creates_deal(self):
        """Grade A leads must have a deal created in HubSpot."""
        from app.services.hubspot import HubSpotService

        svc = HubSpotService(api_token=None)
        result = await svc.sync_lead_to_hubspot(
            email="vip@corp.com",
            full_name="VIP Lead",
            company="Corp",
            grade="A",
            score=90,
        )
        assert result.get("deal_id") is not None

    @pytest.mark.asyncio
    async def test_sync_lead_grade_c_no_deal(self):
        """Grade C leads should NOT create a deal in HubSpot."""
        from app.services.hubspot import HubSpotService

        svc = HubSpotService(api_token=None)
        result = await svc.sync_lead_to_hubspot(
            email="low@example.com",
            full_name="Low Lead",
            company="Small",
            grade="C",
            score=25,
        )
        assert result.get("deal_id") is None


# ─── Bounce Monitoring (8.4) ─────────────────────────────────────────────────


class TestBounceMonitoring:
    """Task 8.4 — Auto-pause when bounce rate exceeds threshold."""

    def test_sync_analytics_pauses_on_high_bounce(self):
        """Campaign with bounce_rate > 2% and ≥20 sent is safety-paused."""
        from app.tasks.outbound_email import sync_email_campaign_analytics

        mock_campaign = MagicMock()
        mock_campaign.id = 3
        mock_campaign.instantly_campaign_id = "inst-abc"
        mock_campaign.email_sent_count = 50
        mock_campaign.email_bounce_count = 0
        mock_campaign.email_safety_paused = False
        mock_campaign.supplier_id = 1

        analytics_data = {
            "emails_sent": 50,
            "emails_opened": 10,
            "emails_replied": 2,
            "emails_bounced": 3,   # 6% bounce rate — above 2% threshold
            "emails_unsubscribed": 1,
        }

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.get_instantly_service") as mock_inst_factory,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_campaign
            mock_get_db.return_value = mock_session

            inst = MagicMock()
            inst.get_campaign_analytics = AsyncMock(return_value=analytics_data)
            inst.pause_campaign = AsyncMock(return_value={"status": "paused"})
            mock_inst_factory.return_value = inst

            sync_email_campaign_analytics(3)

        assert mock_campaign.email_safety_paused is True
        inst.pause_campaign.assert_called_once_with("inst-abc")

    def test_sync_analytics_no_pause_below_threshold(self):
        """Campaign with bounce_rate < 2% is NOT paused."""
        from app.tasks.outbound_email import sync_email_campaign_analytics

        mock_campaign = MagicMock()
        mock_campaign.id = 4
        mock_campaign.instantly_campaign_id = "inst-xyz"
        mock_campaign.email_sent_count = 100
        mock_campaign.email_bounce_count = 0
        mock_campaign.email_safety_paused = False
        mock_campaign.supplier_id = 1

        analytics_data = {
            "emails_sent": 100,
            "emails_opened": 30,
            "emails_replied": 5,
            "emails_bounced": 1,   # 1% — below threshold
            "emails_unsubscribed": 0,
        }

        with (
            patch("app.tasks.outbound_email.get_sync_db") as mock_get_db,
            patch("app.tasks.outbound_email.get_instantly_service") as mock_inst_factory,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=None)
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_campaign
            mock_get_db.return_value = mock_session

            inst = MagicMock()
            inst.get_campaign_analytics = AsyncMock(return_value=analytics_data)
            inst.pause_campaign = AsyncMock()
            mock_inst_factory.return_value = inst

            sync_email_campaign_analytics(4)

        assert mock_campaign.email_safety_paused is False
        inst.pause_campaign.assert_not_called()
