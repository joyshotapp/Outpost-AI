"""Stripe subscription service — Sprint 11

Handles subscription lifecycle: create → upgrade/downgrade → cancel → webhook processing.
Operates in stub mode when STRIPE_SECRET_KEY is not configured.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.subscription import Subscription, PlanTier, SubscriptionStatus
from app.models.supplier import Supplier

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plan → Price ID mapping
# ---------------------------------------------------------------------------
PLAN_PRICE_MAP: dict[str, str] = {
    PlanTier.STARTER: settings.STRIPE_STARTER_PRICE_ID,
    PlanTier.PROFESSIONAL: settings.STRIPE_PROFESSIONAL_PRICE_ID,
    PlanTier.ENTERPRISE: settings.STRIPE_ENTERPRISE_PRICE_ID,
}

PRICE_PLAN_MAP: dict[str, str] = {v: k for k, v in PLAN_PRICE_MAP.items()}

PLAN_DISPLAY: dict[str, dict] = {
    PlanTier.FREE: {
        "name": "Free",
        "price_usd": 0,
        "features": [
            "Company profile listing",
            "Up to 3 product categories",
            "Basic RFQ inbox (5/month)",
            "1 language",
        ],
        "limits": {"rfq_per_month": 5, "languages": 1, "outbound_contacts": 0, "ai_content_pieces": 0},
    },
    PlanTier.STARTER: {
        "name": "Starter",
        "price_usd": settings.STRIPE_STARTER_PRICE_USD,
        "features": [
            "Everything in Free",
            "Unlimited RFQs",
            "AI RFQ parsing & grading",
            "3 languages",
            "50 Outbound contacts/month",
            "10 AI content pieces/month",
        ],
        "limits": {"rfq_per_month": -1, "languages": 3, "outbound_contacts": 50, "ai_content_pieces": 10},
    },
    PlanTier.PROFESSIONAL: {
        "name": "Professional",
        "price_usd": settings.STRIPE_PROFESSIONAL_PRICE_USD,
        "features": [
            "Everything in Starter",
            "AI Digital Sales Rep (avatar)",
            "5 languages",
            "LinkedIn + Email Outbound (unlimited)",
            "100 AI content pieces/month",
            "Visitor intent analytics",
            "Content repurposing",
        ],
        "limits": {"rfq_per_month": -1, "languages": 5, "outbound_contacts": -1, "ai_content_pieces": 100},
    },
    PlanTier.ENTERPRISE: {
        "name": "Enterprise",
        "price_usd": settings.STRIPE_ENTERPRISE_PRICE_USD,
        "features": [
            "Everything in Professional",
            "All languages",
            "Unlimited AI content",
            "White-glove onboarding",
            "Dedicated account manager",
            "Custom integrations",
            "SLA 99.9% uptime",
        ],
        "limits": {"rfq_per_month": -1, "languages": -1, "outbound_contacts": -1, "ai_content_pieces": -1},
    },
}


# ---------------------------------------------------------------------------
# Stripe client initialisation (graceful stub mode)
# ---------------------------------------------------------------------------
_stripe = None


def _get_stripe():
    global _stripe
    if _stripe is None and settings.STRIPE_SECRET_KEY:
        try:
            import stripe as _stripe_lib
            _stripe_lib.api_key = settings.STRIPE_SECRET_KEY
            _stripe = _stripe_lib
            logger.info("Stripe client initialised")
        except ImportError:
            logger.warning("stripe package not installed — running in stub mode")
    return _stripe


def _is_stub_mode() -> bool:
    return _get_stripe() is None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_or_create_subscription(db: AsyncSession, supplier_id: int, user_id: int) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.supplier_id == supplier_id))
    sub = result.scalars().first()
    if sub is None:
        sub = Subscription(
            supplier_id=supplier_id,
            user_id=user_id,
            plan_tier=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(sub)
        await db.flush()
    return sub


async def _update_supplier_tier(db: AsyncSession, supplier_id: int, tier: str) -> None:
    await db.execute(
        update(Supplier).where(Supplier.id == supplier_id).values(subscription_tier=tier)
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_subscription(db: AsyncSession, supplier_id: int, user_id: int) -> dict:
    """Return current subscription info (stub-safe)."""
    sub = await _get_or_create_subscription(db, supplier_id, user_id)
    await db.commit()
    plan_info = PLAN_DISPLAY.get(sub.plan_tier, PLAN_DISPLAY[PlanTier.FREE])
    return {
        "subscription_id": sub.id,
        "plan_tier": sub.plan_tier,
        "status": sub.status,
        "stripe_subscription_id": sub.stripe_subscription_id,
        "stripe_customer_id": sub.stripe_customer_id,
        "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
        "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "canceled_at": sub.canceled_at.isoformat() if sub.canceled_at else None,
        "plan": plan_info,
        "_stub": _is_stub_mode(),
    }


async def create_checkout_session(
    db: AsyncSession,
    supplier_id: int,
    user_id: int,
    plan_tier: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Create a Stripe Checkout Session for a new subscription (or stub URL)."""
    if plan_tier not in PLAN_PRICE_MAP:
        raise ValueError(f"Invalid plan tier: {plan_tier}. Must be one of {list(PLAN_PRICE_MAP)}")

    sub = await _get_or_create_subscription(db, supplier_id, user_id)

    if _is_stub_mode():
        logger.info("[STUB] Stripe checkout session created for supplier=%s plan=%s", supplier_id, plan_tier)
        return {
            "checkout_url": f"https://checkout.stripe.com/stub?plan={plan_tier}",
            "session_id": f"stub_cs_{supplier_id}_{plan_tier}",
            "_stub": True,
        }

    stripe = _get_stripe()
    price_id = PLAN_PRICE_MAP[plan_tier]

    # Ensure Stripe customer exists
    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(metadata={"supplier_id": str(supplier_id), "user_id": str(user_id)})
        sub.stripe_customer_id = customer["id"]
        await db.flush()

    session_kwargs: dict = {
        "customer": sub.stripe_customer_id,
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {"supplier_id": str(supplier_id), "plan_tier": plan_tier},
    }
    if settings.STRIPE_TRIAL_DAYS > 0:
        session_kwargs["subscription_data"] = {"trial_period_days": settings.STRIPE_TRIAL_DAYS}

    session = stripe.checkout.Session.create(**session_kwargs)
    await db.commit()
    return {"checkout_url": session["url"], "session_id": session["id"], "_stub": False}


