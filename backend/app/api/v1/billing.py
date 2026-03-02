"""Billing & Subscription API — Sprint 11 (11.1–11.2)

Endpoints:
  GET    /billing/plans                        — list all plans
  GET    /billing/subscription                 — current supplier subscription
  GET    /billing/invoices                     — billing history
  POST   /billing/checkout                     — create Stripe Checkout Session
  POST   /billing/portal                       — create Stripe Customer Portal session
  PATCH  /billing/plan                         — change plan (upgrade/downgrade)
  DELETE /billing/subscription                 — cancel subscription
  POST   /billing/webhook                      — Stripe webhook (no auth)
  GET    /billing/features                     — feature gate status for current supplier
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_supplier
from app.models import User, Supplier
from app.services import stripe_service
from app.services.feature_gate import FeatureGate

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_supplier_for_user(db: AsyncSession, user: User) -> Supplier:
    result = await db.execute(select(Supplier).where(Supplier.user_id == user.id))
    supplier = result.scalars().first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier profile not found")
    return supplier


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CheckoutRequest(BaseModel):
    plan_tier: str
    success_url: str = "http://localhost:3001/billing?success=1"
    cancel_url: str = "http://localhost:3001/billing?canceled=1"


class ChangePlanRequest(BaseModel):
    plan_tier: str


# ---------------------------------------------------------------------------
# Endpoints — no auth required for plans listing
# ---------------------------------------------------------------------------

@router.get("/plans")
async def list_plans() -> dict:
    """Return all available subscription plans with features and pricing."""
    return {"plans": stripe_service.get_all_plans()}


# ---------------------------------------------------------------------------
# Endpoints — supplier auth required
# ---------------------------------------------------------------------------

@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the current supplier's subscription details."""
    supplier = await _get_supplier_for_user(db, current_user)
    return await stripe_service.get_subscription(db, supplier.id, current_user.id)


@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return billing invoice history (last 12)."""
    supplier = await _get_supplier_for_user(db, current_user)
    invoices = await stripe_service.list_invoices(supplier.id, db)
    return {"invoices": invoices}


@router.post("/checkout", status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a Stripe Checkout Session to start or change a subscription."""
    supplier = await _get_supplier_for_user(db, current_user)
    try:
        result = await stripe_service.create_checkout_session(
            db=db,
            supplier_id=supplier.id,
            user_id=current_user.id,
            plan_tier=body.plan_tier,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result


@router.post("/portal")
async def create_portal_session(
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a Stripe Customer Portal session for self-serve billing management."""
    supplier = await _get_supplier_for_user(db, current_user)
    return await stripe_service.create_portal_session(db, supplier.id, current_user.id)


@router.patch("/plan")
async def change_plan(
    body: ChangePlanRequest,
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upgrade or downgrade subscription plan."""
    supplier = await _get_supplier_for_user(db, current_user)
    try:
        return await stripe_service.change_plan(db, supplier.id, current_user.id, body.plan_tier)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel subscription (takes effect at end of billing period)."""
    supplier = await _get_supplier_for_user(db, current_user)
    return await stripe_service.cancel_subscription(db, supplier.id, current_user.id)


@router.get("/features")
async def get_features(
    current_user: User = Depends(get_current_supplier),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return feature gate status for the current supplier's plan."""
    supplier = await _get_supplier_for_user(db, current_user)
    gate = FeatureGate(getattr(supplier, "subscription_tier", "free"))
    return gate.to_dict()


# ---------------------------------------------------------------------------
# Stripe webhook — NO auth (signature verification instead)
# ---------------------------------------------------------------------------

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        return await stripe_service.handle_webhook(db, payload, sig_header)
    except Exception as exc:
        logger.error("Stripe webhook error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook error")
