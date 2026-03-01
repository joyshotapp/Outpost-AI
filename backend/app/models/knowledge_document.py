"""Knowledge document model for supplier AI avatar RAG knowledge base"""

from sqlalchemy import Column, Integer, String, Text

from app.models.base import BaseModel


class KnowledgeDocument(BaseModel):
    """Supplier knowledge source document metadata and indexing status"""

    __tablename__ = "knowledge_documents"

    supplier_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, index=True)
    source_s3_key = Column(String(500), nullable=True)
    language = Column(String(10), default="en", nullable=False, index=True)
    content_text = Column(Text, nullable=True)

    status = Column(String(50), default="pending", nullable=False, index=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    pinecone_namespace = Column(String(255), nullable=False, index=True)
    pinecone_document_id = Column(String(255), nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<KnowledgeDocument {self.id}:{self.status}>"
