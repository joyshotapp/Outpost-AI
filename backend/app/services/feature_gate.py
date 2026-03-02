"""Feature Gate — Sprint 11 (11.2)

Determines which features are available to a supplier based on their subscription tier.
Usage:
    gate = FeatureGate(supplier.subscription_tier)
    if gate.can("outbound"):
        ...
    gate.require("ai_avatar")  # raises HTTP 403 if not allowed
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from fastapi import HTTPException, status

from app.models.subscription import PlanTier

# ---------------------------------------------------------------------------
# Feature definitions per tier
# Each feature maps to the *minimum* tier required.
# ---------------------------------------------------------------------------
_FEATURE_TIER_FLOOR: dict[str, str] = {
    # ── Free tier ──
    "profile_listing": PlanTier.FREE,
    "rfq_inbox": PlanTier.FREE,          # limited by rfq_per_month limit
    "basic_analytics": PlanTier.FREE,

    # ── Starter ──
    "rfq_unlimited": PlanTier.STARTER,
    "rfq_ai_parse": PlanTier.STARTER,    # AI RFQ parsing & grading
    "multilingual_3": PlanTier.STARTER,  # up to 3 languages
    "outbound_basic": PlanTier.STARTER,  # limited outbound contacts
    "ai_content_basic": PlanTier.STARTER,  # limited AI content

    # ── Professional ──
    "ai_avatar": PlanTier.PROFESSIONAL,           # AI Digital Sales Rep
    "multilingual_5": PlanTier.PROFESSIONAL,      # up to 5 languages
    "outbound_unlimited": PlanTier.PROFESSIONAL,  # LinkedIn + Email unlimited
    "visitor_intent": PlanTier.PROFESSIONAL,      # visitor analytics
    "content_repurpose": PlanTier.PROFESSIONAL,   # OpusClip / Repurpose.io
    "ai_content_unlimited_100": PlanTier.PROFESSIONAL,

    # ── Enterprise ──
    "multilingual_unlimited": PlanTier.ENTERPRISE,
    "ai_content_unlimited": PlanTier.ENTERPRISE,
    "custom_integrations": PlanTier.ENTERPRISE,
    "sla_guarantee": PlanTier.ENTERPRISE,
}

_TIER_ORDER: list[str] = [
    PlanTier.FREE,
    PlanTier.STARTER,
    PlanTier.PROFESSIONAL,
    PlanTier.ENTERPRISE,
]


def _tier_rank(tier: str) -> int:
    try:
        return _TIER_ORDER.index(tier)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# FeatureGate class
# ---------------------------------------------------------------------------

class FeatureGate:
    """Evaluate feature access for a given supplier tier."""

    def __init__(self, tier: str = PlanTier.FREE) -> None:
        self.tier = tier
        self._rank = _tier_rank(tier)

    def can(self, feature: str) -> bool:
        """Return True if the current tier allows *feature*."""
        required_tier = _FEATURE_TIER_FLOOR.get(feature)
        if required_tier is None:
            # Unknown feature — default to denied
            return False
        return self._rank >= _tier_rank(required_tier)

    def require(self, feature: str, detail: Optional[str] = None) -> None:
        """Raise HTTP 403 if the current tier does NOT allow *feature*."""
        if not self.can(feature):
            required_tier = _FEATURE_TIER_FLOOR.get(feature, "professional")
            msg = detail or (
                f"Feature '{feature}' requires {required_tier.title()} plan or higher. "
                f"Your current plan: {self.tier.title()}."
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    def available_features(self) -> list[str]:
        """Return list of all features available at the current tier."""
        return [f for f in _FEATURE_TIER_FLOOR if self.can(f)]

    def limits(self) -> dict:
        """Return numeric limits for the current tier."""
        from app.services.stripe_service import PLAN_DISPLAY
        return PLAN_DISPLAY.get(self.tier, PLAN_DISPLAY[PlanTier.FREE]).get("limits", {})

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "features": self.available_features(),
            "limits": self.limits(),
        }


# ---------------------------------------------------------------------------
# FastAPI dependency helper
# ---------------------------------------------------------------------------

async def get_feature_gate(supplier_tier: str = PlanTier.FREE) -> FeatureGate:
    """Dependency helper — pass supplier.subscription_tier."""
    return FeatureGate(supplier_tier)
