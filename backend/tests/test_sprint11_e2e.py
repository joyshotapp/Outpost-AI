"""Sprint 11 E2E / Unit Tests: Billing, Feature Gate, Admin KPIs

Tests:
  TestConfig               — Stripe config settings
  TestFeatureGate          — Feature gate per tier
  TestStripeServiceStub    — Stripe service in stub mode
  TestBillingAPISchemas    — Billing endpoint schemas
  TestBillingEndpoints     — Billing endpoint HTTP behaviour
  TestAdminKPIEndpoint     — /admin/kpi/overview
  TestAdminSupplierMgmt    — /admin/suppliers
  TestAdminBuyerMgmt       — /admin/buyers
  TestAdminContentReview   — /admin/content/review-queue
  TestAdminOutboundHealth  — /admin/outbound/health
  TestAdminAPIUsage        — /admin/api-usage/summary
  TestAdminSettings        — /admin/settings
  TestSubscriptionModel    — Subscription ORM model
"""

from __future__ import annotations

import importlib
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


def _make_supplier(sid: int = 10, tier: str = "free") -> MagicMock:
    s = MagicMock()
    s.id = sid
    s.company_name = "ACME Corp"
    s.company_slug = "acme-corp"
    s.country = "DE"
    s.industry = "Manufacturing"
    s.is_active = True
    s.is_verified = False
    s.subscription_tier = tier
    s.created_at = datetime.now(timezone.utc)
    return s


def _make_buyer(bid: int = 20) -> MagicMock:
    b = MagicMock()
    b.id = bid
    b.company_name = "Global Buyer Ltd"
    b.country = "US"
    b.is_active = True
    b.created_at = datetime.now(timezone.utc)
    return b


# ============================================================
# TestConfig
# ============================================================

class TestConfig:
    def test_stripe_price_ids_exist(self):
        from app.config import settings
        assert hasattr(settings, "STRIPE_STARTER_PRICE_ID")
        assert hasattr(settings, "STRIPE_PROFESSIONAL_PRICE_ID")
        assert hasattr(settings, "STRIPE_ENTERPRISE_PRICE_ID")

    def test_stripe_prices_usd(self):
        from app.config import settings
        assert settings.STRIPE_STARTER_PRICE_USD == 49
        assert settings.STRIPE_PROFESSIONAL_PRICE_USD == 149
        assert settings.STRIPE_ENTERPRISE_PRICE_USD == 499

    def test_stripe_trial_days(self):
        from app.config import settings
        assert settings.STRIPE_TRIAL_DAYS >= 0

    def test_stripe_portal_url(self):
        from app.config import settings
        assert "billing" in settings.STRIPE_PORTAL_RETURN_URL


# ============================================================
# TestFeatureGate
# ============================================================

