"""Socket.IO server for supplier AI avatar real-time chat"""

import json
import logging
from typing import Optional

import socketio
from sqlalchemy import select

from app.database import async_session_maker
from app.models import Conversation, ConversationMessage, Notification, Supplier, User
from app.security import decode_access_token
from app.services.rag_chat import get_rag_chat_service
from app.services.slack import get_slack_service

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(socketio_server=sio)


def _supplier_room_name(supplier_id: int) -> str:
    return f"supplier:{supplier_id}"


async def _get_user_from_token(token: Optional[str]) -> Optional[User]:
    if not token:
        return None

    normalized = token.replace("Bearer ", "").strip()
    user_id = decode_access_token(normalized)
    if not user_id:
        return None

    async with async_session_maker() as session:
        result = await session.execute(select(User).filter(User.id == int(user_id)))
        return result.scalars().first()


async def _assert_supplier_access(user: User, supplier_id: int) -> Supplier:
    async with async_session_maker() as session:
        result = await session.execute(select(Supplier).filter(Supplier.id == supplier_id))
        supplier = result.scalars().first()
        if not supplier:
            raise ValueError("Supplier not found")
        if user.role.value != "admin" and supplier.user_id != user.id:
            raise ValueError("Not authorized for this supplier")
        return supplier


async def _get_supplier(supplier_id: int) -> Supplier:
    async with async_session_maker() as session:
        result = await session.execute(select(Supplier).filter(Supplier.id == supplier_id))
        supplier = result.scalars().first()
        if not supplier:
            raise ValueError("Supplier not found")
        return supplier


async def _get_supplier_id_for_user(user_id: int) -> Optional[int]:
    async with async_session_maker() as session:
        result = await session.execute(select(Supplier).filter(Supplier.user_id == user_id))
        supplier = result.scalars().first()
        return supplier.id if supplier else None


async def emit_supplier_notification(supplier_id: int, payload: dict) -> None:
    await sio.emit("notification:new", payload, room=_supplier_room_name(supplier_id))


