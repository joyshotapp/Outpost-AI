"""Direct messaging service — Sprint 10 (Task 10.7).

Handles buyer ↔ supplier conversations and per-message CRUD:
  - Start (or return existing) conversation between buyer and supplier
  - List buyer's or supplier's conversations with last-message preview
  - Send a message, update unread counters + last_message_at
  - Mark a conversation as read (clear unread counter for the requesting party)
  - Paginate messages within a conversation
  - Unread badge count for nav indicators
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.conversation import Conversation
from app.models.direct_message import DirectMessage
from app.models.supplier import Supplier
from app.models.buyer import Buyer

logger = logging.getLogger(__name__)

_UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(_UTC)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create_conversation(
    db: AsyncSession,
    buyer_id: int,
    supplier_id: int,
    subject: str | None = None,
) -> Conversation:
    """Return existing direct conversation or create a new one."""
    result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.buyer_id == buyer_id,
                Conversation.supplier_id == supplier_id,
                Conversation.conversation_type == "direct",
            )
        )
    )
    conv = result.scalars().first()
    if conv:
        return conv

    conv = Conversation(
        buyer_id=buyer_id,
        supplier_id=supplier_id,
        conversation_type="direct",
        status="active",
        message_count=0,
        unread_buyer_count=0,
        unread_supplier_count=0,
    )
    db.add(conv)
    await db.flush()
    return conv


# ── Public service functions ──────────────────────────────────────────────────

async def list_conversations(
    db: AsyncSession,
    *,
    buyer_id: int | None = None,
    supplier_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List conversations for a buyer or supplier with pagination."""
    query = select(Conversation)
    if buyer_id is not None:
        query = query.where(Conversation.buyer_id == buyer_id)
    if supplier_id is not None:
        query = query.where(Conversation.supplier_id == supplier_id)
    query = query.where(Conversation.conversation_type == "direct")
    query = query.order_by(Conversation.last_message_at.desc().nullslast())

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    convs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
        "conversations": convs,
    }


async def start_conversation(
    db: AsyncSession,
    *,
    buyer_id: int,
    supplier_id: int,
    initial_message: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """Start (or reuse) a conversation and send the first message."""
    if len(initial_message) > settings.MESSAGE_MAX_LENGTH:
        raise ValueError(f"Message exceeds {settings.MESSAGE_MAX_LENGTH} characters")

    # Validate buyer + supplier exist
    buyer_res = await db.execute(select(Buyer).where(Buyer.buyer_id == buyer_id))
    if not buyer_res.scalars().first():
        raise ValueError("Buyer not found")

    supplier_res = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    if not supplier_res.scalars().first():
        raise ValueError("Supplier not found")

    conv = await _get_or_create_conversation(db, buyer_id, supplier_id, subject)

    msg = DirectMessage(
        conversation_id=conv.id,
        sender_type="buyer",
        sender_id=buyer_id,
        body=initial_message,
        is_read=False,
    )
    db.add(msg)

    conv.message_count = (conv.message_count or 0) + 1
    conv.unread_supplier_count = (conv.unread_supplier_count or 0) + 1
    conv.last_message_at = _now()

    await db.commit()
    await db.refresh(conv)
    await db.refresh(msg)
    return {"conversation": conv, "message": msg}


async def get_messages(
    db: AsyncSession,
    conversation_id: int,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Return paginated messages for a conversation (oldest first)."""
    query = select(DirectMessage).where(
        DirectMessage.conversation_id == conversation_id
    )

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    query = query.order_by(DirectMessage.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    msgs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
        "messages": msgs,
    }


async def send_message(
    db: AsyncSession,
    conversation_id: int,
    sender_type: str,          # "buyer" | "supplier"
    sender_id: int,
    body: str,
    attachment_url: str | None = None,
) -> DirectMessage:
    """Send a message and update conversation unread counters."""
    if len(body) > settings.MESSAGE_MAX_LENGTH:
        raise ValueError(f"Message exceeds {settings.MESSAGE_MAX_LENGTH} characters")
    if sender_type not in ("buyer", "supplier"):
        raise ValueError("sender_type must be 'buyer' or 'supplier'")

    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalars().first()
    if not conv:
        raise ValueError("Conversation not found")

    msg = DirectMessage(
        conversation_id=conversation_id,
        sender_type=sender_type,
        sender_id=sender_id,
        body=body,
        is_read=False,
        attachment_url=attachment_url,
    )
    db.add(msg)

    conv.message_count = (conv.message_count or 0) + 1
    conv.last_message_at = _now()

    if sender_type == "buyer":
        conv.unread_supplier_count = (conv.unread_supplier_count or 0) + 1
    else:
        conv.unread_buyer_count = (conv.unread_buyer_count or 0) + 1

    await db.commit()
    await db.refresh(msg)
    return msg


async def mark_conversation_read(
    db: AsyncSession,
    conversation_id: int,
    reader_type: str,   # "buyer" | "supplier"
) -> None:
    """Mark all unread messages in conversation as read for the given party."""
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalars().first()
    if not conv:
        raise ValueError("Conversation not found")

    now = _now()

    # Mark individual messages as read
    await db.execute(
        update(DirectMessage)
        .where(
            and_(
                DirectMessage.conversation_id == conversation_id,
                DirectMessage.is_read.is_(False),
                DirectMessage.sender_type != reader_type,
            )
        )
        .values(is_read=True, read_at=now)
    )

    # Reset unread counter
    if reader_type == "buyer":
        conv.unread_buyer_count = 0
    else:
        conv.unread_supplier_count = 0

    await db.commit()


async def get_unread_count(
    db: AsyncSession,
    *,
    buyer_id: int | None = None,
    supplier_id: int | None = None,
) -> int:
    """Return total unread message count badge for buyer or supplier."""
    query = select(Conversation).where(Conversation.conversation_type == "direct")
    if buyer_id is not None:
        query = query.where(Conversation.buyer_id == buyer_id)
    if supplier_id is not None:
        query = query.where(Conversation.supplier_id == supplier_id)

    result = await db.execute(query)
    convs = result.scalars().all()

    if buyer_id is not None:
        return sum((c.unread_buyer_count or 0) for c in convs)
    return sum((c.unread_supplier_count or 0) for c in convs)
