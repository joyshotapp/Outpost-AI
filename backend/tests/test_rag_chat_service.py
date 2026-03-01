"""Tests for RAG chat service"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.rag_chat import RAGChatService


@pytest.mark.asyncio
async def test_answer_question_with_context_and_grounded_answer():
    with patch("app.services.rag_chat.get_pinecone_knowledge_service") as mock_get_pinecone, \
         patch("app.services.rag_chat.get_claude_service") as mock_get_claude:
        pinecone = MagicMock()
        pinecone.query_supplier_knowledge.return_value = {
            "matches": [
                {
                    "id": "doc-1",
                    "score": 0.87,
                    "chunk_text": "MOQ is 500 pcs.",
                    "source_title": "FAQ",
                    "source_type": "faq",
                    "chunk_index": 0,
                }
            ]
        }
        mock_get_pinecone.return_value = pinecone

        claude = MagicMock()
        claude.model = "claude-3-5-sonnet-latest"
        claude.tracker = MagicMock()
        claude.client.messages.create.return_value = MagicMock(
            usage=MagicMock(input_tokens=10, output_tokens=12),
            content=[MagicMock(text='{"answer":"Our MOQ is 500 pcs.","grounded":true,"missing_info":[]}')],
        )
        mock_get_claude.return_value = claude

        service = RAGChatService()
        result = await service.answer_question(7, "What is MOQ?", "en", 5)

    assert result["confidence_score"] >= 70
    assert result["should_escalate"] is False
    assert "500" in result["answer"]


@pytest.mark.asyncio
async def test_answer_question_low_confidence_escalates():
    with patch("app.services.rag_chat.get_pinecone_knowledge_service") as mock_get_pinecone, \
         patch("app.services.rag_chat.get_claude_service") as mock_get_claude:
        pinecone = MagicMock()
        pinecone.query_supplier_knowledge.return_value = {"matches": []}
        mock_get_pinecone.return_value = pinecone

        claude = MagicMock()
        mock_get_claude.return_value = claude

        service = RAGChatService()
        result = await service.answer_question(8, "Do you support ISO13485?", "en", 5)

    assert result["confidence_score"] == 0
    assert result["should_escalate"] is True
    assert "human sales representative" in result["answer"]


@pytest.mark.asyncio
async def test_answer_question_multilingual_query_translates_for_retrieval():
    with patch("app.services.rag_chat.get_pinecone_knowledge_service") as mock_get_pinecone, \
         patch("app.services.rag_chat.get_claude_service") as mock_get_claude:
        pinecone = MagicMock()
        pinecone.query_supplier_knowledge.return_value = {
            "matches": [
                {
                    "id": "doc-2",
                    "score": 0.8,
                    "chunk_text": "Delivery lead time is 20 days.",
                    "source_title": "Catalog",
                    "source_type": "catalog",
                    "chunk_index": 0,
                }
            ]
        }
        mock_get_pinecone.return_value = pinecone

        claude = MagicMock()
        claude.model = "claude-3-5-sonnet-latest"
        claude.tracker = MagicMock()
        claude.client.messages.create.side_effect = [
            MagicMock(
                usage=MagicMock(input_tokens=5, output_tokens=5),
                content=[MagicMock(text='{"language":"de"}')],
            ),
            MagicMock(
                usage=MagicMock(input_tokens=8, output_tokens=10),
                content=[MagicMock(text="What is your delivery lead time?")],
            ),
            MagicMock(
                usage=MagicMock(input_tokens=20, output_tokens=30),
                content=[MagicMock(text='{"answer":"Unsere Lieferzeit beträgt 20 Tage.","grounded":true,"missing_info":[]}')],
            ),
        ]
        mock_get_claude.return_value = claude

        service = RAGChatService()
        result = await service.answer_question(9, "Wie lang ist die Lieferzeit?", "de", 5)

    assert result["language"] == "de"
    assert "20" in result["answer"]
    pinecone.query_supplier_knowledge.assert_called_once()
    kwargs = pinecone.query_supplier_knowledge.call_args.kwargs
    assert kwargs["query"] == "What is your delivery lead time?"


@pytest.mark.asyncio
async def test_answer_question_auto_language_uses_detected_language():
    with patch("app.services.rag_chat.get_pinecone_knowledge_service") as mock_get_pinecone, \
         patch("app.services.rag_chat.get_claude_service") as mock_get_claude:
        pinecone = MagicMock()
        pinecone.query_supplier_knowledge.return_value = {
            "matches": [
                {
                    "id": "doc-3",
                    "score": 0.82,
                    "chunk_text": "Lead time is 15 days.",
                    "source_title": "FAQ",
                    "source_type": "faq",
                    "chunk_index": 0,
                }
            ]
        }
        mock_get_pinecone.return_value = pinecone

        claude = MagicMock()
        claude.model = "claude-3-5-sonnet-latest"
        claude.tracker = MagicMock()
        claude.client.messages.create.side_effect = [
            MagicMock(
                usage=MagicMock(input_tokens=5, output_tokens=5),
                content=[MagicMock(text='{"language":"ja"}')],
            ),
            MagicMock(
                usage=MagicMock(input_tokens=10, output_tokens=10),
                content=[MagicMock(text="What is your lead time?")],
            ),
            MagicMock(
                usage=MagicMock(input_tokens=20, output_tokens=30),
                content=[MagicMock(text='{"answer":"リードタイムは15日です。","grounded":true,"missing_info":[]}')],
            ),
        ]
        mock_get_claude.return_value = claude

        service = RAGChatService()
        result = await service.answer_question(11, "納期はどれくらいですか？", "auto", 5)

    assert result["language"] == "ja"
    assert result["should_escalate"] is False
