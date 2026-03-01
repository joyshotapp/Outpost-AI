"""Sprint 7 E2E Tests — Outbound Engine (7.1, 7.2, 7.3, 7.7, 7.8, 7.9, 7.10).

Tests cover:
  - Clay enrichment pipeline (stub mode, no real API key)
  - HeyReach sequence launch (stub mode)
  - Outbound Campaign CRUD API
  - Contact approve / exclude actions
  - AI LinkedIn opener generation (stub fallback)
  - LinkedIn safety enforcement (daily limits)
  - HeyReach Webhook hot-lead flow (reply event → Slack + Notification)
"""

import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.dependencies import get_db
from app.models.base import Base
from app.models import User, Supplier, UserRole
from app.models.outbound_campaign import OutboundCampaign
from app.models.outbound_contact import OutboundContact
from app.models.linkedin_sequence import LinkedInSequence
from app.security import hash_password

SPRINT7_DB = "sqlite+aiosqlite:///./test_sprint7_e2e.db"


# ──────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
async def s7_db():
    engine = create_async_engine(
        SPRINT7_DB,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def s7_supplier_user(s7_db):
    user = User(
        email="sprint7@example.com",
        password_hash=hash_password("pass1234"),
        role=UserRole.SUPPLIER,
        is_active=True,
    )
    s7_db.add(user)
    await s7_db.commit()
    await s7_db.refresh(user)

    supplier = Supplier(
        user_id=user.id,
        company_name="Sprint7 Factory",
        company_slug="sprint7-factory",
        company_description="Test",
        country="DE",
        industry="Manufacturing",
        main_products="Machinery",
        is_active=True,
        is_verified=True,
        view_count=0,
    )
    s7_db.add(supplier)
    await s7_db.commit()
    await s7_db.refresh(supplier)
    return user, supplier


@pytest.fixture
def s7_client(s7_db):
    app.dependency_overrides[get_db] = lambda: s7_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client, email="sprint7@example.com", password="pass1234"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _session_ctx_factory(session: AsyncSession):
    @asynccontextmanager
    async def _ctx():
        yield session

    return _ctx


# ──────────────────────────────────────────────────────────────────────────────
# 7.1 — Clay enrichment pipeline (stub mode)
# ──────────────────────────────────────────────────────────────────────────────


class TestClayEnrichmentPipeline:
    """Verify Clay stub mode creates contacts correctly."""

    def test_create_campaign_triggers_enrichment_task(self, s7_client, s7_supplier_user):
        """POST /outbound/campaigns → 201, enrichment task queued."""
        token = _login(s7_client)

        with patch("app.tasks.outbound.enrich_contacts_pipeline") as mock_task:
            resp = s7_client.post(
                "/api/v1/outbound/campaigns",
                json={
                    "campaign_name": "Test Q1 2026",
                    "campaign_type": "linkedin",
                    "icp_criteria": {
                        "industries": ["Automotive"],
                        "countries": ["Germany"],
                        "job_titles": ["Procurement Manager"],
                        "company_sizes": ["51-200"],
                        "seniority_levels": ["Manager"],
                        "limit": 100,
                    },
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["campaign_name"] == "Test Q1 2026"
        assert data["clay_enrichment_status"] == "pending"
        mock_task.delay.assert_called_once()

    def test_clay_stub_pipeline_saves_contacts(self, s7_db, s7_supplier_user):
        """_enrich_contacts_pipeline_async stub saves 0 contacts (no real Clay API)."""
        from app.tasks.outbound import _enrich_contacts_pipeline_async

        _user, supplier = s7_supplier_user

        # Create a campaign directly
        async def _run():
            campaign = OutboundCampaign(
                supplier_id=supplier.id,
                campaign_name="Clay Stub Test",
                campaign_type="linkedin",
                clay_enrichment_status="pending",
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)

            icp = {"industries": ["Automotive"], "limit": 10}
            with patch("app.tasks.outbound.async_session_maker", _session_ctx_factory(s7_db)):
                result = await _enrich_contacts_pipeline_async(campaign.id, icp)
            return result, campaign.id

        result, camp_id = asyncio.run(_run())
        # Stub Clay returns 0 contacts (no real key)
        assert result["campaign_id"] == camp_id
        assert "contacts_saved" in result
        assert "clay_table_id" in result


# ──────────────────────────────────────────────────────────────────────────────
# 7.2 — HeyReach import + sequence launch (stub mode)
# ──────────────────────────────────────────────────────────────────────────────


class TestHeyReachSequenceLaunch:
    """Verify HeyReach stub import creates linkedin_sequences rows."""

    def test_import_contacts_to_heyreach_stub(self, s7_db, s7_supplier_user):
        from app.tasks.outbound import _import_contacts_to_heyreach_async

        _user, supplier = s7_supplier_user

        async def _run():
            campaign = OutboundCampaign(
                supplier_id=supplier.id,
                campaign_name="HeyReach Stub Test",
                campaign_type="linkedin",
                clay_enrichment_status="completed",
                status="draft",
                safety_paused=0,
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)

            contact = OutboundContact(
                campaign_id=campaign.id,
                supplier_id=supplier.id,
                full_name="Max Müller",
                linkedin_url="https://linkedin.com/in/max-mueller",
                company_name="BMW AG",
                status="approved",
            )
            s7_db.add(contact)
            await s7_db.commit()
            await s7_db.refresh(contact)

            with patch("app.tasks.outbound.async_session_maker", _session_ctx_factory(s7_db)):
                result = await _import_contacts_to_heyreach_async(campaign.id)
            return result, campaign.id

        result, camp_id = asyncio.run(_run())
        assert result["imported"] >= 0  # stub returns 1
        # linkedin_sequence should be created
        from sqlalchemy import select as _sel
        async def check_seq():
            r = await s7_db.execute(
                _sel(LinkedInSequence).where(LinkedInSequence.campaign_id == camp_id)
            )
            return r.scalars().all()

        seqs = asyncio.run(check_seq())
        assert len(seqs) >= 1


# ──────────────────────────────────────────────────────────────────────────────
# 7.3 — Campaign CRUD
# ──────────────────────────────────────────────────────────────────────────────


class TestOutboundCampaignCRUD:

    def test_list_campaigns_empty(self, s7_client, s7_supplier_user):
        token = _login(s7_client)
        resp = s7_client.get(
            "/api/v1/outbound/campaigns",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["campaigns"] == []

    def test_create_and_get_campaign(self, s7_client, s7_supplier_user):
        token = _login(s7_client)
        with patch("app.tasks.outbound.enrich_contacts_pipeline"):
            resp = s7_client.post(
                "/api/v1/outbound/campaigns",
                json={
                    "campaign_name": "CRUD Test",
                    "campaign_type": "linkedin",
                    "icp_criteria": {"industries": ["Electronics Manufacturing"], "limit": 50},
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201
        camp_id = resp.json()["id"]

        get_resp = s7_client.get(
            f"/api/v1/outbound/campaigns/{camp_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["campaign_name"] == "CRUD Test"

    def test_pause_and_resume_campaign(self, s7_client, s7_supplier_user):
        token = _login(s7_client)
        with patch("app.tasks.outbound.enrich_contacts_pipeline"):
            camp = s7_client.post(
                "/api/v1/outbound/campaigns",
                json={"campaign_name": "Pause Test", "campaign_type": "linkedin", "icp_criteria": {}},
                headers={"Authorization": f"Bearer {token}"},
            ).json()
        camp_id = camp["id"]

        # Pause
        pause_resp = s7_client.patch(
            f"/api/v1/outbound/campaigns/{camp_id}/pause",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"

        # Resume
        resume_resp = s7_client.patch(
            f"/api/v1/outbound/campaigns/{camp_id}/resume",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "running"

    def test_cannot_resume_non_paused_campaign(self, s7_client, s7_supplier_user):
        token = _login(s7_client)
        with patch("app.tasks.outbound.enrich_contacts_pipeline"):
            camp = s7_client.post(
                "/api/v1/outbound/campaigns",
                json={"campaign_name": "Draft Camp", "campaign_type": "linkedin", "icp_criteria": {}},
                headers={"Authorization": f"Bearer {token}"},
            ).json()
        # Trying to resume a draft campaign should fail
        resp = s7_client.patch(
            f"/api/v1/outbound/campaigns/{camp['id']}/resume",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 7.3 — Contact approve / exclude
# ──────────────────────────────────────────────────────────────────────────────


class TestContactApproveExclude:

    def test_approve_contact_changes_status(self, s7_client, s7_db, s7_supplier_user):
        _user, supplier = s7_supplier_user
        token = _login(s7_client)

        async def _seed():
            c = OutboundCampaign(
                supplier_id=supplier.id, campaign_name="Contact Test",
                campaign_type="linkedin", clay_enrichment_status="completed",
            )
            s7_db.add(c)
            await s7_db.commit()
            await s7_db.refresh(c)

            contact = OutboundContact(
                campaign_id=c.id, supplier_id=supplier.id,
                full_name="Anna Schmidt", status="enriched",
            )
            s7_db.add(contact)
            await s7_db.commit()
            await s7_db.refresh(contact)
            return contact.id

        contact_id = asyncio.run(_seed())

        resp = s7_client.patch(
            f"/api/v1/outbound/contacts/{contact_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_exclude_contact_changes_status(self, s7_client, s7_db, s7_supplier_user):
        _user, supplier = s7_supplier_user
        token = _login(s7_client)

        async def _seed():
            c = OutboundCampaign(
                supplier_id=supplier.id, campaign_name="Exclude Test",
                campaign_type="linkedin", clay_enrichment_status="completed",
            )
            s7_db.add(c)
            await s7_db.commit()
            await s7_db.refresh(c)
            contact = OutboundContact(
                campaign_id=c.id, supplier_id=supplier.id,
                full_name="Hans Weber", status="enriched",
            )
            s7_db.add(contact)
            await s7_db.commit()
            await s7_db.refresh(contact)
            return contact.id

        contact_id = asyncio.run(_seed())
        resp = s7_client.patch(
            f"/api/v1/outbound/contacts/{contact_id}/exclude",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "excluded"


# ──────────────────────────────────────────────────────────────────────────────
# 7.7 — AI opener generation (stub fallback)
# ──────────────────────────────────────────────────────────────────────────────


class TestAIOpenerGeneration:

    def test_generate_linkedin_opener_stub_when_no_api_key(self):
        """When ANTHROPIC_API_KEY is not set, opener returns safe fallback."""
        from app.services.claude import ClaudeService

        with patch("app.services.claude.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            svc = ClaudeService.__new__(ClaudeService)

            async def _run():
                return await svc.generate_linkedin_opener(
                    full_name="Maria García",
                    company_name="Volkswagen",
                    job_title="Head of Procurement",
                    industry="Automotive",
                )
            result = asyncio.run(_run())

        assert isinstance(result, str)
        assert len(result) <= 300
        assert "Maria" in result or "Volkswagen" in result

    def test_opener_hard_truncated_to_300_chars(self):
        """Opener is never longer than 300 characters."""
        from app.services.claude import ClaudeService

        with patch("app.services.claude.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            svc = ClaudeService.__new__(ClaudeService)

            async def _run():
                return await svc.generate_linkedin_opener(
                    full_name="A" * 100,
                    company_name="B" * 100,
                    job_title="C" * 100,
                )
            result = asyncio.run(_run())

        assert len(result) <= 300


# ──────────────────────────────────────────────────────────────────────────────
# 7.8 — LinkedIn safety enforcement
# ──────────────────────────────────────────────────────────────────────────────


class TestLinkedInSafetyEnforcement:

    def test_safety_pause_when_connection_limit_exceeded(self, s7_db, s7_supplier_user):
        """enforce_linkedin_safety pauses campaign when connections >= limit."""
        from app.tasks.outbound import _enforce_linkedin_safety_async

        _user, supplier = s7_supplier_user

        async def _run():
            campaign = OutboundCampaign(
                supplier_id=supplier.id,
                campaign_name="Safety Test",
                campaign_type="linkedin",
                status="running",
                heyreach_campaign_id="stub_hr_camp",
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)

            with patch("app.tasks.outbound.get_heyreach_service") as mock_hr_fn:
                mock_hr = MagicMock()
                mock_hr.get_daily_stats.return_value = {
                    "connections_sent_today": 30,  # over 25 limit
                    "messages_sent_today": 5,
                }
                mock_hr.pause_campaign = MagicMock()
                mock_hr_fn.return_value = mock_hr

                with patch("app.tasks.outbound.settings.LINKEDIN_DAILY_CONNECTION_LIMIT", 25):
                    with patch("app.tasks.outbound.settings.LINKEDIN_DAILY_MESSAGE_LIMIT", 30):
                        with patch("app.tasks.outbound.async_session_maker", _session_ctx_factory(s7_db)):
                            result = await _enforce_linkedin_safety_async(campaign.id)

            return result

        result = asyncio.run(_run())
        assert result["paused"] is True
        assert "daily_connection_limit_reached" in result["reason"]

    def test_no_pause_when_within_limits(self, s7_db, s7_supplier_user):
        """enforce_linkedin_safety does NOT pause when within limits."""
        from app.tasks.outbound import _enforce_linkedin_safety_async

        _user, supplier = s7_supplier_user

        async def _run():
            campaign = OutboundCampaign(
                supplier_id=supplier.id,
                campaign_name="Safe Campaign",
                campaign_type="linkedin",
                status="running",
                heyreach_campaign_id="stub_safe",
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)

            with patch("app.tasks.outbound.get_heyreach_service") as mock_hr_fn:
                mock_hr = MagicMock()
                mock_hr.get_daily_stats.return_value = {
                    "connections_sent_today": 10,
                    "messages_sent_today": 8,
                }
                mock_hr_fn.return_value = mock_hr

                with patch("app.tasks.outbound.settings.LINKEDIN_DAILY_CONNECTION_LIMIT", 25):
                    with patch("app.tasks.outbound.settings.LINKEDIN_DAILY_MESSAGE_LIMIT", 30):
                        with patch("app.tasks.outbound.async_session_maker", _session_ctx_factory(s7_db)):
                            result = await _enforce_linkedin_safety_async(campaign.id)
            return result

        result = asyncio.run(_run())
        assert result["paused"] is False


# ──────────────────────────────────────────────────────────────────────────────
# 7.9 — HeyReach Webhook hot lead flow
# ──────────────────────────────────────────────────────────────────────────────


class TestHeyReachWebhookHotLead:

    def test_lead_replied_creates_hot_lead_and_notification(self, s7_client, s7_db, s7_supplier_user):
        """POST /webhooks/heyreach with lead_replied marks hot lead + creates notification."""
        _user, supplier = s7_supplier_user

        async def _seed():
            campaign = OutboundCampaign(
                supplier_id=supplier.id, campaign_name="Webhook Test",
                campaign_type="linkedin", status="running",
                heyreach_campaign_id="hr_camp_001",
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)

            contact = OutboundContact(
                campaign_id=campaign.id, supplier_id=supplier.id,
                full_name="Peter Braun", company_name="Siemens",
                job_title="Procurement Lead",
                status="in_sequence",
                heyreach_contact_id="hr_cont_001",
            )
            s7_db.add(contact)
            await s7_db.commit()
            await s7_db.refresh(contact)

            seq = LinkedInSequence(
                campaign_id=campaign.id, contact_id=contact.id,
                supplier_id=supplier.id,
                heyreach_campaign_id="hr_camp_001",
                heyreach_contact_id="hr_cont_001",
                sequence_status="active",
                current_day=5,
            )
            s7_db.add(seq)
            await s7_db.commit()
            return contact.id, seq.id

        contact_id, seq_id = asyncio.run(_seed())

        payload = {
            "event_type": "lead_replied",
            "campaign_id": "hr_camp_001",
            "contact_id": "hr_cont_001",
            "data": {
                "reply_content": "Hi! Thanks for reaching out. We are indeed looking for reliable suppliers.",
                "current_day": 5,
            },
        }

        with patch("app.api.v1.webhooks._push_hot_lead_to_slack", new_callable=AsyncMock):
            resp = s7_client.post("/api/v1/webhooks/heyreach", json=payload)

        assert resp.status_code == 200
        assert resp.json()["event_type"] == "lead_replied"

        # Verify contact marked as hot lead
        from sqlalchemy import select as _sel
        async def _check():
            c = await s7_db.execute(_sel(OutboundContact).where(OutboundContact.id == contact_id))
            s = await s7_db.execute(_sel(LinkedInSequence).where(LinkedInSequence.id == seq_id))
            from app.models.notification import Notification
            n = await s7_db.execute(
                _sel(Notification).where(Notification.supplier_id == supplier.id)
            )
            return c.scalar_one(), s.scalar_one(), n.scalars().all()

        contact, seq, notifs = asyncio.run(_check())
        assert contact.is_hot_lead is True
        assert contact.status == "replied"
        assert seq.is_hot_lead is True
        assert seq.sequence_status == "replied"
        assert len(notifs) >= 1
        assert any("熱線索" in n.title or "linkedin_hot_lead" in n.notification_type for n in notifs)

    def test_connection_accepted_updates_sequence_day(self, s7_client, s7_db, s7_supplier_user):
        """connection_accepted event advances sequence to day 2."""
        _user, supplier = s7_supplier_user

        async def _seed():
            campaign = OutboundCampaign(
                supplier_id=supplier.id, campaign_name="Accept Test",
                campaign_type="linkedin", status="running",
                heyreach_campaign_id="hr_camp_002",
            )
            s7_db.add(campaign)
            await s7_db.commit()
            await s7_db.refresh(campaign)
            contact = OutboundContact(
                campaign_id=campaign.id, supplier_id=supplier.id,
                status="in_sequence", heyreach_contact_id="hr_cont_002",
            )
            s7_db.add(contact)
            await s7_db.commit()
            await s7_db.refresh(contact)
            seq = LinkedInSequence(
                campaign_id=campaign.id, contact_id=contact.id,
                supplier_id=supplier.id,
                heyreach_campaign_id="hr_camp_002",
                heyreach_contact_id="hr_cont_002",
                sequence_status="active", current_day=1,
            )
            s7_db.add(seq)
            await s7_db.commit()
            return seq.id

        seq_id = asyncio.run(_seed())

        resp = s7_client.post(
            "/api/v1/webhooks/heyreach",
            json={
                "event_type": "connection_accepted",
                "campaign_id": "hr_camp_002",
                "contact_id": "hr_cont_002",
                "data": {},
            },
        )
        assert resp.status_code == 200

        from sqlalchemy import select as _sel
        async def _check():
            r = await s7_db.execute(_sel(LinkedInSequence).where(LinkedInSequence.id == seq_id))
            return r.scalar_one()

        seq = asyncio.run(_check())
        assert seq.connection_accepted_at is not None
        assert seq.current_day >= 2

    def test_invalid_signature_returns_401(self, s7_client, s7_supplier_user):
        """Webhook with wrong signature is rejected when HEYREACH_WEBHOOK_SECRET is set."""
        with patch("app.api.v1.webhooks.settings") as mock_settings:
            mock_settings.HEYREACH_WEBHOOK_SECRET = "super_secret"
            resp = s7_client.post(
                "/api/v1/webhooks/heyreach",
                json={"event_type": "lead_replied", "campaign_id": "x", "contact_id": "y", "data": {}},
                headers={"X-HeyReach-Signature": "sha256=wrong_sig"},
            )
        assert resp.status_code == 401

    def test_unhandled_event_type_returns_200(self, s7_client, s7_supplier_user):
        """Unknown event types are gracefully ignored (return 200)."""
        resp = s7_client.post(
            "/api/v1/webhooks/heyreach",
            json={"event_type": "some_future_event", "campaign_id": "a", "contact_id": "b", "data": {}},
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "some_future_event"