class TestFeatureGate:
    def test_free_tier_basic_features(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("free")
        assert gate.can("profile_listing")
        assert gate.can("rfq_inbox")

    def test_free_tier_no_outbound(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("free")
        assert not gate.can("outbound_unlimited")
        assert not gate.can("ai_avatar")

    def test_starter_unlocks_rfq_ai(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("starter")
        assert gate.can("rfq_ai_parse")
        assert gate.can("outbound_basic")
        assert not gate.can("ai_avatar")

    def test_professional_unlocks_avatar(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("professional")
        assert gate.can("ai_avatar")
        assert gate.can("visitor_intent")
        assert gate.can("outbound_unlimited")

    def test_enterprise_all_features(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("enterprise")
        assert gate.can("multilingual_unlimited")
        assert gate.can("sla_guarantee")

    def test_require_raises_403_for_insufficient_tier(self):
        from fastapi import HTTPException
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("free")
        with pytest.raises(HTTPException) as exc:
            gate.require("ai_avatar")
        assert exc.value.status_code == 403

    def test_require_passes_on_sufficient_tier(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("enterprise")
        gate.require("ai_avatar")  # should not raise

    def test_available_features_list(self):
        from app.services.feature_gate import FeatureGate
        gate_free = FeatureGate("free")
        gate_pro = FeatureGate("professional")
        assert len(gate_pro.available_features()) > len(gate_free.available_features())

    def test_unknown_feature_denied(self):
        from app.services.feature_gate import FeatureGate
        gate = FeatureGate("enterprise")
        assert not gate.can("non_existent_feature_xyz")

    def test_to_dict_structure(self):
        from app.services.feature_gate import FeatureGate
        d = FeatureGate("starter").to_dict()
        assert "tier" in d
        assert "features" in d
        assert "limits" in d

    def test_limits_for_free_tier(self):
        from app.services.feature_gate import FeatureGate
        limits = FeatureGate("free").limits()
        assert limits["rfq_per_month"] == 5
        assert limits["outbound_contacts"] == 0


# ============================================================
# TestStripeServiceStub
# ============================================================

class TestStripeServiceStub:
    """All tests use stub mode (no real Stripe key)."""

    @pytest.mark.asyncio
    async def test_get_subscription_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True):
            result = await stripe_service.get_subscription(db, supplier_id=1, user_id=1)
        assert result["_stub"] is True
        assert "plan_tier" in result

    @pytest.mark.asyncio
    async def test_checkout_session_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True):
            result = await stripe_service.create_checkout_session(
                db, supplier_id=1, user_id=1, plan_tier="starter",
                success_url="http://localhost/success",
                cancel_url="http://localhost/cancel",
            )
        assert result["_stub"] is True
        assert "checkout_url" in result

    @pytest.mark.asyncio
    async def test_portal_session_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.stripe_customer_id = None
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_sub)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True):
            result = await stripe_service.create_portal_session(db, supplier_id=1, user_id=1)
        assert "portal_url" in result

    @pytest.mark.asyncio
    async def test_change_plan_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = None
        mock_sub.status = "active"
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_sub)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True), \
             patch.object(stripe_service, "_update_supplier_tier", new=AsyncMock()):
            result = await stripe_service.change_plan(db, 1, 1, "professional")
        assert result["plan_tier"] == "professional"

    @pytest.mark.asyncio
    async def test_cancel_subscription_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.stripe_subscription_id = None
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_sub)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True), \
             patch.object(stripe_service, "_update_supplier_tier", new=AsyncMock()):
            result = await stripe_service.cancel_subscription(db, 1, 1)
        assert result["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_invalid_plan_tier_raises(self):
        from app.services import stripe_service
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()

        with pytest.raises(ValueError):
            await stripe_service.create_checkout_session(
                db, 1, 1, "invalid_tier", "http://x", "http://x"
            )

    @pytest.mark.asyncio
    async def test_list_invoices_stub(self):
        from app.services import stripe_service
        db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.stripe_customer_id = None
        mock_sub.plan_tier = "starter"
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_sub)))))

        with patch.object(stripe_service, "_is_stub_mode", return_value=True):
            invoices = await stripe_service.list_invoices(1, db)
        assert isinstance(invoices, list)
        assert all("date" in inv for inv in invoices)

    def test_get_all_plans(self):
        from app.services.stripe_service import get_all_plans
        plans = get_all_plans()
        tiers = [p["tier"] for p in plans]
        assert "free" in tiers
        assert "starter" in tiers
        assert "professional" in tiers
        assert "enterprise" in tiers

    def test_webhook_stub(self):
        from app.services import stripe_service
        import asyncio
        db = AsyncMock()

        with patch.object(stripe_service, "_is_stub_mode", return_value=True):
            result = asyncio.get_event_loop().run_until_complete(
                stripe_service.handle_webhook(db, b"payload", "sig")
            )
        assert result["_stub"] is True


# ============================================================
# TestSubscriptionModel
# ============================================================

class TestSubscriptionModel:
    def test_subscription_model_imports(self):
        from app.models.subscription import Subscription, PlanTier, SubscriptionStatus
        assert Subscription.__tablename__ == "subscriptions"

    def test_plan_tier_enum(self):
        from app.models.subscription import PlanTier
        assert PlanTier.FREE == "free"
        assert PlanTier.ENTERPRISE == "enterprise"

    def test_subscription_status_enum(self):
        from app.models.subscription import SubscriptionStatus
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.PAST_DUE == "past_due"

    def test_api_usage_record_model(self):
        from app.models.api_usage_record import ApiUsageRecord
        assert ApiUsageRecord.__tablename__ == "api_usage_records"

    def test_system_setting_model(self):
        from app.models.system_setting import SystemSetting
        assert SystemSetting.__tablename__ == "system_settings"

    def test_models_init_exports(self):
        from app.models import Subscription, ApiUsageRecord, SystemSetting, PlanTier, SubscriptionStatus
        assert Subscription is not None


