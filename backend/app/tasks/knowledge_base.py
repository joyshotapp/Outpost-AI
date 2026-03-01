"""Celery tasks for supplier knowledge base ingestion pipeline"""

import asyncio
import logging
from typing import Optional

from celery import shared_task

from app.database import async_session_maker
from app.models import KnowledgeDocument
from app.services.claude import get_claude_service
from app.services.pinecone_knowledge import get_pinecone_knowledge_service

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery worker context.

    Celery workers run in threads that may have no event loop or a closed one,
    so we always create a fresh loop via asyncio.run().
    """
    return asyncio.run(coro)


async def _fetch_document(document_id: int) -> Optional[KnowledgeDocument]:
    async with async_session_maker() as session:
        return await session.get(KnowledgeDocument, document_id)


async def _update_document_status(
    document_id: int,
    status: str,
    chunk_count: Optional[int] = None,
    pinecone_document_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    async with async_session_maker() as session:
        document = await session.get(KnowledgeDocument, document_id)
        if not document:
            return
        document.status = status
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if pinecone_document_id is not None:
            document.pinecone_document_id = pinecone_document_id
        document.error_message = error_message
        await session.commit()


async def _resolve_document_text(document: KnowledgeDocument) -> str:
    if document.content_text and document.content_text.strip():
        return document.content_text

    if not document.source_s3_key:
        raise ValueError("Knowledge document has no text_content or source_s3_key")

    if document.source_s3_key.lower().endswith(".pdf"):
        claude_service = get_claude_service()
        pdf_bytes = await claude_service.extract_pdf_from_s3(document.source_s3_key)
        if not pdf_bytes:
            raise ValueError("Failed to fetch PDF bytes from S3")

        images = await claude_service.convert_pdf_to_images(pdf_bytes)
        if not images:
            raise ValueError("Failed to convert PDF to images")

        vision_result = await claude_service.analyze_pdf_with_vision(images)
        if not vision_result.get("success"):
            raise ValueError("Failed to extract text from PDF with Claude Vision")

        vision_data = vision_result.get("vision_data")
        return str(vision_data)

    claude_service = get_claude_service()
    file_bytes = await claude_service.extract_pdf_from_s3(document.source_s3_key)
    if not file_bytes:
        raise ValueError("Failed to fetch source file from S3")

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Source file is not UTF-8 text") from exc


@shared_task(bind=True, max_retries=3)
def ingest_knowledge_document(self, document_id: int) -> dict:
    try:
        document = _run_async(_fetch_document(document_id))
        if not document:
            return {"success": False, "error": "Knowledge document not found"}

        _run_async(_update_document_status(document_id, status="processing", error_message=None))

        content_text = _run_async(_resolve_document_text(document))

        pinecone_service = get_pinecone_knowledge_service()
        pinecone_service.ensure_supplier_namespace(document.supplier_id)
        result = pinecone_service.upsert_document_chunks(
            supplier_id=document.supplier_id,
            title=document.title,
            source_type=document.source_type,
            language=document.language,
            text=content_text,
        )

        _run_async(
            _update_document_status(
                document_id,
                status="indexed",
                chunk_count=result["chunk_count"],
                pinecone_document_id=result["document_id"],
                error_message=None,
            )
        )

        return {
            "success": True,
            "document_id": document_id,
            "pinecone_document_id": result["document_id"],
            "chunk_count": result["chunk_count"],
            "namespace": result["namespace"],
        }
    except Exception as exc:
        logger.error("Knowledge document ingestion failed for %s: %s", document_id, str(exc))
        _run_async(_update_document_status(document_id, status="failed", error_message=str(exc)))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
