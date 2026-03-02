"""Direct messaging API — Sprint 10 (Task 10.7).

Endpoints:
  GET  /messages/conversations                         — list conversations
  POST /messages/conversations                         — start conversation
  GET  /messages/conversations/{id}/messages           — paginated messages
  POST /messages/conversations/{id}/messages           — send message
  PATCH /messages/conversations/{id}/read              — mark as read
  GET  /messages/unread-count                          — badge count
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services import messages as msg_svc

router = APIRouter(prefix="/messages", tags=["messages"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: int
    buyer_id: int | None = None
    supplier_id: int | None = None
    conversation_type: str
    status: str
    message_count: int = 0
    unread_buyer_count: int = 0
    unread_supplier_count: int = 0
    last_message_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    conversations: list[ConversationOut]


class StartConversationRequest(BaseModel):
    supplier_id: int
    initial_message: str = Field(..., min_length=1, max_length=5000)
    subject: str | None = None


class StartConversationResponse(BaseModel):
    conversation: ConversationOut
    message_id: int


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_type: str
    sender_id: int
    body: str
    is_read: bool = False
    read_at: datetime | None = None
    attachment_url: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    messages: list[MessageOut]


class SendMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    attachment_url: str | None = None


class UnreadCountResponse(BaseModel):
    unread_count: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _buyer_id_from_user(user: User) -> int | None:
    """Extract the buyer_id from the user's profile, if it exists."""
    return getattr(user, "buyer_profile_id", None) or getattr(user, "id", None)


def _supplier_id_from_user(user: User) -> int | None:
    return getattr(user, "supplier_profile_id", None)


def _is_buyer(user: User) -> bool:
    return getattr(user, "role", "") == "buyer" or True   # default: buyers can message


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List conversations for the authenticated buyer or supplier."""
    buyer_id = _buyer_id_from_user(current_user)
    supplier_id = _supplier_id_from_user(current_user)

    result = await msg_svc.list_conversations(
        db, buyer_id=buyer_id, supplier_id=supplier_id,
        page=page, page_size=page_size,
    )
    return ConversationListResponse(**result)


@router.post(
    "/conversations",
    response_model=StartConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_conversation(
    body: StartConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Start a direct conversation with a supplier (buyer only)."""
    buyer_id = _buyer_id_from_user(current_user)
    if not buyer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyer profile not found")

    try:
        data = await msg_svc.start_conversation(
            db,
            buyer_id=buyer_id,
            supplier_id=body.supplier_id,
            initial_message=body.initial_message,
            subject=body.subject,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return StartConversationResponse(
        conversation=ConversationOut.model_validate(data["conversation"]),
        message_id=data["message"].id,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve paginated messages for a conversation."""
    result = await msg_svc.get_messages(db, conversation_id, page=page, page_size=page_size)
    return MessageListResponse(**result)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Send a message in an existing conversation."""
    # Determine whether current user is buyer or supplier in this conversation
    buyer_id = _buyer_id_from_user(current_user)
    supplier_id = _supplier_id_from_user(current_user)
    sender_type = "supplier" if supplier_id else "buyer"
    sender_id = supplier_id if sender_type == "supplier" else buyer_id

    if not sender_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User profile not found")

    try:
        msg = await msg_svc.send_message(
            db,
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            body=body.body,
            attachment_url=body.attachment_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return MessageOut.model_validate(msg)


@router.patch("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Mark all messages in this conversation as read for the current user."""
    supplier_id = _supplier_id_from_user(current_user)
    reader_type = "supplier" if supplier_id else "buyer"

    try:
        await msg_svc.mark_conversation_read(db, conversation_id, reader_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return Response(status_code=204)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    """Return total unread message count for nav badge."""
    buyer_id = _buyer_id_from_user(current_user)
    supplier_id = _supplier_id_from_user(current_user)

    count = await msg_svc.get_unread_count(db, buyer_id=buyer_id, supplier_id=supplier_id)
    return UnreadCountResponse(unread_count=count)
