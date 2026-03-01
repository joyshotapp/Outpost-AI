"""Tests for knowledge base RAG chat endpoint"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app

client = TestClient(app)


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def first(self):
        return self._items[0] if self._items else None


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarsResult(self._items)


def _make_mock_db(execute_results=None):
    db = AsyncMock()
    queue = list(execute_results or [])

    async def _execute(*_args, **_kwargs):
        items = queue.pop(0) if queue else []
        return _ExecuteResult(items)

    db.execute = AsyncMock(side_effect=_execute)
    return db


def _override_dependencies(current_user, db):
    async def _get_user_override():
        return current_user

    async def _get_db_override():
        yield db

    app.dependency_overrides[get_current_user] = _get_user_override
    app.dependency_overrides[get_db] = _get_db_override


def setup_function():
    app.dependency_overrides = {}


def teardown_function():
    app.dependency_overrides = {}


def test_ask_rag_chat_success():
    user = SimpleNamespace(id=501, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=66, user_id=501)
    db = _make_mock_db(execute_results=[[supplier]])
    _override_dependencies(user, db)

    with patch("app.api.v1.knowledge_base.get_rag_chat_service") as mock_get_service:
        service = AsyncMock()
        service.answer_question.return_value = {
            "supplier_id": 66,
            "question": "What is your lead time?",
            "answer": "Our standard lead time is 30 days.",
            "language": "en",
            "confidence_score": 82,
            "should_escalate": False,
            "matched_chunks": [
                {
                    "id": "doc-66-1",
                    "score": 0.82,
                    "chunk_text": "Lead time 30 days",
                    "source_title": "Catalog",
                    "source_type": "catalog",
                    "chunk_index": 0,
                }
            ],
        }
        mock_get_service.return_value = service

        response = client.post(
            "/api/v1/knowledge-base/chat/ask",
            json={
                "supplier_id": 66,
                "question": "What is your lead time?",
                "language": "en",
                "top_k": 5,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] == 82
    assert data["should_escalate"] is False
