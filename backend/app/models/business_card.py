"""Business card model — Sprint 12 (Task 12.3).

Stores results from Claude Vision OCR of physical business cards
captured at trade shows or in-person meetings.
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.models.base import BaseModel


class BusinessCard(BaseModel):
    """Scanned business card with Claude Vision OCR parsed fields."""

    __tablename__ = "business_cards"

    supplier_id = Column(Integer, nullable=False, index=True)
    exhibition_id = Column(Integer, nullable=True, index=True)   # FK to exhibitions

    # ── Source image ──────────────────────────────────────────────────────
    image_url = Column(String(500), nullable=True)
    raw_ocr_text = Column(Text, nullable=True)

    # ── Parsed contact info ───────────────────────────────────────────────
    full_name = Column(String(200), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_title = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # ── OCR processing ────────────────────────────────────────────────────
    # pending | processing | completed | failed
    ocr_status = Column(String(30), nullable=False, default="pending")
    ocr_confidence = Column(Float, nullable=True)   # 0.0 – 1.0

    # ── CRM conversion ────────────────────────────────────────────────────
    converted_to_contact = Column(Boolean, nullable=False, default=False)
    contact_id = Column(Integer, nullable=True)   # outbound_contacts.id if converted

    # ── Follow-up ─────────────────────────────────────────────────────────
    follow_up_sent = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
