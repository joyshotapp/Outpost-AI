"""Knowledge base API endpoints for Sprint 4 supplier AI avatar"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import KnowledgeDocument, Supplier, User
from app.schemas import (
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentResponse,
    KnowledgeNamespaceInitResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeSupplierContextResponse,
    RAGChatRequest,
    RAGChatResponse,
)
from app.services.pinecone_knowledge import get_pinecone_knowledge_service
from app.services.rag_chat import get_rag_chat_service
from app.tasks.knowledge_base import ingest_knowledge_document

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


async def _assert_supplier_access(
    supplier_id: int,
    current_user: User,
    db: AsyncSession,
) -> Supplier:
    supplier_result = await db.execute(
        select(Supplier).filter(Supplier.id == supplier_id)
    )
    supplier = supplier_result.scalars().first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    if current_user.role.value != "admin" and supplier.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this supplier knowledge base",
        )

    return supplier


@router.post(
    "/suppliers/{supplier_id}/namespace/init",
    response_model=KnowledgeNamespaceInitResponse,
)
async def initialize_supplier_namespace(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeNamespaceInitResponse:
    await _assert_supplier_access(supplier_id, current_user, db)
    pinecone_service = get_pinecone_knowledge_service()
    result = pinecone_service.ensure_supplier_namespace(supplier_id)
    return KnowledgeNamespaceInitResponse(**result)


@router.get("/me", response_model=KnowledgeSupplierContextResponse)
async def get_my_knowledge_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSupplierContextResponse:
    if current_user.role.value != "supplier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can access knowledge context",
        )

    supplier_result = await db.execute(select(Supplier).filter(Supplier.user_id == current_user.id))
    supplier = supplier_result.scalars().first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier profile not found",
        )

    pinecone_service = get_pinecone_knowledge_service()
    return KnowledgeSupplierContextResponse(
        supplier_id=supplier.id,
        namespace=pinecone_service.namespace_for_supplier(supplier.id),
    )


@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_document(
    request: KnowledgeDocumentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeDocumentResponse:
    await _assert_supplier_access(request.supplier_id, current_user, db)

    if not request.text_content and not request.source_s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text_content or source_s3_key must be provided",
        )

    pinecone_service = get_pinecone_knowledge_service()
    namespace = pinecone_service.namespace_for_supplier(request.supplier_id)

    document = KnowledgeDocument(
        supplier_id=request.supplier_id,
        title=request.title,
        source_type=request.source_type,
        source_s3_key=request.source_s3_key,
        language=request.language,
        content_text=request.text_content,
        status="pending",
        chunk_count=0,
        pinecone_namespace=namespace,
        pinecone_document_id="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    ingest_knowledge_document.delay(document.id)

    return KnowledgeDocumentResponse.model_validate(document)


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_knowledge_documents(
    supplier_id: int = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeDocumentResponse]:
    await _assert_supplier_access(supplier_id, current_user, db)

    query = select(KnowledgeDocument).filter(KnowledgeDocument.supplier_id == supplier_id)
    if status_filter:
        query = query.filter(KnowledgeDocument.status == status_filter)

    result = await db.execute(query.order_by(KnowledgeDocument.created_at.desc()))
    documents = result.scalars().all()
    return [KnowledgeDocumentResponse.model_validate(d) for d in documents]


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge_base(
    request: KnowledgeQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeQueryResponse:
    await _assert_supplier_access(request.supplier_id, current_user, db)
    pinecone_service = get_pinecone_knowledge_service()
    result = pinecone_service.query_supplier_knowledge(
        supplier_id=request.supplier_id,
        query=request.query,
        top_k=request.top_k,
    )
    return KnowledgeQueryResponse(**result)


@router.post("/chat/ask", response_model=RAGChatResponse)
async def ask_rag_chat(
    request: RAGChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RAGChatResponse:
    await _assert_supplier_access(request.supplier_id, current_user, db)
    rag_service = get_rag_chat_service()
    result = await rag_service.answer_question(
        supplier_id=request.supplier_id,
        question=request.question,
        language=request.language,
        top_k=request.top_k,
    )
    return RAGChatResponse(**result)
