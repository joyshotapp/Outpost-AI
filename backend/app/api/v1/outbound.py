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


# ══════════════════════════════════════════════════════════════════════════════
# Sprint 8 — Email Campaign API (Task 8.2)
# ══════════════════════════════════════════════════════════════════════════════

from app.models.email_sequence import EmailSequence
from app.models.unified_lead import UnifiedLead


class EmailCampaignCreateRequest(BaseModel):
    campaign_name: str
    icp_criteria: IcpCriteria
    daily_send_limit: int = 50


@router.post("/campaigns/email", status_code=status.HTTP_201_CREATED)
async def create_email_campaign(
    body: EmailCampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new email outbound campaign (campaign_type=email).

    Immediately triggers Clay enrichment; Instantly import done separately
    via POST /campaigns/{id}/start-email-sequence.
    """
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = OutboundCampaign(
        supplier_id=supplier.id,
        campaign_name=body.campaign_name,
        campaign_type="email",
        status="draft",
        icp_criteria=json.dumps(body.icp_criteria.model_dump()),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # Trigger Clay enrichment (same pipeline as LinkedIn)
    from app.tasks.outbound import enrich_contacts_pipeline
    enrich_contacts_pipeline.delay(campaign.id, body.icp_criteria.model_dump())

    logger.info("Email campaign created: id=%d supplier=%d", campaign.id, supplier.id)
    return {"campaign_id": campaign.id, "status": campaign.status, "campaign_type": "email"}


@router.post("/campaigns/{campaign_id}/start-email-sequence", status_code=status.HTTP_202_ACCEPTED)
async def start_email_sequence(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Import approved contacts into Instantly and start the email sequence.

    Prerequisite: contacts must be enriched (clay_enrichment_status=completed)
    and approved (status=approved) with valid email addresses.
    """
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    if campaign.campaign_type != "email":
        raise HTTPException(status_code=400, detail="Campaign is not an email campaign")
    if campaign.clay_enrichment_status != "completed":
        raise HTTPException(status_code=400, detail="Enrichment not yet completed")

    from app.tasks.outbound_email import import_contacts_to_instantly
    import_contacts_to_instantly.delay(campaign_id)

    return {"campaign_id": campaign_id, "status": "importing", "message": "Email sequence import started"}


@router.get("/campaigns/{campaign_id}/email-sequences")
async def list_email_sequences(
    campaign_id: int,
    seq_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List email sequence progress for all contacts in an email campaign."""
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    await _get_campaign_owned_by(campaign_id, supplier.id, db)

    query = select(EmailSequence).where(EmailSequence.campaign_id == campaign_id)
    if seq_status:
        query = query.where(EmailSequence.status == seq_status)
    query = query.order_by(EmailSequence.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sequences = result.scalars().all()

    return {
        "sequences": [
            {
                "id": s.id,
                "email": s.email,
                "full_name": s.full_name,
                "company_name": s.company_name,
                "status": s.status,
                "current_step": s.current_step,
                "total_steps": s.total_steps,
                "emails_sent": s.emails_sent,
                "emails_opened": s.emails_opened,
                "reply_received": s.reply_received,
                "replied_at": s.replied_at,
                "is_bounced": s.is_bounced,
                "bounce_type": s.bounce_type,
                "is_unsubscribed": s.is_unsubscribed,
                "is_hot_lead": s.is_hot_lead,
                "hot_lead_reason": s.hot_lead_reason,
                "hubspot_synced": s.hubspot_synced,
                "created_at": str(s.created_at),
            }
            for s in sequences
        ],
        "total": len(sequences),
        "page": page,
        "page_size": page_size,
    }


@router.post("/campaigns/{campaign_id}/sync-analytics", status_code=status.HTTP_202_ACCEPTED)
async def sync_campaign_analytics(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger an immediate analytics sync from Instantly for this campaign."""
    from app.models import Supplier as SupplierModel
    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    campaign = await _get_campaign_owned_by(campaign_id, supplier.id, db)
    if campaign.campaign_type != "email":
        raise HTTPException(status_code=400, detail="Analytics sync only available for email campaigns")

    from app.tasks.outbound_email import sync_email_campaign_analytics
    task = sync_email_campaign_analytics.delay(campaign_id)

    return {"campaign_id": campaign_id, "task_id": task.id, "status": "syncing"}


# ══════════════════════════════════════════════════════════════════════════════
# Sprint 8 — Unified Leads / Business Workbench API (Task 8.5 / 8.6)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/leads")
async def list_unified_leads(
    lead_grade: Optional[str] = Query(None, description="A | B | C"),
    source: Optional[str] = Query(None, description="rfq | linkedin | email | visitor | chat | manual"),
    lead_status: Optional[str] = Query(None, alias="status"),
    is_hot_lead: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Business Workbench — List unified leads from all sources.

    Supports filtering by grade (A/B/C), source, status, and hot_lead flag.
    Sorted by lead_score DESC (highest priority first).
    """
    from sqlalchemy import and_, desc
    from app.models import Supplier as SupplierModel

    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    conditions = [UnifiedLead.supplier_id == supplier.id]
    if lead_grade:
        conditions.append(UnifiedLead.lead_grade == lead_grade.upper())
    if source:
        conditions.append(UnifiedLead.source == source)
    if lead_status:
        conditions.append(UnifiedLead.status == lead_status)
    if is_hot_lead is not None:
        conditions.append(UnifiedLead.is_hot_lead == is_hot_lead)

    count_result = await db.execute(
        select(UnifiedLead).where(and_(*conditions))
    )
    total = len(count_result.scalars().all())

    query = (
        select(UnifiedLead)
        .where(and_(*conditions))
        .order_by(desc(UnifiedLead.lead_score), UnifiedLead.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    leads = result.scalars().all()

    return {
        "leads": [
            {
                "id": ld.id,
                "email": ld.email,
                "full_name": ld.full_name,
                "company_name": ld.company_name,
                "job_title": ld.job_title,
                "source": ld.source,
                "source_ref_id": ld.source_ref_id,
                "lead_score": ld.lead_score,
                "lead_grade": ld.lead_grade,
                "status": ld.status,
                "recommended_action": ld.recommended_action,
                "is_hot_lead": ld.is_hot_lead,
                "auto_reply_sent": ld.auto_reply_sent,
                "draft_reply_body": ld.draft_reply_body,
                "draft_reply_sent": ld.draft_reply_sent,
                "hubspot_synced": ld.hubspot_synced,
                "created_at": str(ld.created_at),
                "updated_at": str(ld.updated_at),
            }
            for ld in leads
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/leads/{lead_id}")
async def get_unified_lead(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get detailed info for a single unified lead."""
    from app.models import Supplier as SupplierModel

    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    result = await db.execute(
        select(UnifiedLead).where(
            UnifiedLead.id == lead_id,
            UnifiedLead.supplier_id == supplier.id,
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "id": lead.id,
        "email": lead.email,
        "full_name": lead.full_name,
        "company_name": lead.company_name,
        "company_domain": lead.company_domain,
        "job_title": lead.job_title,
        "phone": lead.phone,
        "linkedin_url": lead.linkedin_url,
        "source": lead.source,
        "source_ref_id": lead.source_ref_id,
        "lead_score": lead.lead_score,
        "lead_grade": lead.lead_grade,
        "score_breakdown": json.loads(lead.score_breakdown) if lead.score_breakdown else {},
        "status": lead.status,
        "recommended_action": lead.recommended_action,
        "is_hot_lead": lead.is_hot_lead,
        "hot_lead_reason": lead.hot_lead_reason,
        "auto_reply_sent": lead.auto_reply_sent,
        "auto_reply_type": lead.auto_reply_type,
        "draft_reply_body": lead.draft_reply_body,
        "draft_reply_generated_at": lead.draft_reply_generated_at,
        "draft_reply_sent": lead.draft_reply_sent,
        "draft_reply_sent_at": lead.draft_reply_sent_at,
        "hubspot_contact_id": lead.hubspot_contact_id,
        "hubspot_deal_id": lead.hubspot_deal_id,
        "hubspot_synced": lead.hubspot_synced,
        "raw_payload": json.loads(lead.raw_payload) if lead.raw_payload else {},
        "created_at": str(lead.created_at),
        "updated_at": str(lead.updated_at),
    }


@router.post("/leads/{lead_id}/send-draft", status_code=status.HTTP_200_OK)
async def send_draft_reply(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """8.8 — Supplier confirms and sends the AI-generated draft reply.

    Marks the draft as sent and updates lead status to 'contacted'.
    Actual email delivery is handled via Instantly API.
    """
    from app.models import Supplier as SupplierModel
    from sqlalchemy import update as _upd

    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    result = await db.execute(
        select(UnifiedLead).where(
            UnifiedLead.id == lead_id,
            UnifiedLead.supplier_id == supplier.id,
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.draft_reply_body:
        raise HTTPException(status_code=400, detail="No draft reply available. Generate draft first.")
    if lead.draft_reply_sent:
        raise HTTPException(status_code=400, detail="Draft already sent")

    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.execute(
        _upd(UnifiedLead)
        .where(UnifiedLead.id == lead_id)
        .values(
            draft_reply_sent=True,
            draft_reply_sent_at=now_iso,
            status="contacted",
        )
    )
    await db.commit()

    logger.info("Draft sent: lead_id=%d by supplier=%d", lead_id, supplier.id)
    return {
        "lead_id": lead_id,
        "draft_sent": True,
        "sent_at": now_iso,
        "status": "contacted",
    }


@router.post("/leads/{lead_id}/regenerate-draft", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_draft_reply(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Force-regenerate the AI draft reply for a lead (clears existing draft)."""
    from app.models import Supplier as SupplierModel
    from sqlalchemy import update as _upd

    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    result = await db.execute(
        select(UnifiedLead).where(
            UnifiedLead.id == lead_id,
            UnifiedLead.supplier_id == supplier.id,
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.draft_reply_sent:
        raise HTTPException(status_code=400, detail="Cannot regenerate — draft already sent")

    # Clear existing draft so the task will regenerate
    await db.execute(
        _upd(UnifiedLead)
        .where(UnifiedLead.id == lead_id)
        .values(draft_reply_body=None, draft_reply_generated_at=None)
    )
    await db.commit()

    from app.tasks.outbound_email import generate_b_grade_draft
    task = generate_b_grade_draft.delay(lead_id)

    return {"lead_id": lead_id, "task_id": task.id, "status": "regenerating"}


# ══════════════════════════════════════════════════════════════════════════════
# Sprint 8 — Inbound Lead Intake (Task 8.5)
# ══════════════════════════════════════════════════════════════════════════════

class InboundLeadCreate(BaseModel):
    """Manual or API-triggered inbound lead — fed through unified processing matrix."""

    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: str = "manual"  # rfq | linkedin | email | visitor | chat | manual
    source_ref_id: Optional[str] = None
    message: Optional[str] = None  # original message / RFQ body
    raw_payload: Optional[dict] = None


@router.post("/leads/inbound", status_code=status.HTTP_202_ACCEPTED)
async def intake_inbound_lead(
    body: InboundLeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """8.5 — Unified lead intake endpoint.

    Routes the lead through the entire scoring + action matrix:
    - Grade A (≥80): Slack alert + B-grade AI draft + HubSpot deal
    - Grade B (50-79): AI draft generated + HubSpot contact
    - Grade C (<50): Auto thank-you reply + HubSpot contact

    Returns lead_id and assigned grade immediately; async tasks run in background.
    """
    from app.models import Supplier as SupplierModel
    from app.services.lead_pipeline import get_lead_pipeline

    sup_result = await db.execute(
        select(SupplierModel).where(SupplierModel.user_id == current_user.id)
    )
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=403, detail="Supplier profile required")

    pipeline = get_lead_pipeline()
    payload = body.model_dump(exclude_none=True)
    payload["supplier_id"] = supplier.id

    lead = await pipeline.process_inbound(
        supplier_id=supplier.id,
        email=body.email,
        full_name=body.full_name,
        company_name=body.company_name,
        company_domain=body.company_domain,
        job_title=body.job_title,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        source=body.source,
        source_ref_id=body.source_ref_id,
        raw_payload=payload,
        db=db,
    )

    return {
        "lead_id": lead.id,
        "email": lead.email,
        "lead_grade": lead.lead_grade,
        "lead_score": lead.lead_score,
        "recommended_action": lead.recommended_action,
        "status": lead.status,
    }

