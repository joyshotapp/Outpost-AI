"""Supplier search API — Sprint 10 (Task 10.2).

Endpoints:
  GET  /search/suppliers         — full-text + filtered search
  GET  /search/suppliers/suggest — autocomplete prefix suggestions
  POST /search/suppliers/reindex — admin: reindex all active suppliers
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.search import get_search_service

router = APIRouter(prefix="/search", tags=["search"])


# ── Response schemas ──────────────────────────────────────────────────────────

class SupplierSearchResult(BaseModel):
    id: int | None = None
    company_name: str
    company_slug: str
    company_description: str | None = None
    main_products: str | None = None
    certifications: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    is_verified: bool = False
    view_count: int = 0
    lead_time_days: int | None = None
    number_of_employees: int | None = None

    class Config:
        from_attributes = True


class SupplierSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    results: list[SupplierSearchResult]
    took_ms: float | None = None
    stub: bool = Field(False, alias="_stub")

    class Config:
        populate_by_name = True


class SuggestResponse(BaseModel):
    suggestions: list[str]


class ReindexResponse(BaseModel):
    indexed: int
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/suppliers",
    response_model=SupplierSearchResponse,
    summary="Search supplier profiles",
)
async def search_suppliers(
    q: str = Query("", description="Full-text search query"),
    industry: str | None = Query(None, description="Filter by industry"),
    country: str | None = Query(None, description="Filter by ISO-2 country code"),
    certifications: str | None = Query(None, description="Comma-separated certifications (e.g. ISO 9001,ISO 14001)"),
    is_verified: bool | None = Query(None, description="Filter verified suppliers only"),
    min_employees: int | None = Query(None, description="Minimum headcount"),
    max_lead_time_days: int | None = Query(None, description="Maximum lead time in days"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("_score", description="Sort key: _score | view_count | lead_time_days | newest"),
) -> Any:
    svc = get_search_service()
    result = svc.search(
        q=q,
        industry=industry,
        country=country,
        certifications=certifications,
        is_verified=is_verified,
        min_employees=min_employees,
        max_lead_time_days=max_lead_time_days,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )
    # Normalise alias
    result.setdefault("_stub", result.pop("_stub", False))
    return result


@router.get(
    "/suppliers/suggest",
    response_model=SuggestResponse,
    summary="Autocomplete company name suggestions",
)
async def suggest_suppliers(
    q: str = Query(..., min_length=1, description="Prefix to autocomplete"),
    size: int = Query(5, ge=1, le=20),
) -> SuggestResponse:
    svc = get_search_service()
    suggestions = svc.suggest(prefix=q, size=size)
    return SuggestResponse(suggestions=suggestions)


@router.post(
    "/suppliers/reindex",
    response_model=ReindexResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Re-index all active suppliers (admin only)",
)
async def reindex_suppliers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReindexResponse:
    """Trigger a full reindex of all active suppliers into Elasticsearch.
    Requires admin role.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    from app.models import Supplier  # local import avoids circular dep

    result = await db.execute(
        select(Supplier).where(Supplier.is_active.is_(True))
    )
    suppliers = list(result.scalars().all())

    svc = get_search_service()
    svc.ensure_index()
    indexed = svc.reindex_all(suppliers)

    return ReindexResponse(
        indexed=indexed,
        message=f"Reindexed {indexed} suppliers successfully",
    )
