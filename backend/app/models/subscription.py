"""Subscription model — Sprint 11"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PlanTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class Subscription(BaseModel):
    """Supplier subscription record — one per supplier"""

    __tablename__ = "subscriptions"

    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Plan
    plan_tier = Column(String(30), nullable=False, default=PlanTier.FREE)

    # Stripe
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Status
    status = Column(String(30), nullable=False, default=SubscriptionStatus.ACTIVE)

    # Periods
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Subscription supplier={self.supplier_id} tier={self.plan_tier} status={self.status}>"