async def create_portal_session(db: AsyncSession, supplier_id: int, user_id: int) -> dict:
    """Return Stripe Customer Portal URL (or stub URL)."""
    sub = await _get_or_create_subscription(db, supplier_id, user_id)

    if _is_stub_mode() or not sub.stripe_customer_id:
        return {
            "portal_url": f"{settings.STRIPE_PORTAL_RETURN_URL}?stub=1",
            "_stub": True,
        }

    stripe = _get_stripe()
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=settings.STRIPE_PORTAL_RETURN_URL,
    )
    return {"portal_url": session["url"], "_stub": False}


async def change_plan(
    db: AsyncSession,
    supplier_id: int,
    user_id: int,
    new_tier: str,
) -> dict:
    """Upgrade or downgrade via Stripe subscription items update (or stub)."""
    if new_tier not in PLAN_PRICE_MAP:
        raise ValueError(f"Invalid plan tier: {new_tier}")

    sub = await _get_or_create_subscription(db, supplier_id, user_id)

    if _is_stub_mode() or not sub.stripe_subscription_id:
        sub.plan_tier = new_tier
        await _update_supplier_tier(db, supplier_id, new_tier)
        await db.commit()
        logger.info("[STUB] Plan changed supplier=%s new_tier=%s", supplier_id, new_tier)
        return {"plan_tier": new_tier, "status": sub.status, "_stub": _is_stub_mode()}

    stripe = _get_stripe()
    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    item_id = stripe_sub["items"]["data"][0]["id"]
    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        items=[{"id": item_id, "price": PLAN_PRICE_MAP[new_tier]}],
        proration_behavior="always_invoice",
    )
    sub.plan_tier = new_tier
    sub.stripe_price_id = PLAN_PRICE_MAP[new_tier]
    await _update_supplier_tier(db, supplier_id, new_tier)
    await db.commit()
    return {"plan_tier": new_tier, "status": sub.status, "_stub": False}


async def cancel_subscription(db: AsyncSession, supplier_id: int, user_id: int) -> dict:
    """Cancel at period end (or stub)."""
    sub = await _get_or_create_subscription(db, supplier_id, user_id)

    if _is_stub_mode() or not sub.stripe_subscription_id:
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = datetime.now(timezone.utc)
        sub.plan_tier = PlanTier.FREE
        await _update_supplier_tier(db, supplier_id, PlanTier.FREE)
        await db.commit()
        logger.info("[STUB] Subscription cancelled supplier=%s", supplier_id)
        return {"status": SubscriptionStatus.CANCELED, "_stub": _is_stub_mode()}

    stripe = _get_stripe()
    stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
    sub.status = SubscriptionStatus.CANCELED
    sub.canceled_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": SubscriptionStatus.CANCELED, "_stub": False}