async def _get_or_create_conversation(
    supplier_id: int,
    visitor_session_id: Optional[str],
    language: str,
) -> Conversation:
    async with async_session_maker() as session:
        if visitor_session_id:
            result = await session.execute(
                select(Conversation).filter(
                    Conversation.supplier_id == supplier_id,
                    Conversation.visitor_session_id == visitor_session_id,
                    Conversation.status == "active",
                )
            )
            conversation = result.scalars().first()
            if conversation:
                return conversation

        conversation = Conversation(
            supplier_id=supplier_id,
            visitor_session_id=visitor_session_id,
            conversation_type="ai_chat",
            language=language,
            status="active",
            is_escalated=0,
            message_count=0,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation


async def _save_message(
    conversation_id: int,
    supplier_id: int,
    sender_type: str,
    message_text: str,
    language: str,
    confidence_score: Optional[int] = None,
) -> None:
    async with async_session_maker() as session:
        message = ConversationMessage(
            conversation_id=conversation_id,
            supplier_id=supplier_id,
            sender_type=sender_type,
            message_text=message_text,
            language=language,
            confidence_score=confidence_score,
        )
        session.add(message)

        conversation = await session.get(Conversation, conversation_id)
        if conversation:
            conversation.message_count = (conversation.message_count or 0) + 1
            if confidence_score is not None:
                conversation.ai_confidence_score = confidence_score
        await session.commit()


async def _handle_escalation(
    supplier_id: int,
    conversation: Conversation,
    question: str,
    confidence_score: int,
) -> None:
    async with async_session_maker() as session:
        db_conversation = await session.get(Conversation, conversation.id)
        if db_conversation:
            db_conversation.is_escalated = 1
            db_conversation.status = "active"

        notification = Notification(
            supplier_id=supplier_id,
            conversation_id=conversation.id,
            notification_type="ai_handoff",
            title="AI 對話需要人工接手",
            message="有一筆買家對話信心度偏低，請盡快人工介入。",
            is_read=0,
            metadata_json=json.dumps(
                {
                    "confidence_score": confidence_score,
                    "visitor_session_id": conversation.visitor_session_id,
                    "question_preview": question[:200],
                },
                ensure_ascii=False,
            ),
        )
        session.add(notification)
        await session.commit()

    slack_service = get_slack_service()
    await slack_service.send_handoff_notification(
        supplier_id=supplier_id,
        conversation_id=conversation.id,
        visitor_session_id=conversation.visitor_session_id,
        question_preview=question,
        confidence_score=confidence_score,
    )


@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    user = await _get_user_from_token(token)
    session_payload = {"user_id": user.id} if user else {"user_id": None}
    await sio.save_session(sid, session_payload)

    if user:
        supplier_id = await _get_supplier_id_for_user(user.id)
        if supplier_id:
            await sio.enter_room(sid, _supplier_room_name(supplier_id))

    logger.info("Socket connected sid=%s user_id=%s", sid, session_payload["user_id"])
    return True


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected sid=%s", sid)


@sio.on("chat:message")
async def handle_chat_message(sid, data):
    try:
        session_data = await sio.get_session(sid)
        user_id = session_data.get("user_id")

        supplier_id = int(data.get("supplier_id"))
        question = (data.get("question") or "").strip()
        language = (data.get("language") or "auto").strip().lower()
        visitor_session_id = data.get("visitor_session_id")

        if not question:
            await sio.emit("chat:error", {"error": "Question is required"}, to=sid)
            return

        # Authenticated users (dashboard / admin) must have access to the supplier.
        # Anonymous visitors (widget embedded on buyer-facing pages) only need a
        # valid supplier_id — no token required.
        if user_id:
            async with async_session_maker() as db:
                result = await db.execute(select(User).filter(User.id == user_id))
                user = result.scalars().first()
            if not user:
                await sio.emit("chat:error", {"error": "User not found"}, to=sid)
                return
            await _assert_supplier_access(user, supplier_id)
        else:
            # Visitor (unauthenticated) — just verify the supplier exists.
            await _get_supplier(supplier_id)

        conversation = await _get_or_create_conversation(
            supplier_id=supplier_id,
            visitor_session_id=visitor_session_id,
            language=language if language != "auto" else "en",
        )

        await _save_message(
            conversation_id=conversation.id,
            supplier_id=supplier_id,
            sender_type="visitor",
            message_text=question,
            language=language if language != "auto" else "en",
        )

        rag_service = get_rag_chat_service()
        rag_result = await rag_service.answer_question(
            supplier_id=supplier_id,
            question=question,
            language=language,
            top_k=5,
        )

        answer = rag_result["answer"]
        confidence_score = rag_result["confidence_score"]
        should_escalate = rag_result["should_escalate"]

        await _save_message(
            conversation_id=conversation.id,
            supplier_id=supplier_id,
            sender_type="assistant",
            message_text=answer,
            language=rag_result["language"],
            confidence_score=confidence_score,
        )

        if should_escalate:
            await _handle_escalation(
                supplier_id=supplier_id,
                conversation=conversation,
                question=question,
                confidence_score=confidence_score,
            )

        await sio.emit(
            "chat:response",
            {
                "conversation_id": conversation.id,
                "answer": answer,
                "language": rag_result["language"],
                "confidence_score": confidence_score,
                "should_escalate": should_escalate,
                "matched_chunks": rag_result["matched_chunks"],
            },
            to=sid,
        )
    except Exception as exc:
        logger.error("Socket chat handling failed: %s", str(exc))
        await sio.emit("chat:error", {"error": str(exc)}, to=sid)


@sio.on("notification:subscribe")
async def handle_notification_subscribe(sid, data):
    try:
        session_data = await sio.get_session(sid)
        user_id = session_data.get("user_id")
        if not user_id:
            await sio.emit("notification:error", {"error": "Authentication required"}, to=sid)
            return

        supplier_id = int((data or {}).get("supplier_id"))

        async with async_session_maker() as db:
            user_result = await db.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().first()
        if not user:
            await sio.emit("notification:error", {"error": "User not found"}, to=sid)
            return

        await _assert_supplier_access(user, supplier_id)
        await sio.enter_room(sid, _supplier_room_name(supplier_id))
        await sio.emit("notification:subscribed", {"supplier_id": supplier_id}, to=sid)
    except Exception as exc:
        logger.error("Notification subscription failed: %s", str(exc))
        await sio.emit("notification:error", {"error": str(exc)}, to=sid)
