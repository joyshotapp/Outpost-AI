"""Outbound campaign & contact management API — Sprint 7 (7.3, 7.4, 7.5).

Endpoints:
  POST   /outbound/campaigns                         create campaign + trigger enrichment
  GET    /outbound/campaigns                         list supplier campaigns
  GET    /outbound/campaigns/{id}                    get campaign details
  PATCH  /outbound/campaigns/{id}/pause              pause campaign
  PATCH  /outbound/campaigns/{id}/resume             resume campaign
  POST   /outbound/campaigns/{id}/start-sequence     import approved contacts → HeyReach
  GET    /outbound/campaigns/{id}/contacts           list contacts with enrichment data
  PATCH  /outbound/contacts/{id}/approve             approve contact for outreach
  PATCH  /outbound/contacts/{id}/exclude             exclude contact from outreach
  GET    /outbound/campaigns/{id}/sequences          LinkedIn sequence progress
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.models.outbound_campaign import OutboundCampaign
from app.models.outbound_contact import OutboundContact
from app.models.linkedin_sequence import LinkedInSequence

router = APIRouter(prefix="/outbound", tags=["outbound"])
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (inline — Sprint 7 specific)
# ──────────────────────────────────────────────────────────────────────────────

class IcpCriteria(BaseModel):
    industries: list[str] = []
    countries: list[str] = []
    job_titles: list[str] = []
    company_sizes: list[str] = []
    seniority_levels: list[str] = []
    limit: int = 500


class CampaignCreateRequest(BaseModel):
    campaign_name: str
    campaign_type: str = "linkedin"
    icp_criteria: IcpCriteria


class CampaignResponse(BaseModel):
    id: int
    supplier_id: int
    campaign_name: str
    campaign_type: str
    status: str
    clay_table_id: Optional[str]
    clay_enrichment_status: str
    heyreach_campaign_id: Optional[str]
    target_count: int
    contacts_reached: int
    responses_received: int
    hot_leads: int
    daily_connections_sent: int
    daily_messages_sent: int
    safety_paused: int
    created_at: str
    updated_at: str
    icp_criteria: Optional[dict]

    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    id: int
    campaign_id: int
    full_name: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    company_name: Optional[str]
    company_industry: Optional[str]
    company_size: Optional[str]
    company_country: Optional[str]
    job_title: Optional[str]
    seniority: Optional[str]
    status: str
    is_hot_lead: bool
    linkedin_opener: Optional[str]
    sequence_day: Optional[int]
    lead_score: Optional[float]
    created_at: str

    class Config:
        from_attributes = True


class SequenceResponse(BaseModel):
    id: int
    campaign_id: int
    contact_id: int
    sequence_status: str
    current_day: int
    total_days: int
    is_hot_lead: bool
    connection_sent_at: Optional[str]
    connection_accepted_at: Optional[str]
    replied_at: Optional[str]
    reply_content: Optional[str]
    hot_lead_flagged_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _serialise_campaign(c: OutboundCampaign) -> dict[str, Any]:
    icp = None
    if c.icp_criteria:
        try:
            icp = json.loads(c.icp_criteria)
        except (json.JSONDecodeError, TypeError):
            icp = None
    return {
        "id": c.id,
        "supplier_id": c.supplier_id,
        "campaign_name": c.campaign_name,
        "campaign_type": c.campaign_type,
        "status": c.status,
        "clay_table_id": c.clay_table_id,
        "clay_enrichment_status": c.clay_enrichment_status,
        "heyreach_campaign_id": c.heyreach_campaign_id,
        "target_count": c.target_count,
        "contacts_reached": c.contacts_reached,
        "responses_received": c.responses_received,
        "hot_leads": c.hot_leads,
        "daily_connections_sent": c.daily_connections_sent,
        "daily_messages_sent": c.daily_messages_sent,
        "safety_paused": c.safety_paused,
        "created_at": str(c.created_at),
        "updated_at": str(c.updated_at),
        "icp_criteria": icp,
    }


def _serialise_contact(c: OutboundContact) -> dict[str, Any]:
    return {
        "id": c.id,
        "campaign_id": c.campaign_id,
        "full_name": c.full_name,
        "email": c.email,
        "linkedin_url": c.linkedin_url,
        "company_name": c.company_name,
        "company_industry": c.company_industry,
        "company_size": c.company_size,
        "company_country": c.company_country,
        "job_title": c.job_title,
        "seniority": c.seniority,
        "status": c.status,
        "is_hot_lead": c.is_hot_lead,
        "linkedin_opener": c.linkedin_opener,
        "sequence_day": c.sequence_day,
        "lead_score": c.lead_score,
        "created_at": str(c.created_at),
    }


async def _get_campaign_owned_by(
    campaign_id: int,
    supplier_id: int,
    db: AsyncSession,
) -> OutboundCampaign:
    result = await db.execute(
        select(OutboundCampaign).where(
            OutboundCampaign.id == campaign_id,
            OutboundCampaign.supplier_id == supplier_id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


# ──────────────────────────────────────────────────────────────────────────────
# Campaign CRUD
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create an outbound campaign and trigger Clay ICP enrichment asynchronously.

    Returns the created campaign immediately; enrichment happens in the background.
    Poll `GET /outbound/campaigns/{id}` to check `clay_enrichment_status`.
    """
    # Resolve supplier_id
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    icp_dict = body.icp_criteria.model_dump()
    campaign = OutboundCampaign(
        supplier_id=supplier.id,
        campaign_name=body.campaign_name,
        campaign_type=body.campaign_type,
        status="draft",
        icp_criteria=json.dumps(icp_dict),
        clay_enrichment_status="pending",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # Trigger Clay enrichment Celery task
    from app.tasks.outbound import enrich_contacts_pipeline
    try:
        enrich_contacts_pipeline.delay(campaign.id, icp_dict)
    except Exception as exc:
        logger.warning(
            "Campaign %d created but enrichment queue failed: %s",
            campaign.id,
            exc,
        )

    logger.info(
        "Campaign %d created for supplier %d; enrichment task queued",
        campaign.id, supplier.id,
    )
    return _serialise_campaign(campaign)


@router.get("/campaigns")
async def list_campaigns(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List outbound campaigns for the current supplier."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        return {"campaigns": [], "total": 0}

    query = select(OutboundCampaign).where(OutboundCampaign.supplier_id == supplier.id)
    if status_filter:
        query = query.where(OutboundCampaign.status == status_filter)
    query = query.order_by(OutboundCampaign.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    campaigns = result.scalars().all()

    return {
        "campaigns": [_serialise_campaign(c) for c in campaigns],
        "total": len(campaigns),
        "page": page,
        "page_size": page_size,
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get campaign details including enrichment + HeyReach status."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    return _serialise_campaign(campaign)


@router.patch("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Pause a running outbound campaign (pauses HeyReach sequence too)."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    if campaign.status not in ("running", "draft"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause campaign with status '{campaign.status}'",
        )

    campaign.status = "paused"
    await db.commit()
    await db.refresh(campaign)

    # Best-effort HeyReach pause
    if campaign.heyreach_campaign_id:
        try:
            from app.services.heyreach import get_heyreach_service
            get_heyreach_service().pause_campaign(campaign.heyreach_campaign_id)
        except Exception as exc:
            logger.warning("HeyReach pause skipped: %s", exc)

    return _serialise_campaign(campaign)


@router.patch("/campaigns/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resume a paused campaign (re-activates HeyReach sequence)."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    if campaign.status != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Campaign is not paused (current status: '{campaign.status}')",
        )

    campaign.status = "running"
    campaign.safety_paused = 0
    await db.commit()
    await db.refresh(campaign)

    # Best-effort HeyReach resume
    if campaign.heyreach_campaign_id:
        try:
            from app.services.heyreach import get_heyreach_service
            get_heyreach_service().resume_campaign(campaign.heyreach_campaign_id)
        except Exception as exc:
            logger.warning("HeyReach resume skipped: %s", exc)

    return _serialise_campaign(campaign)


@router.post("/campaigns/{campaign_id}/start-sequence")
async def start_sequence(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate AI openers for approved contacts, then import into HeyReach and start sequence.

    This is a two-step background pipeline:
      1. generate_openers_batch (Claude)
      2. import_contacts_to_heyreach (HeyReach)

    Returns immediately with task status.
    """
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    if campaign.clay_enrichment_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Clay enrichment not yet completed; wait for clay_enrichment_status=completed",
        )

    # Approve all enriched contacts that don't have a decision yet
    from sqlalchemy import update as _upd
    await db.execute(
        _upd(OutboundContact)
        .where(
            OutboundContact.campaign_id == campaign_id,
            OutboundContact.status == "enriched",
        )
        .values(status="approved")
    )
    await db.commit()

    # Chain: generate openers then import to HeyReach
    from app.tasks.outbound import generate_openers_batch, import_contacts_to_heyreach
    from celery import chain as celery_chain
    try:
        celery_chain(
            generate_openers_batch.s(campaign_id),
            import_contacts_to_heyreach.si(campaign_id),
        ).delay()
    except Exception as exc:
        logger.warning("Sequence start queue failed for campaign %d: %s", campaign_id, exc)

    return {
        "message": "Sequence start queued",
        "campaign_id": campaign_id,
        "tasks": ["generate_openers_batch", "import_contacts_to_heyreach"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Contact management
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/campaigns/{campaign_id}/contacts")
async def list_contacts(
    campaign_id: int,
    contact_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List enriched contacts for a campaign with optional status filter."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    await _get_campaign_owned_by(campaign_id, supplier.id, db)  # ownership check

    query = select(OutboundContact).where(OutboundContact.campaign_id == campaign_id)
    if contact_status:
        query = query.where(OutboundContact.status == contact_status)
    query = query.order_by(OutboundContact.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    contacts = result.scalars().all()

    return {
        "contacts": [_serialise_contact(c) for c in contacts],
        "total": len(contacts),
        "page": page,
        "page_size": page_size,
    }


@router.patch("/contacts/{contact_id}/approve")
async def approve_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Approve a contact for LinkedIn outreach."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    result = await db.execute(
        select(OutboundContact).where(
            OutboundContact.id == contact_id,
            OutboundContact.supplier_id == supplier.id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.status = "approved"
    await db.commit()
    await db.refresh(contact)
    return _serialise_contact(contact)


@router.patch("/contacts/{contact_id}/exclude")
async def exclude_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Exclude a contact from outreach (will not be imported to HeyReach)."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    result = await db.execute(
        select(OutboundContact).where(
            OutboundContact.id == contact_id,
            OutboundContact.supplier_id == supplier.id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.status = "excluded"
    await db.commit()
    await db.refresh(contact)
    return _serialise_contact(contact)


# ──────────────────────────────────────────────────────────────────────────────
# LinkedIn sequence progress — 7.6
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/campaigns/{campaign_id}/sequences")
async def list_sequences(
    campaign_id: int,
    seq_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List Day 1–25 LinkedIn sequence progress for all contacts in a campaign."""
    from sqlalchemy import select as _sel
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        _sel(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    await _get_campaign_owned_by(campaign_id, supplier.id, db)

    query = select(LinkedInSequence).where(LinkedInSequence.campaign_id == campaign_id)
    if seq_status:
        query = query.where(LinkedInSequence.sequence_status == seq_status)
    query = query.order_by(LinkedInSequence.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sequences = result.scalars().all()

    return {
        "sequences": [
            {
                "id": s.id,
                "campaign_id": s.campaign_id,
                "contact_id": s.contact_id,
                "sequence_status": s.sequence_status,
                "current_day": s.current_day,
                "total_days": s.total_days,
                "is_hot_lead": s.is_hot_lead,
                "connection_sent_at": s.connection_sent_at,
                "connection_accepted_at": s.connection_accepted_at,
                "replied_at": s.replied_at,
                "reply_content": s.reply_content,
                "hot_lead_flagged_at": s.hot_lead_flagged_at,
                "created_at": str(s.created_at),
            }
            for s in sequences
        ],
        "total": len(sequences),
        "page": page,
        "page_size": page_size,
    }
