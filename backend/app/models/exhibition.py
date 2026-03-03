"""Exhibition event model — Sprint 12 (Task 12.2).

Manages the full lifecycle of trade show / exhibition participation:
  planning → active (during show) → post_show → completed
"""

from sqlalchemy import Boolean, Column, Date, Integer, String, Text

from app.models.base import BaseModel


class Exhibition(BaseModel):
    """Trade show / exhibition event managed by a supplier."""

    __tablename__ = "exhibitions"

    supplier_id = Column(Integer, nullable=False, index=True)

    # ── Event details ─────────────────────────────────────────────────────
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    booth_number = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────
    # planning | active | post_show | completed
    status = Column(String(30), nullable=False, default="planning")

    # ── Pre-show ICP criteria (JSON string) ───────────────────────────────
    icp_criteria = Column(Text, nullable=True)

    # ── Counters ─────────────────────────────────────────────────────────
    contacts_count = Column(Integer, nullable=False, default=0)

    # ── Notes ─────────────────────────────────────────────────────────────
    notes = Column(Text, nullable=True)
