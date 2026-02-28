"""Supplier API endpoints"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Supplier, User
from app.schemas import (
    SupplierCreateRequest,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdateRequest,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    request: SupplierCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    """Create a new supplier"""
    # Check if company slug already exists
    result = await db.execute(
        select(Supplier).filter(Supplier.company_slug == request.company_slug)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company slug already exists",
        )

    # Verify user exists
    user_result = await db.execute(select(User).filter(User.id == request.user_id))
    if not user_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Create supplier
    supplier = Supplier(
        user_id=request.user_id,
        company_name=request.company_name,
        company_slug=request.company_slug,
        website=request.website,
        phone=request.phone,
        email=request.email,
        country=request.country,
        city=request.city,
        industry=request.industry,
        company_description=request.company_description,
        number_of_employees=request.number_of_employees,
        established_year=request.established_year,
        certifications=request.certifications,
        main_products=request.main_products,
        manufacturing_capacity=request.manufacturing_capacity,
        lead_time_days=request.lead_time_days,
        is_active=True,
        is_verified=False,
        view_count=0,
    )

    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)

    return SupplierResponse.model_validate(supplier)


@router.get("", response_model=List[SupplierListResponse])
async def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    country: str | None = None,
    industry: str | None = None,
    is_verified: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> List[SupplierListResponse]:
    """List suppliers with filtering"""
    query = select(Supplier)

    if country:
        query = query.filter(Supplier.country == country)
    if industry:
        query = query.filter(Supplier.industry == industry)
    if is_verified is not None:
        query = query.filter(Supplier.is_verified == is_verified)

    # Always filter for active suppliers
    query = query.filter(Supplier.is_active == True)

    result = await db.execute(
        query.order_by(Supplier.created_at.desc()).offset(skip).limit(limit)
    )
    suppliers = result.scalars().all()

    return [SupplierListResponse.model_validate(s) for s in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    """Get supplier by ID"""
    result = await db.execute(
        select(Supplier).filter(Supplier.id == supplier_id)
    )
    supplier = result.scalars().first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return SupplierResponse.model_validate(supplier)


@router.get("/by-slug/{company_slug}", response_model=SupplierResponse)
async def get_supplier_by_slug(
    company_slug: str,
    db: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    """Get supplier by company slug"""
    result = await db.execute(
        select(Supplier).filter(Supplier.company_slug == company_slug)
    )
    supplier = result.scalars().first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return SupplierResponse.model_validate(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    request: SupplierUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SupplierResponse:
    """Update supplier details"""
    result = await db.execute(
        select(Supplier).filter(Supplier.id == supplier_id)
    )
    supplier = result.scalars().first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check authorization (only own supplier can update)
    if supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this supplier",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    await db.commit()
    await db.refresh(supplier)

    return SupplierResponse.model_validate(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate (soft delete) a supplier"""
    result = await db.execute(
        select(Supplier).filter(Supplier.id == supplier_id)
    )
    supplier = result.scalars().first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    # Check authorization
    if supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate this supplier",
        )

    supplier.is_active = False
    await db.commit()
