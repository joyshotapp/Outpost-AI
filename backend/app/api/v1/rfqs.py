"""RFQ (Request for Quotation) API endpoints"""

import json
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import RFQ, User, Supplier
from app.schemas import RFQCreateRequest, RFQListResponse, RFQResponse
from app.services.s3 import S3Service
from app.services.claude import get_claude_service

router = APIRouter(prefix="/rfqs", tags=["rfqs"])


@router.post("", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq(
    title: str = Form(...),
    description: str = Form(...),
    specifications: str = Form(None),
    quantity: int = Form(None),
    unit: str = Form(None),
    required_delivery_date: str = Form(None),
    attachment: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFQResponse:
    """Create a new RFQ

    Request body:
    - title: RFQ title (required)
    - description: RFQ description/content (required)
    - specifications: Additional specifications (optional)
    - quantity: Required quantity (optional)
    - unit: Unit of measurement (optional)
    - required_delivery_date: Expected delivery date (optional)
    - attachment: PDF file (optional)
    """

    # Verify user is a buyer
    if current_user.role != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers can submit RFQs",
        )

    attachment_url = None
    s3_service = S3Service()

    # Upload attachment to S3 if provided
    if attachment and attachment.filename:
        try:
            # Validate file type (only PDF)
            if attachment.content_type not in ["application/pdf", "application/x-pdf"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PDF files are allowed",
                )

            # Read file content
            file_content = await attachment.read()

            # Upload to S3
            attachment_url = await s3_service.upload_rfq_attachment(
                file_content=file_content,
                filename=attachment.filename,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to upload attachment: {str(e)}",
            )

    # Create RFQ record
    rfq = RFQ(
        buyer_id=current_user.id,
        title=title,
        description=description,
        specifications=specifications,
        quantity=quantity,
        unit=unit,
        required_delivery_date=required_delivery_date,
        attachment_url=attachment_url,
        status="pending",
    )

    db.add(rfq)
    await db.commit()
    await db.refresh(rfq)

    # Analyze PDF if attachment was uploaded
    if attachment_url:
        try:
            claude_service = get_claude_service()
            # Extract S3 object key from URL (reverse engineering from presigned URL)
            # The attachment_url is a presigned URL, we need the S3 key
            # For now, construct it from the pattern used in S3Service
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            s3_object_key = f"rfqs/{timestamp}-{attachment.filename}"

            # Analyze PDF with vision and Textract
            pdf_analysis = await claude_service.analyze_rfq_pdf(
                s3_object_key=s3_object_key,
                rfq_text=description,
            )

            # Store PDF vision analysis if successful
            if pdf_analysis.get("success"):
                rfq.pdf_vision_data = json.dumps(pdf_analysis, ensure_ascii=False)
                await db.commit()
                await db.refresh(rfq)
        except Exception as e:
            # Log error but don't fail the RFQ creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to analyze RFQ PDF: {str(e)}")

    return RFQResponse.model_validate(rfq)


@router.get("", response_model=List[RFQListResponse])
async def list_rfqs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    lead_grade: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RFQListResponse]:
    """List RFQs

    - Buyers see their own submitted RFQs
    - Suppliers see RFQs for their company
    - Admins see all RFQs
    """
    query = select(RFQ)

    # Filter by user role
    if current_user.role == "buyer":
        query = query.filter(RFQ.buyer_id == current_user.id)
    elif current_user.role == "supplier":
        # Get supplier ID for current user
        supplier_result = await db.execute(
            select(Supplier).filter(Supplier.user_id == current_user.id)
        )
        supplier = supplier_result.scalars().first()
        if supplier:
            query = query.filter(RFQ.supplier_id == supplier.id)
        else:
            # Supplier hasn't set up company yet
            return []
    # else: admin sees all RFQs

    # Apply filters
    if status:
        query = query.filter(RFQ.status == status)
    if lead_grade:
        query = query.filter(RFQ.lead_grade == lead_grade)

    result = await db.execute(
        query.order_by(RFQ.created_at.desc()).offset(skip).limit(limit)
    )
    rfqs = result.scalars().all()

    return [RFQListResponse.model_validate(r) for r in rfqs]


@router.get("/{rfq_id}", response_model=RFQResponse)
async def get_rfq(
    rfq_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFQResponse:
    """Get RFQ by ID"""

    result = await db.execute(select(RFQ).filter(RFQ.id == rfq_id))
    rfq = result.scalars().first()

    if not rfq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found",
        )

    # Check authorization
    if current_user.role == "buyer" and rfq.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this RFQ",
        )
    elif current_user.role == "supplier":
        supplier_result = await db.execute(
            select(Supplier).filter(Supplier.user_id == current_user.id)
        )
        supplier = supplier_result.scalars().first()
        if not supplier or rfq.supplier_id != supplier.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this RFQ",
            )

    return RFQResponse.model_validate(rfq)