async def handle_webhook(db: AsyncSession, payload: bytes, sig_header: str) -> dict:
    """Process Stripe webhook events."""
    if _is_stub_mode():
        return {"received": True, "_stub": True}

    stripe = _get_stripe()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        logger.error("Stripe webhook signature verification failed: %s", exc)
        raise

    event_type = event["type"]
    data_obj = event["data"]["object"]
    logger.info("Stripe webhook: %s", event_type)

    if event_type in ("customer.subscription.updated", "customer.subscription.created"):
        await _sync_subscription_from_stripe(db, data_obj)

    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data_obj["id"]
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalars().first()
        if sub:
            sub.status = SubscriptionStatus.CANCELED
            sub.plan_tier = PlanTier.FREE
            sub.canceled_at = datetime.now(timezone.utc)
            await _update_supplier_tier(db, sub.supplier_id, PlanTier.FREE)
            await db.commit()

    elif event_type == "invoice.paid":
        # Subscription is healthy
        stripe_sub_id = data_obj.get("subscription")
        if stripe_sub_id:
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
            )
            sub = result.scalars().first()
            if sub and sub.status == SubscriptionStatus.PAST_DUE:
                sub.status = SubscriptionStatus.ACTIVE
                await db.commit()

    elif event_type == "invoice.payment_failed":
        stripe_sub_id = data_obj.get("subscription")
        if stripe_sub_id:
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
            )
            sub = result.scalars().first()
            if sub:
                sub.status = SubscriptionStatus.PAST_DUE
                await db.commit()

    return {"received": True, "event_type": event_type}


async def _sync_subscription_from_stripe(db: AsyncSession, stripe_sub: dict) -> None:
    """Sync our DB subscription record from a Stripe subscription object."""
    stripe_sub_id = stripe_sub["id"]
    stripe_customer_id = stripe_sub["customer"]
    price_id = stripe_sub["items"]["data"][0]["price"]["id"]
    plan_tier = PRICE_PLAN_MAP.get(price_id, PlanTier.STARTER)
    status = stripe_sub["status"]

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalars().first()

    if sub is None:
        # Try matching by customer ID
        result2 = await db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
        )
        sub = result2.scalars().first()

    if sub:
        sub.stripe_subscription_id = stripe_sub_id
        sub.stripe_price_id = price_id
        sub.plan_tier = plan_tier
        sub.status = status
        period_start = stripe_sub.get("current_period_start")
        period_end = stripe_sub.get("current_period_end")
        trial_end = stripe_sub.get("trial_end")
        if period_start:
            sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
        if period_end:
            sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
        if trial_end:
            sub.trial_end = datetime.fromtimestamp(trial_end, tz=timezone.utc)
        await _update_supplier_tier(db, sub.supplier_id, plan_tier)
        await db.commit()


async def list_invoices(supplier_id: int, db: AsyncSession) -> list[dict]:
    """Return last 12 invoices from Stripe (or stub list)."""
    result = await db.execute(
        select(Subscription).where(Subscription.supplier_id == supplier_id)
    )
    sub = result.scalars().first()

    if _is_stub_mode() or not sub or not sub.stripe_customer_id:
        return [
            {
                "id": f"stub_inv_{i}",
                "date": f"2026-{3 - i:02d}-01",
                "amount_usd": PLAN_DISPLAY.get(sub.plan_tier if sub else PlanTier.FREE, {}).get("price_usd", 0),
                "status": "paid",
                "pdf_url": None,
                "_stub": True,
            }
            for i in range(3)
        ]

    stripe = _get_stripe()
    invoices = stripe.Invoice.list(customer=sub.stripe_customer_id, limit=12)
    return [
        {
            "id": inv["id"],
            "date": datetime.fromtimestamp(inv["created"], tz=timezone.utc).date().isoformat(),
            "amount_usd": inv["amount_paid"] / 100,
            "status": inv["status"],
            "pdf_url": inv.get("invoice_pdf"),
            "_stub": False,
        }
        for inv in invoices.get("data", [])
    ]


def get_all_plans() -> list[dict]:
    """Return display info for all plans."""
    return [
        {"tier": tier, **info}
        for tier, info in PLAN_DISPLAY.items()
    ]
