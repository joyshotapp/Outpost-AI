"""In-app notifications API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Notification, Supplier, User
from app.schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _resolve_supplier_id(current_user: User, db: AsyncSession) -> int:
    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.user_id == current_user.id)
    )
    supplier = supplier_result.scalars().first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier profile not found",
        )
    return supplier.id


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NotificationResponse]:
    if current_user.role.value != "supplier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can view notifications",
        )

    supplier_id = await _resolve_supplier_id(current_user, db)

    query = select(Notification).filter(Notification.supplier_id == supplier_id)
    if unread_only:
        query = query.filter(Notification.is_read == 0)

    result = await db.execute(query.order_by(Notification.created_at.desc()).limit(limit))
    notifications = result.scalars().all()

    return [NotificationResponse.model_validate(item) for item in notifications]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    if current_user.role.value != "supplier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can update notifications",
        )

    supplier_id = await _resolve_supplier_id(current_user, db)

    result = await db.execute(
        select(Notification).filter(
            Notification.id == notification_id,
            Notification.supplier_id == supplier_id,
        )
    )
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = 1
    await db.commit()
    await db.refresh(notification)

    return NotificationResponse.model_validate(notification)