# ============================================================
# TestBillingEndpoints
# ============================================================

class TestBillingEndpoints:
    def _make_app(self):
        from fastapi import FastAPI
        from app.api.v1.billing import router
        app = FastAPI()
        app.include_router(router)
        return app

    def _client(self, app=None):
        from fastapi.testclient import TestClient
        return TestClient(app or self._make_app())

    def test_get_plans_200(self):
        app = self._make_app()

        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/billing/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data
        assert len(data["plans"]) == 4

    def test_get_subscription_requires_auth(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        resp = client.get("/billing/subscription")
        assert resp.status_code in (401, 403, 422)

    def test_get_features_requires_auth(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        resp = client.get("/billing/features")
        assert resp.status_code in (401, 403, 422)

    def test_checkout_requires_auth(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        resp = client.post("/billing/checkout", json={"plan_tier": "starter"})
        assert resp.status_code in (401, 403, 422)

    def test_cancel_requires_auth(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        resp = client.delete("/billing/subscription")
        assert resp.status_code in (401, 403, 422)

    def test_webhook_endpoint_exists(self):
        """Webhook should NOT 404 — it requires Stripe signature so will 400 without header."""
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app(), raise_server_exceptions=False)
        resp = client.post("/billing/webhook", content=b"payload")
        assert resp.status_code in (200, 400, 422)  # not 404

    def test_plans_contain_required_fields(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        data = client.get("/billing/plans").json()
        for plan in data["plans"]:
            assert "tier" in plan
            assert "name" in plan
            assert "price_usd" in plan
            assert "features" in plan

    def test_plans_free_is_zero_cost(self):
        from fastapi.testclient import TestClient
        client = TestClient(self._make_app())
        data = client.get("/billing/plans").json()
        free_plan = next((p for p in data["plans"] if p["tier"] == "free"), None)
        assert free_plan is not None
        assert free_plan["price_usd"] == 0


# ============================================================
# TestAdminKPIEndpoint
# ============================================================

class TestAdminKPIEndpoint:
    def _make_app_with_mocked_db(self):
        from fastapi import FastAPI
        from app.api.v1.admin import router
        from app.database import get_db

        app = FastAPI()
        app.include_router(router)
        return app

    def test_kpi_overview_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/kpi/overview")
        assert resp.status_code in (401, 403, 422)

    def test_admin_suppliers_list_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/suppliers")
        assert resp.status_code in (401, 403, 422)

    def test_admin_buyers_list_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/buyers")
        assert resp.status_code in (401, 403, 422)

    def test_admin_content_review_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/content/review-queue")
        assert resp.status_code in (401, 403, 422)

    def test_admin_outbound_health_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/outbound/health")
        assert resp.status_code in (401, 403, 422)

    def test_admin_api_usage_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/api-usage/summary")
        assert resp.status_code in (401, 403, 422)

    def test_admin_settings_requires_admin(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/admin/settings")
        assert resp.status_code in (401, 403, 422)


# ============================================================
# TestAdminSupplierMgmt (service-layer unit tests with mocked DB)
# ============================================================

class TestAdminSupplierMgmt:
    @pytest.mark.asyncio
    async def test_patch_supplier_verifies(self):
        """Ensure PATCH supplier sets is_verified correctly."""
        from app.api.v1 import admin as admin_module
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_supplier = _make_supplier()
        mock_supplier.is_verified = False

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_supplier)))
        ))
        db.commit = AsyncMock()

        from app.api.v1.admin import SupplierAdminUpdateRequest, admin_update_supplier
        body = SupplierAdminUpdateRequest(is_verified=True)
        admin_user = _make_user(role="admin")

        result = await admin_update_supplier(10, body, admin_user, db)
        assert result["is_verified"] is True

    @pytest.mark.asyncio
    async def test_patch_supplier_not_found(self):
        from fastapi import HTTPException
        from app.api.v1.admin import SupplierAdminUpdateRequest, admin_update_supplier
        from sqlalchemy.ext.asyncio import AsyncSession

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))

        body = SupplierAdminUpdateRequest(is_verified=True)
        admin_user = _make_user(role="admin")

        with pytest.raises(HTTPException) as exc:
            await admin_update_supplier(999, body, admin_user, db)
        assert exc.value.status_code == 404


