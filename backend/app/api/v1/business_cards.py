"""Business card OCR API — Sprint 12 (Task 12.3).

Endpoints:
  POST   /business-cards/scan                  upload image + OCR via Claude Vision
  GET    /business-cards                        list scanned cards for supplier
  GET    /business-cards/{id}                   get single card
  PATCH  /business-cards/{id}                   update card fields manually
  DELETE /business-cards/{id}                   delete card
  POST   /business-cards/{id}/convert-to-lead   create outbound_contact from card
"""

import base64
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models.business_card import BusinessCard
from app.models.exhibition import Exhibition
from app.models.outbound_contact import OutboundContact

router = APIRouter(prefix="/business-cards", tags=["business-cards"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Claude Vision OCR helper
# ─────────────────────────────────────────────────────────────────────────────


async def _ocr_via_claude(image_bytes: bytes, mime_type: str) -> dict:
    """Use Claude Vision to extract structured contact info from a business card image.

    Returns a dict with keys: full_name, company_name, job_title, email, phone,
    website, address, country, linkedin_url, confidence (0.0-1.0).
    Falls back to empty fields (confidence=0.0) when Anthropic key is not configured.
    """
    try:
        import anthropic  # type: ignore

        from app.config import settings
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Extract all contact information from this business card image. "
                                "Return ONLY a valid JSON object with these fields (use null for missing): "
                                "full_name, company_name, job_title, email, phone, website, address, "
                                "country, linkedin_url. "
                                "Also include a confidence field (0.0 to 1.0) indicating how clearly "
                                "the card text was readable. "
                                "Return only the JSON, no other text."
                            ),
                        },
                    ],
                }
            ],
        )

        import json
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        return {
            "full_name": parsed.get("full_name"),
            "company_name": parsed.get("company_name"),
            "job_title": parsed.get("job_title"),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "website": parsed.get("website"),
            "address": parsed.get("address"),
            "country": parsed.get("country"),
            "linkedin_url": parsed.get("linkedin_url"),
            "confidence": float(parsed.get("confidence", 0.85)),
        }
    except Exception as exc:
        logger.warning("Claude Vision OCR failed: %s — returning stub result", exc)
        return {
            "full_name": None,
            "company_name": None,
            "job_title": None,
            "email": None,
            "phone": None,
            "website": None,
            "address": None,
            "country": None,
            "linkedin_url": None,
            "confidence": 0.0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────


class BusinessCardUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _supplier_id(user: User) -> int:
    sid = getattr(user, "supplier_profile_id", None) or getattr(user, "id", None)
    if not sid:
        raise HTTPException(status_code=403, detail="Supplier profile required")
    return int(sid)


def _card_to_dict(c: BusinessCard) -> dict:
    return {
        "id": c.id,
        "supplier_id": c.supplier_id,
        "exhibition_id": c.exhibition_id,
        "image_url": c.image_url,
        "full_name": c.full_name,
        "company_name": c.company_name,
        "job_title": c.job_title,
        "email": c.email,
        "phone": c.phone,
        "website": c.website,
        "address": c.address,
        "country": c.country,
        "linkedin_url": c.linkedin_url,
        "ocr_status": c.ocr_status,
        "ocr_confidence": c.ocr_confidence,
        "converted_to_contact": c.converted_to_contact,
        "contact_id": c.contact_id,
        "follow_up_sent": c.follow_up_sent,
        "notes": c.notes,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/scan", status_code=status.HTTP_201_CREATED)
async def scan_business_card(
    image: UploadFile = File(..., description="Business card image (JPEG/PNG/WEBP)"),
    exhibition_id: Optional[int] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a business card photo and extract contact info via Claude Vision OCR.

    - Accepts JPEG, PNG, WEBP images (max 10 MB)
    - Runs Claude Vision OCR synchronously
    - Returns structured contact data with confidence score
    """
    supplier_id = _supplier_id(current_user)

    # Validate mime type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{image.content_type}'. Accepted: {', '.join(allowed_types)}",
        )

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")

    if exhibition_id is not None:
        ex_result = await db.execute(
            select(Exhibition).where(
                Exhibition.id == exhibition_id,
                Exhibition.supplier_id == supplier_id,
            )
        )
        if not ex_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Exhibition not found")

    # Create a pending record first
    card = BusinessCard(
        supplier_id=supplier_id,
        exhibition_id=exhibition_id,
        image_url=None,  # Will be set after S3 upload in production
        ocr_status="processing",
        raw_ocr_text=None,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    # Run OCR
    ocr_result = await _ocr_via_claude(image_bytes, image.content_type)

    # Update card with OCR results
    for field in ("full_name", "company_name", "job_title", "email", "phone",
                  "website", "address", "country", "linkedin_url"):
        setattr(card, field, ocr_result.get(field))

    card.ocr_confidence = ocr_result.get("confidence", 0.0)
    card.ocr_status = "completed" if ocr_result["confidence"] > 0.0 else "failed"
    card.updated_at = datetime.now(tz=timezone.utc)

    # Increment exhibition contacts_count
    if exhibition_id:
        ex_result = await db.execute(
            select(Exhibition).where(
                Exhibition.id == exhibition_id,
                Exhibition.supplier_id == supplier_id,
            )
        )
        if ex := ex_result.scalar_one_or_none():
            ex.contacts_count = (ex.contacts_count or 0) + 1

    await db.commit()
    await db.refresh(card)
    logger.info(
        "Business card %d scanned for supplier %d (confidence=%.2f)",
        card.id, supplier_id, card.ocr_confidence or 0,
    )
    return _card_to_dict(card)


@router.get("")
async def list_business_cards(
    exhibition_id: Optional[int] = Query(default=None),
    ocr_status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List scanned business cards for the current supplier."""
    supplier_id = _supplier_id(current_user)
    q = select(BusinessCard).where(BusinessCard.supplier_id == supplier_id)
    if exhibition_id is not None:
        q = q.where(BusinessCard.exhibition_id == exhibition_id)
    if ocr_status is not None:
        q = q.where(BusinessCard.ocr_status == ocr_status)
    q = q.order_by(BusinessCard.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return [_card_to_dict(c) for c in result.scalars().all()]


@router.get("/{card_id}")
async def get_business_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single business card by ID."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(BusinessCard).where(
            BusinessCard.id == card_id,
            BusinessCard.supplier_id == supplier_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Business card not found")
    return _card_to_dict(card)


@router.patch("/{card_id}")
async def update_business_card(
    card_id: int,
    body: BusinessCardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually correct OCR parsed fields on a business card."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(BusinessCard).where(
            BusinessCard.id == card_id,
            BusinessCard.supplier_id == supplier_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Business card not found")

    for field in ("full_name", "company_name", "job_title", "email", "phone",
                  "website", "address", "country", "linkedin_url", "notes"):
        value = getattr(body, field, None)
        if value is not None:
            setattr(card, field, value)

    card.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(card)
    return _card_to_dict(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a business card record."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(BusinessCard).where(
            BusinessCard.id == card_id,
            BusinessCard.supplier_id == supplier_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Business card not found")

    if card.exhibition_id is not None:
        ex_result = await db.execute(
            select(Exhibition).where(
                Exhibition.id == card.exhibition_id,
                Exhibition.supplier_id == supplier_id,
            )
        )
        if ex := ex_result.scalar_one_or_none():
            ex.contacts_count = max(0, (ex.contacts_count or 0) - 1)

    await db.delete(card)
    await db.commit()


@router.post("/{card_id}/convert-to-lead", status_code=status.HTTP_201_CREATED)
async def convert_card_to_lead(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Convert a scanned business card into an OutboundContact (CRM lead).

    Creates an OutboundContact record populated from the card's OCR fields.
    Marks the card as converted.
    """
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(BusinessCard).where(
            BusinessCard.id == card_id,
            BusinessCard.supplier_id == supplier_id,
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Business card not found")
    if card.converted_to_contact:
        raise HTTPException(status_code=400, detail="Business card already converted to a contact")
    if not card.email:
        raise HTTPException(status_code=400, detail="Email address required to convert to contact")

    existing_result = await db.execute(
        select(OutboundContact).where(
            OutboundContact.supplier_id == supplier_id,
            OutboundContact.email == card.email,
        )
    )
    existing_contact = existing_result.scalar_one_or_none()
    if existing_contact:
        card.converted_to_contact = True
        card.contact_id = existing_contact.id
        card.updated_at = datetime.now(tz=timezone.utc)
        await db.commit()
        return {
            "contact_id": existing_contact.id,
            "email": existing_contact.email,
            "full_name": existing_contact.full_name,
            "company_name": existing_contact.company_name,
            "message": "Existing outbound contact linked to business card",
        }

    contact = OutboundContact(
        supplier_id=supplier_id,
        campaign_id=0,           # 0 = sourced from business card (no campaign)
        full_name=card.full_name or "",
        company_name=card.company_name or "",
        email=card.email,
        phone=card.phone,
        job_title=card.job_title,
        company_country=card.country,
        linkedin_url=card.linkedin_url,
        status="pending",
    )
    db.add(contact)
    await db.flush()  # Get contact.id

    card.converted_to_contact = True
    card.contact_id = contact.id
    card.updated_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(contact)
    logger.info(
        "Business card %d converted to contact %d (supplier %d)",
        card_id, contact.id, supplier_id,
    )
    return {
        "contact_id": contact.id,
        "email": contact.email,
        "full_name": contact.full_name,
        "company_name": contact.company_name,
        "message": "Business card successfully converted to outbound contact",
    }
