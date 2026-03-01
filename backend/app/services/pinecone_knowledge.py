"""Pinecone knowledge base service for supplier AI avatar RAG"""

import hashlib
import logging
from typing import Any, Optional

from pinecone import Pinecone, ServerlessSpec

from app.config import settings

logger = logging.getLogger(__name__)


class PineconeKnowledgeService:
    """Knowledge base service with per-supplier namespace isolation"""

    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 120

    def __init__(self):
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is required")

        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.PINECONE_DIMENSION
        self.metric = settings.PINECONE_METRIC
        self.cloud = settings.PINECONE_CLOUD
        self.region = settings.PINECONE_REGION
        self.embed_model = settings.PINECONE_EMBED_MODEL

    def namespace_for_supplier(self, supplier_id: int) -> str:
        return f"supplier-{supplier_id}"

    def ensure_index(self) -> str:
        existing_indexes = self.client.list_indexes().names()
        if self.index_name not in existing_indexes:
            self.client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(cloud=self.cloud, region=self.region),
            )
            logger.info("Created Pinecone index %s", self.index_name)
        return self.index_name

    def _index(self):
        self.ensure_index()
        return self.client.Index(self.index_name)

    def _extract_embedding_values(self, embedding_item: Any) -> list[float]:
        if hasattr(embedding_item, "values"):
            return embedding_item.values
        if isinstance(embedding_item, dict) and "values" in embedding_item:
            return embedding_item["values"]
        raise ValueError("Unexpected embedding item format from Pinecone inference")

    def embed_texts(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.inference.embed(
            model=self.embed_model,
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"},
        )

        if hasattr(response, "data"):
            items = response.data
        elif isinstance(response, dict) and "data" in response:
            items = response["data"]
        else:
            items = response

        return [self._extract_embedding_values(item) for item in items]

    def chunk_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + self.CHUNK_SIZE, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(0, end - self.CHUNK_OVERLAP)
        return chunks

    def ensure_supplier_namespace(self, supplier_id: int) -> dict[str, Any]:
        namespace = self.namespace_for_supplier(supplier_id)
        index = self._index()
        sentinel_text = f"namespace initialization for supplier {supplier_id}"
        sentinel_vector = self.embed_texts([sentinel_text], input_type="passage")[0]
        sentinel_id = f"namespace-init-{supplier_id}"

        index.upsert(
            vectors=[
                {
                    "id": sentinel_id,
                    "values": sentinel_vector,
                    "metadata": {
                        "type": "namespace_init",
                        "supplier_id": supplier_id,
                    },
                }
            ],
            namespace=namespace,
        )
        index.delete(ids=[sentinel_id], namespace=namespace)

        return {
            "supplier_id": supplier_id,
            "namespace": namespace,
            "index_name": self.index_name,
            "initialized": True,
        }

    def _document_id(self, supplier_id: int, title: str, source_type: str) -> str:
        fingerprint = hashlib.sha1(f"{supplier_id}:{title}:{source_type}".encode("utf-8")).hexdigest()[:16]
        return f"doc-{supplier_id}-{fingerprint}"

    def upsert_document_chunks(
        self,
        supplier_id: int,
        title: str,
        source_type: str,
        language: str,
        text: str,
        document_id: Optional[str] = None,
    ) -> dict[str, Any]:
        namespace = self.namespace_for_supplier(supplier_id)
        index = self._index()
        chunks = self.chunk_text(text)
        if not chunks:
            raise ValueError("No text chunks generated for knowledge document")

        embeddings = self.embed_texts(chunks, input_type="passage")
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count mismatch")

        document_key = document_id or self._document_id(supplier_id, title, source_type)

        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append(
                {
                    "id": f"{document_key}-chunk-{i}",
                    "values": embedding,
                    "metadata": {
                        "supplier_id": supplier_id,
                        "document_id": document_key,
                        "source_title": title,
                        "source_type": source_type,
                        "language": language,
                        "chunk_index": i,
                        "chunk_text": chunk,
                    },
                }
            )

        index.upsert(vectors=vectors, namespace=namespace)
        return {
            "namespace": namespace,
            "document_id": document_key,
            "chunk_count": len(vectors),
        }

    def query_supplier_knowledge(
        self,
        supplier_id: int,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        namespace = self.namespace_for_supplier(supplier_id)
        index = self._index()
        query_vector = self.embed_texts([query], input_type="query")[0]

        result = index.query(
            vector=query_vector,
            namespace=namespace,
            top_k=top_k,
            include_metadata=True,
        )

        matches = getattr(result, "matches", None)
        if matches is None and isinstance(result, dict):
            matches = result.get("matches", [])

        normalized_matches = []
        for match in matches or []:
            if isinstance(match, dict):
                metadata = match.get("metadata", {})
                normalized_matches.append(
                    {
                        "id": match.get("id"),
                        "score": float(match.get("score", 0)),
                        "chunk_text": metadata.get("chunk_text", ""),
                        "source_title": metadata.get("source_title"),
                        "source_type": metadata.get("source_type"),
                        "chunk_index": metadata.get("chunk_index"),
                    }
                )
            else:
                metadata = getattr(match, "metadata", {}) or {}
                normalized_matches.append(
                    {
                        "id": getattr(match, "id", None),
                        "score": float(getattr(match, "score", 0)),
                        "chunk_text": metadata.get("chunk_text", ""),
                        "source_title": metadata.get("source_title"),
                        "source_type": metadata.get("source_type"),
                        "chunk_index": metadata.get("chunk_index"),
                    }
                )

        return {
            "supplier_id": supplier_id,
            "namespace": namespace,
            "matches": normalized_matches,
        }


_pinecone_knowledge_service: Optional[PineconeKnowledgeService] = None


def get_pinecone_knowledge_service() -> PineconeKnowledgeService:
    global _pinecone_knowledge_service
    if _pinecone_knowledge_service is None:
        _pinecone_knowledge_service = PineconeKnowledgeService()
    return _pinecone_knowledge_service
