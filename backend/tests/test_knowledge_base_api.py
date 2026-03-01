"""Tests for knowledge base API endpoints"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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

    def all(self):
        return self._items


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

    def _add(entity):
        if getattr(entity, "id", None) is None:
            entity.id = 1
        if getattr(entity, "created_at", None) is None:
            entity.created_at = datetime.utcnow()
        if getattr(entity, "updated_at", None) is None:
            entity.updated_at = datetime.utcnow()

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock(side_effect=_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
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


def test_initialize_namespace_success():
    user = SimpleNamespace(id=10, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=5, user_id=10)
    db = _make_mock_db(execute_results=[[supplier]])
    _override_dependencies(user, db)

    with patch("app.api.v1.knowledge_base.get_pinecone_knowledge_service") as mock_get_service:
        service = MagicMock()
        service.ensure_supplier_namespace.return_value = {
            "supplier_id": 5,
            "namespace": "supplier-5",
            "index_name": "factory-insider-knowledge",
            "initialized": True,
        }
        mock_get_service.return_value = service

        response = client.post("/api/v1/knowledge-base/suppliers/5/namespace/init")

    assert response.status_code == 200
    data = response.json()
    assert data["namespace"] == "supplier-5"
    assert data["initialized"] is True


def test_create_knowledge_document_success():
    user = SimpleNamespace(id=11, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=6, user_id=11)
    db = _make_mock_db(execute_results=[[supplier]])
    _override_dependencies(user, db)

    with patch("app.api.v1.knowledge_base.get_pinecone_knowledge_service") as mock_get_service, \
         patch("app.api.v1.knowledge_base.ingest_knowledge_document.delay") as mock_delay:
        service = MagicMock()
        service.namespace_for_supplier.return_value = "supplier-6"
        mock_get_service.return_value = service

        response = client.post(
            "/api/v1/knowledge-base/documents",
            json={
                "supplier_id": 6,
                "title": "Product Catalog",
                "source_type": "catalog",
                "text_content": "CNC machining capabilities...",
                "language": "en",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["supplier_id"] == 6
    assert data["status"] == "pending"
    mock_delay.assert_called_once_with(1)


def test_query_knowledge_base_success():
    user = SimpleNamespace(id=12, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=7, user_id=12)
    db = _make_mock_db(execute_results=[[supplier]])
    _override_dependencies(user, db)

    with patch("app.api.v1.knowledge_base.get_pinecone_knowledge_service") as mock_get_service:
        service = MagicMock()
        service.query_supplier_knowledge.return_value = {
            "supplier_id": 7,
            "namespace": "supplier-7",
            "matches": [
                {
                    "id": "doc-7-abc-chunk-0",
                    "score": 0.9,
                    "chunk_text": "We support ISO9001 production.",
                    "source_title": "FAQ",
                    "source_type": "faq",
                    "chunk_index": 0,
                }
            ],
        }
        mock_get_service.return_value = service

        response = client.post(
            "/api/v1/knowledge-base/query",
            json={
                "supplier_id": 7,
                "query": "Do you support ISO?",
                "top_k": 3,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["namespace"] == "supplier-7"
    assert len(data["matches"]) == 1
    assert data["matches"][0]["source_type"] == "faq"


def test_get_my_knowledge_context_success():
    user = SimpleNamespace(id=13, role=SimpleNamespace(value="supplier"))
    supplier = SimpleNamespace(id=8, user_id=13)
    db = _make_mock_db(execute_results=[[supplier]])
    _override_dependencies(user, db)

    with patch("app.api.v1.knowledge_base.get_pinecone_knowledge_service") as mock_get_service:
        service = MagicMock()
        service.namespace_for_supplier.return_value = "supplier-8"
        mock_get_service.return_value = service

        response = client.get("/api/v1/knowledge-base/me")

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == 8
    assert data["namespace"] == "supplier-8"