# ============================================================
# TestAdminBuyerMgmt
# ============================================================

class TestAdminBuyerMgmt:
    @pytest.mark.asyncio
    async def test_block_buyer(self):
        from app.api.v1.admin import BuyerAdminUpdateRequest, admin_block_buyer
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_buyer = _make_buyer()
        mock_buyer.is_active = True

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_buyer)))
        ))
        db.commit = AsyncMock()

        body = BuyerAdminUpdateRequest(is_active=False)
        admin_user = _make_user(role="admin")

        result = await admin_block_buyer(20, body, admin_user, db)
        assert result["is_active"] is False

    @pytest.mark.asyncio
    async def test_block_buyer_not_found_404(self):
        from fastapi import HTTPException
        from app.api.v1.admin import BuyerAdminUpdateRequest, admin_block_buyer
        from sqlalchemy.ext.asyncio import AsyncSession

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))

        body = BuyerAdminUpdateRequest(is_active=False)
        with pytest.raises(HTTPException) as exc:
            await admin_block_buyer(999, body, _make_user("admin"), db)
        assert exc.value.status_code == 404


# ============================================================
# TestAdminContentReview
# ============================================================

class TestAdminContentReview:
    @pytest.mark.asyncio
    async def test_review_approve_content(self):
        from app.api.v1.admin import ContentReviewRequest, admin_review_content
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_item = MagicMock()
        mock_item.id = 5
        mock_item.review_status = "pending"

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_item)))
        ))
        db.commit = AsyncMock()

        body = ContentReviewRequest(review_status="approved", review_note="Looks good!")
        result = await admin_review_content(5, body, _make_user("admin"), db)
        assert result["review_status"] == "approved"

    @pytest.mark.asyncio
    async def test_review_invalid_status_400(self):
        from fastapi import HTTPException
        from app.api.v1.admin import ContentReviewRequest, admin_review_content
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_item = MagicMock()
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_item)))
        ))

        body = ContentReviewRequest(review_status="invalid_status")
        with pytest.raises(HTTPException) as exc:
            await admin_review_content(5, body, _make_user("admin"), db)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_review_content_not_found(self):
        from fastapi import HTTPException
        from app.api.v1.admin import ContentReviewRequest, admin_review_content
        from sqlalchemy.ext.asyncio import AsyncSession

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))

        body = ContentReviewRequest(review_status="approved")
        with pytest.raises(HTTPException) as exc:
            await admin_review_content(999, body, _make_user("admin"), db)
        assert exc.value.status_code == 404


# ============================================================
# TestAdminSettings
# ============================================================

class TestAdminSettings:
    @pytest.mark.asyncio
    async def test_upsert_new_setting(self):
        from app.api.v1.admin import SystemSettingUpsertRequest, admin_upsert_setting
        from app.models.system_setting import SystemSetting
        from sqlalchemy.ext.asyncio import AsyncSession

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))
        db.add = MagicMock()
        db.commit = AsyncMock()

        body = SystemSettingUpsertRequest(key="test.key", value="test_value")
        result = await admin_upsert_setting(body, _make_user("admin"), db)

        db.add.assert_called_once()
        created_setting = db.add.call_args.args[0]
        assert isinstance(created_setting, SystemSetting)
        assert result["key"] == "test.key"
        assert result["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_delete_setting_not_found(self):
        from fastapi import HTTPException
        from app.api.v1.admin import admin_delete_setting
        from sqlalchemy.ext.asyncio import AsyncSession

        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))

        with pytest.raises(HTTPException) as exc:
            await admin_delete_setting("nonexistent.key", _make_user("admin"), db)
        assert exc.value.status_code == 404
