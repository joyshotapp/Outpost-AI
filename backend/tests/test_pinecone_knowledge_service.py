"""Tests for Pinecone knowledge service"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.services.pinecone_knowledge import PineconeKnowledgeService


@pytest.fixture(autouse=True)
def _set_pinecone_key():
    original = settings.PINECONE_API_KEY
    settings.PINECONE_API_KEY = "test-key"
    yield
    settings.PINECONE_API_KEY = original


def _make_mock_pinecone():
    mock_client = MagicMock()

    indexes = MagicMock()
    indexes.names.return_value = ["factory-insider-knowledge"]
    mock_client.list_indexes.return_value = indexes

    mock_index = MagicMock()
    mock_client.Index.return_value = mock_index

    mock_client.inference.embed.side_effect = [
        {"data": [{"values": [0.1, 0.2, 0.3]}]},
        {"data": [{"values": [0.4, 0.5, 0.6]}, {"values": [0.7, 0.8, 0.9]}]},
    ]

    mock_query_result = SimpleNamespace(
        matches=[
            SimpleNamespace(
                id="doc-1-chunk-0",
                score=0.91,
                metadata={
                    "chunk_text": "sample chunk",
                    "source_title": "Catalog A",
                    "source_type": "catalog",
                    "chunk_index": 0,
                },
            )
        ]
    )
    mock_index.query.return_value = mock_query_result

    return mock_client, mock_index


def test_namespace_for_supplier():
    with patch("app.services.pinecone_knowledge.Pinecone") as mock_pinecone_cls:
        mock_client, _ = _make_mock_pinecone()
        mock_pinecone_cls.return_value = mock_client

        service = PineconeKnowledgeService()
        assert service.namespace_for_supplier(42) == "supplier-42"


def test_chunk_text_generates_chunks():
    with patch("app.services.pinecone_knowledge.Pinecone") as mock_pinecone_cls:
        mock_client, _ = _make_mock_pinecone()
        mock_pinecone_cls.return_value = mock_client

        service = PineconeKnowledgeService()
        text = " ".join(["word"] * 1200)
        chunks = service.chunk_text(text)

        assert len(chunks) >= 2
        assert all(isinstance(chunk, str) and chunk for chunk in chunks)


def test_ensure_supplier_namespace():
    with patch("app.services.pinecone_knowledge.Pinecone") as mock_pinecone_cls:
        mock_client, mock_index = _make_mock_pinecone()
        mock_pinecone_cls.return_value = mock_client

        service = PineconeKnowledgeService()
        result = service.ensure_supplier_namespace(7)

        assert result["initialized"] is True
        assert result["namespace"] == "supplier-7"
        mock_index.upsert.assert_called_once()
        mock_index.delete.assert_called_once()


def test_query_supplier_knowledge_normalizes_matches():
    with patch("app.services.pinecone_knowledge.Pinecone") as mock_pinecone_cls:
        mock_client, _ = _make_mock_pinecone()
        mock_pinecone_cls.return_value = mock_client

        service = PineconeKnowledgeService()
        result = service.query_supplier_knowledge(10, "What is MOQ?", top_k=3)

        assert result["supplier_id"] == 10
        assert result["namespace"] == "supplier-10"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["chunk_text"] == "sample chunk"
