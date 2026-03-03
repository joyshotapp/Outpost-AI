"""Exhibition event management API — Sprint 12 (Task 12.2).

Endpoints:
  POST   /exhibitions                           create exhibition
  GET    /exhibitions                           list exhibitions for supplier
  GET    /exhibitions/{id}                      get exhibition detail
  PATCH  /exhibitions/{id}                      update exhibition
  DELETE /exhibitions/{id}                      delete exhibition
  PATCH  /exhibitions/{id}/status               advance lifecycle status
  GET    /exhibitions/{id}/contacts             list business cards for exhibition
"""

import json
import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models.exhibition import Exhibition
from app.models.business_card import BusinessCard

router = APIRouter(prefix="/exhibitions", tags=["exhibitions"])
logger = logging.getLogger(__name__)

VALID_TRANSITIONS: dict[str, list[str]] = {
    "planning":   ["active"],
    "active":     ["post_show"],
    "post_show":  ["completed"],
    "completed":  [],
}


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────


class ExhibitionCreate(BaseModel):
    name: str
    location: Optional[str] = None
    booth_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    icp_criteria: Optional[dict] = None
    notes: Optional[str] = None


class ExhibitionUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    booth_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    icp_criteria: Optional[dict] = None
    notes: Optional[str] = None


class ExhibitionStatusUpdate(BaseModel):
    status: str


class ExhibitionResponse(BaseModel):
    id: int
    supplier_id: int
    name: str
    location: Optional[str]
    booth_number: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    contacts_count: int
    icp_criteria: Optional[dict]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _supplier_id(user: User) -> int:
    sid = getattr(user, "supplier_profile_id", None) or getattr(user, "id", None)
    if not sid:
        raise HTTPException(status_code=403, detail="Supplier profile required")
    return int(sid)


def _to_response(ex: Exhibition) -> dict:
    icp = None
    if ex.icp_criteria:
        try:
            icp = json.loads(ex.icp_criteria)
        except Exception:
            icp = ex.icp_criteria
    return {
        "id": ex.id,
        "supplier_id": ex.supplier_id,
        "name": ex.name,
        "location": ex.location,
        "booth_number": ex.booth_number,
        "start_date": ex.start_date,
        "end_date": ex.end_date,
        "status": ex.status,
        "contacts_count": ex.contacts_count,
        "icp_criteria": icp,
        "notes": ex.notes,
        "created_at": ex.created_at,
        "updated_at": ex.updated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_exhibition(
    body: ExhibitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new exhibition event."""
    supplier_id = _supplier_id(current_user)
    ex = Exhibition(
        supplier_id=supplier_id,
        name=body.name,
        location=body.location,
        booth_number=body.booth_number,
        start_date=body.start_date,
        end_date=body.end_date,
        icp_criteria=json.dumps(body.icp_criteria) if body.icp_criteria else None,
        notes=body.notes,
        status="planning",
        contacts_count=0,
    )
    db.add(ex)
    await db.commit()
    await db.refresh(ex)
    logger.info("Exhibition %d created for supplier %d", ex.id, supplier_id)
    return _to_response(ex)


@router.get("")
async def list_exhibitions(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all exhibitions for the current supplier."""
    supplier_id = _supplier_id(current_user)
    q = select(Exhibition).where(Exhibition.supplier_id == supplier_id)
    if status_filter:
        q = q.where(Exhibition.status == status_filter)
    q = q.order_by(Exhibition.start_date.desc().nullslast(), Exhibition.created_at.desc())
    result = await db.execute(q)
    return [_to_response(ex) for ex in result.scalars().all()]


@router.get("/{exhibition_id}")
async def get_exhibition(
    exhibition_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single exhibition by ID."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(Exhibition).where(
            Exhibition.id == exhibition_id,
            Exhibition.supplier_id == supplier_id,
        )
    )
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    return _to_response(ex)


@router.patch("/{exhibition_id}")
async def update_exhibition(
    exhibition_id: int,
    body: ExhibitionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update exhibition details."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(Exhibition).where(
            Exhibition.id == exhibition_id,
            Exhibition.supplier_id == supplier_id,
        )
    )
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    if body.name is not None:
        ex.name = body.name
    if body.location is not None:
        ex.location = body.location
    if body.booth_number is not None:
        ex.booth_number = body.booth_number
    if body.start_date is not None:
        ex.start_date = body.start_date
    if body.end_date is not None:
        ex.end_date = body.end_date
    if body.icp_criteria is not None:
        ex.icp_criteria = json.dumps(body.icp_criteria)
    if body.notes is not None:
        ex.notes = body.notes

    ex.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(ex)
    return _to_response(ex)


@router.delete("/{exhibition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exhibition(
    exhibition_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an exhibition (only in planning status)."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(Exhibition).where(
            Exhibition.id == exhibition_id,
            Exhibition.supplier_id == supplier_id,
        )
    )
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    if ex.status != "planning":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete exhibition in '{ex.status}' status. Only 'planning' exhibitions can be deleted.",
        )
    await db.delete(ex)
    await db.commit()


@router.patch("/{exhibition_id}/status")
async def update_exhibition_status(
    exhibition_id: int,
    body: ExhibitionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Advance exhibition lifecycle status."""
    supplier_id = _supplier_id(current_user)
    result = await db.execute(
        select(Exhibition).where(
            Exhibition.id == exhibition_id,
            Exhibition.supplier_id == supplier_id,
        )
    )
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    allowed = VALID_TRANSITIONS.get(ex.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{ex.status}' to '{body.status}'. Allowed: {allowed}",
        )
    ex.status = body.status
    ex.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(ex)
    return _to_response(ex)


@router.get("/{exhibition_id}/contacts")
async def list_exhibition_contacts(
    exhibition_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List business cards collected at a specific exhibition."""
    supplier_id = _supplier_id(current_user)

    # Verify ownership
    ex_result = await db.execute(
        select(Exhibition).where(
            Exhibition.id == exhibition_id,
            Exhibition.supplier_id == supplier_id,
        )
    )
    if not ex_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exhibition not found")

    result = await db.execute(
        select(BusinessCard)
        .where(BusinessCard.exhibition_id == exhibition_id)
        .order_by(BusinessCard.created_at.desc())
    )
    cards = result.scalars().all()
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "company_name": c.company_name,
            "job_title": c.job_title,
            "email": c.email,
            "phone": c.phone,
            "country": c.country,
            "ocr_status": c.ocr_status,
            "ocr_confidence": c.ocr_confidence,
            "converted_to_contact": c.converted_to_contact,
            "follow_up_sent": c.follow_up_sent,
            "created_at": c.created_at,
        }
        for c in cards
    ]
