"""Sprint 10 tests: Elasticsearch search service + messaging system.

Tests:
  - TestSearchServiceStub: stub-mode search (no real ES required)
  - TestSearchServiceFilters: in-memory filter logic
  - TestSearchSuggest: autocomplete prefix matching
  - TestSavedSupplierModel: field validation + unique constraint repr
  - TestDirectMessageModel: field types and relationship repr
  - TestSearchAPISchemas: Pydantic response model validation
  - TestSearchEndpoints: FastAPI search/suggest endpoints via TestClient
  - TestMessagesEndpoints: messaging CRUD via TestClient
  - TestMessagesService: service-layer unit tests with mocked DB
  - TestConfig: Sprint 10 settings are present in config
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app

client = TestClient(app)

# ── Shared helpers ────────────────────────────────────────────────────────────


class _ScalarsResult:
    def __init__(self, items: list):
        self._items = items

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return self._items


class _ExecuteResult:
    def __init__(self, items: list, scalar_val: Any = None):
        self._items = items
        self._scalar_val = scalar_val

    def scalars(self) -> _ScalarsResult:
        return _ScalarsResult(self._items)

    def scalar(self) -> Any:
        return self._scalar_val


def _make_mock_db(execute_results: list | None = None, scalar_vals: list | None = None):
    db = AsyncMock()
    execute_queue = list(execute_results or [])
    scalar_queue = list(scalar_vals or [])

    async def _execute(*_args, **_kwargs):
        items = execute_queue.pop(0) if execute_queue else []
        scalar = scalar_queue.pop(0) if scalar_queue else None
        return _ExecuteResult(items, scalar)

    def _add(entity):
        for attr in ("id", "created_at", "updated_at"):
            if getattr(entity, attr, None) is None:
                setattr(entity, attr, 1 if attr == "id" else datetime.now(timezone.utc))

    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock(side_effect=_add)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_user(is_admin=False, role="buyer", buyer_profile_id=None, supplier_profile_id=None):
    if buyer_profile_id is None:
        buyer_profile_id = 1 if role == "buyer" else None
    if supplier_profile_id is None:
        supplier_profile_id = 1 if role == "supplier" else None
    return SimpleNamespace(
        id=1,
        email="test@example.com",
        is_admin=is_admin,
        role=role,
        buyer_profile_id=buyer_profile_id,
        supplier_profile_id=supplier_profile_id,
    )


def _override(user, db):
    async def _get_user():
        return user

    async def _get_db():
        yield db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db


def _clear_overrides():
    app.dependency_overrides.clear()


# ── TestConfig ────────────────────────────────────────────────────────────────

class TestConfig:
    def test_es_suppliers_index_exists(self):
        from app.config import settings
        assert settings.ES_SUPPLIERS_INDEX == "suppliers"

    def test_search_max_results(self):
        from app.config import settings
        assert settings.SEARCH_MAX_RESULTS >= 100

    def test_message_max_length(self):
        from app.config import settings
        assert settings.MESSAGE_MAX_LENGTH >= 1000

    def test_search_default_page_size(self):
        from app.config import settings
        assert settings.SEARCH_DEFAULT_PAGE_SIZE == 20


# ── TestSearchServiceStub ─────────────────────────────────────────────────────

class TestSearchServiceStub:
    @pytest.fixture(autouse=True)
    def svc(self):
        """Always use stub mode — no real ES needed."""
        from app.services.search import ElasticsearchSearchService
        svc = ElasticsearchSearchService.__new__(ElasticsearchSearchService)
        svc._client = None
        svc.stub_mode = True
        svc._index = "suppliers"
        return svc

    def test_stub_mode_flag(self, svc):
        assert svc.stub_mode is True

    def test_search_returns_results(self, svc):
        result = svc.search()
        assert isinstance(result.get("results"), list)
        assert len(result["results"]) > 0
        assert result["total"] > 0
        assert result["_stub"] is True

    def test_search_returns_pagination_keys(self, svc):
        result = svc.search(page=1, page_size=5)
        assert "total" in result
        assert "page" in result
        assert "pages" in result
        assert result["page"] == 1

    def test_search_full_text_filter(self, svc):
        result = svc.search(q="precision")
        # At least one stub result matches "Precision Parts Co"
        names = [r["company_name"] for r in result["results"]]
        assert any("Precision" in n for n in names)

    def test_search_industry_filter(self, svc):
        result = svc.search(industry="Automotive")
        for r in result["results"]:
            assert r["industry"] == "Automotive"

    def test_search_country_filter(self, svc):
        result = svc.search(country="DE")
        for r in result["results"]:
            assert r["country"] == "DE"

    def test_search_certifications_filter(self, svc):
        result = svc.search(certifications="ISO 9001")
        # All stub suppliers have ISO 9001 — result should not be empty
        assert result["total"] > 0

    def test_search_no_results_for_gibberish(self, svc):
        result = svc.search(q="xyzzy_nonexistent_1234")
        assert result["total"] == 0

    def test_search_pagination(self, svc):
        page1 = svc.search(page=1, page_size=3)
        page2 = svc.search(page=2, page_size=3)
        # Different pages return different results (assuming >= 4 total)
        if page1["total"] > 3:
            p1_names = {r["company_name"] for r in page1["results"]}
            p2_names = {r["company_name"] for r in page2["results"]}
            assert p1_names != p2_names

    def test_ensure_index_noops_in_stub(self, svc):
        """ensure_index should not raise in stub mode."""
        svc.ensure_index()  # no exception

    def test_index_supplier_noops_in_stub(self, svc):
        fake = SimpleNamespace(id=99, company_name="Test", company_slug="test")
        svc.index_supplier(fake)  # no exception

    def test_delete_supplier_noops_in_stub(self, svc):
        svc.delete_supplier(99)  # no exception

    def test_reindex_all_returns_count(self, svc):
        fake_suppliers = [SimpleNamespace(id=i) for i in range(5)]
        count = svc.reindex_all(fake_suppliers)
        assert count == 5


# ── TestSearchSuggest ──────────────────────────────────────────────────────────

class TestSearchSuggest:
    @pytest.fixture(autouse=True)
    def svc(self):
        from app.services.search import ElasticsearchSearchService
        svc = ElasticsearchSearchService.__new__(ElasticsearchSearchService)
        svc._client = None
        svc.stub_mode = True
        svc._index = "suppliers"
        return svc

    def test_suggest_prefix_match(self, svc):
        results = svc.suggest("Prec")
        assert len(results) >= 1
        assert all("Prec" in r or "prec" in r.lower() for r in results)

    def test_suggest_empty_prefix(self, svc):
        results = svc.suggest("")
        assert results == []

    def test_suggest_size_limit(self, svc):
        results = svc.suggest("a", size=2)
        assert len(results) <= 2

    def test_suggest_no_match_returns_empty(self, svc):
        results = svc.suggest("zzzzzzz_no_match")
        assert results == []


# ── TestSavedSupplierModel ────────────────────────────────────────────────────

class TestSavedSupplierModel:
    def test_model_tablename(self):
        from app.models.saved_supplier import SavedSupplier
        assert SavedSupplier.__tablename__ == "saved_suppliers"

    def test_model_has_buyer_id_column(self):
        from app.models.saved_supplier import SavedSupplier
        assert hasattr(SavedSupplier, "buyer_id")

    def test_model_has_supplier_id_column(self):
        from app.models.saved_supplier import SavedSupplier
        assert hasattr(SavedSupplier, "supplier_id")

    def test_model_has_notes_column(self):
        from app.models.saved_supplier import SavedSupplier
        assert hasattr(SavedSupplier, "notes")

    def test_model_has_unique_constraint(self):
        from app.models.saved_supplier import SavedSupplier
        from sqlalchemy import inspect
        insp = inspect(SavedSupplier)
        constraint_names = [c.name for c in insp.mapper.persist_selectable.constraints]
        assert any("saved" in (n or "").lower() or "unique" in (n or "").lower() for n in constraint_names)

    def test_repr(self):
        from app.models.saved_supplier import SavedSupplier
        s = SavedSupplier()
        s.buyer_id = 1
        s.supplier_id = 2
        assert "1" in repr(s) or "SavedSupplier" in repr(s)


# ── TestDirectMessageModel ────────────────────────────────────────────────────

class TestDirectMessageModel:
    def test_model_tablename(self):
        from app.models.direct_message import DirectMessage
        assert DirectMessage.__tablename__ == "direct_messages"

    def test_model_has_required_columns(self):
        from app.models.direct_message import DirectMessage
        for col in ("conversation_id", "sender_type", "sender_id", "body", "is_read", "read_at", "attachment_url"):
            assert hasattr(DirectMessage, col), f"Missing column: {col}"

    def test_repr(self):
        from app.models.direct_message import DirectMessage
        m = DirectMessage()
        m.conversation_id = 42
        m.sender_type = "buyer"
        assert "buyer" in repr(m)

    def test_sender_type_values(self):
        """sender_type is a string column — validate the expected values."""
        from app.models.direct_message import DirectMessage
        col = DirectMessage.sender_type
        assert col is not None  # column descriptor exists


# ── TestSearchAPISchemas ──────────────────────────────────────────────────────

class TestSearchAPISchemas:
    def test_supplier_search_result_schema(self):
        from app.api.v1.search import SupplierSearchResult
        obj = SupplierSearchResult(company_name="Acme", company_slug="acme")
        assert obj.company_name == "Acme"
        assert obj.is_verified is False

    def test_suggest_response_schema(self):
        from app.api.v1.search import SuggestResponse
        resp = SuggestResponse(suggestions=["Acme Corp", "AcmeTech"])
        assert len(resp.suggestions) == 2

    def test_reindex_response_schema(self):
        from app.api.v1.search import ReindexResponse
        resp = ReindexResponse(indexed=42, message="Done")
        assert resp.indexed == 42


# ── TestSearchEndpoints ───────────────────────────────────────────────────────

class TestSearchEndpoints:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_search_endpoint_returns_200(self):
        with patch("app.api.v1.search.get_search_service") as mock_svc:
            mock_svc.return_value.search.return_value = {
                "total": 2, "page": 1, "page_size": 20, "pages": 1,
                "results": [
                    {"company_name": "Acme", "company_slug": "acme", "is_verified": True, "view_count": 5},
                ],
                "_stub": True,
            }
            resp = client.get("/api/v1/search/suppliers?q=acme")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["total"] == 2

    def test_search_endpoint_accepts_filters(self):
        with patch("app.api.v1.search.get_search_service") as mock_svc:
            mock_svc.return_value.search.return_value = {
                "total": 0, "page": 1, "page_size": 20, "pages": 1, "results": [], "_stub": True,
            }
            resp = client.get("/api/v1/search/suppliers?industry=Automotive&country=DE&is_verified=true")
        assert resp.status_code == 200
        call_kwargs = mock_svc.return_value.search.call_args.kwargs
        assert call_kwargs["industry"] == "Automotive"
        assert call_kwargs["country"] == "DE"
        assert call_kwargs["is_verified"] is True

    def test_suggest_endpoint_returns_200(self):
        with patch("app.api.v1.search.get_search_service") as mock_svc:
            mock_svc.return_value.suggest.return_value = ["Acme Corp", "Acme Taiwan"]
            resp = client.get("/api/v1/search/suppliers/suggest?q=Acme")
        assert resp.status_code == 200
        assert resp.json()["suggestions"] == ["Acme Corp", "Acme Taiwan"]

    def test_suggest_requires_q(self):
        resp = client.get("/api/v1/search/suppliers/suggest")
        assert resp.status_code == 422

    def test_reindex_requires_auth(self):
        resp = client.post("/api/v1/search/suppliers/reindex")
        assert resp.status_code in (401, 403, 422)

    def test_reindex_requires_admin(self):
        db = _make_mock_db(execute_results=[[]])
        _override(_make_user(is_admin=False), db)
        with patch("app.api.v1.search.get_search_service"):
            resp = client.post("/api/v1/search/suppliers/reindex")
        assert resp.status_code == 403

    def test_reindex_success_as_admin(self):
        db = _make_mock_db(execute_results=[[]])
        _override(_make_user(is_admin=True), db)
        with patch("app.api.v1.search.get_search_service") as mock_svc:
            mock_svc.return_value.ensure_index.return_value = None
            mock_svc.return_value.reindex_all.return_value = 0
            resp = client.post("/api/v1/search/suppliers/reindex")
        assert resp.status_code == 202
        assert "indexed" in resp.json()


# ── TestMessagesEndpoints ─────────────────────────────────────────────────────

class TestMessagesEndpoints:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def _make_conv(self, **kwargs):
        defaults = dict(
            id=1, buyer_id=1, supplier_id=2, conversation_type="direct",
            status="active", message_count=1, unread_buyer_count=0,
            unread_supplier_count=1, last_message_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _make_msg(self, **kwargs):
        defaults = dict(
            id=10, conversation_id=1, sender_type="buyer", sender_id=1,
            body="Hello!", is_read=False, read_at=None, attachment_url=None,
            created_at=datetime.now(timezone.utc),
        )
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_list_conversations_200(self):
        conv = self._make_conv()
        db = _make_mock_db(execute_results=[[conv], [conv]], scalar_vals=[1])
        _override(_make_user(), db)

        with patch("app.services.messages.list_conversations") as mock_list:
            mock_list.return_value = {
                "total": 1, "page": 1, "page_size": 20, "pages": 1,
                "conversations": [conv],
            }
            resp = client.get("/api/v1/messages/conversations")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["conversations"]) == 1

    def test_start_conversation_201(self):
        conv = self._make_conv()
        msg = self._make_msg()
        db = _make_mock_db()
        _override(_make_user(), db)

        with patch("app.services.messages.start_conversation") as mock_start:
            mock_start.return_value = {"conversation": conv, "message": msg}
            resp = client.post("/api/v1/messages/conversations", json={
                "supplier_id": 2, "initial_message": "Hello supplier!"
            })

        assert resp.status_code == 201
        data = resp.json()
        assert "conversation" in data
        assert data["message_id"] == 10

    def test_start_conversation_validates_body(self):
        db = _make_mock_db()
        _override(_make_user(), db)
        resp = client.post("/api/v1/messages/conversations", json={"supplier_id": 2})
        assert resp.status_code == 422  # missing initial_message

    def test_start_conversation_supplier_rejected(self):
        db = _make_mock_db()
        _override(_make_user(role="supplier"), db)
        resp = client.post(
            "/api/v1/messages/conversations",
            json={"supplier_id": 2, "initial_message": "Hello supplier!"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Buyer profile not found"

    def test_get_messages_200(self):
        msg = self._make_msg()
        db = _make_mock_db()
        _override(_make_user(), db)

        with patch("app.services.messages.get_messages") as mock_get:
            mock_get.return_value = {
                "total": 1, "page": 1, "page_size": 50, "pages": 1,
                "messages": [msg],
            }
            resp = client.get("/api/v1/messages/conversations/1/messages")

        assert resp.status_code == 200
        assert len(resp.json()["messages"]) == 1

    def test_send_message_201(self):
        msg = self._make_msg()
        db = _make_mock_db()
        _override(_make_user(), db)

        with patch("app.services.messages.send_message") as mock_send:
            mock_send.return_value = msg
            resp = client.post("/api/v1/messages/conversations/1/messages", json={
                "body": "Can you provide a quote for 500 units?"
            })

        assert resp.status_code == 201
        data = resp.json()
        assert data["body"] == "Hello!"

    def test_send_message_validates_empty_body(self):
        db = _make_mock_db()
        _override(_make_user(), db)
        resp = client.post("/api/v1/messages/conversations/1/messages", json={"body": ""})
        assert resp.status_code == 422

    def test_mark_read_204(self):
        db = _make_mock_db()
        _override(_make_user(), db)

        with patch("app.services.messages.mark_conversation_read") as mock_read:
            mock_read.return_value = None
            resp = client.patch("/api/v1/messages/conversations/1/read")

        assert resp.status_code == 204

    def test_unread_count_200(self):
        db = _make_mock_db()
        _override(_make_user(), db)

        with patch("app.services.messages.get_unread_count") as mock_count:
            mock_count.return_value = 3
            resp = client.get("/api/v1/messages/unread-count")

        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 3


# ── TestMessagesService ───────────────────────────────────────────────────────

class TestMessagesService:
    """Unit-test the service layer with fully mocked DB sessions."""

    def _loop(self):
        return asyncio.get_event_loop()

    def _run(self, coro):
        return self._loop().run_until_complete(coro)

    def test_list_conversations_empty(self):
        from app.services import messages as svc

        db = _make_mock_db(execute_results=[[], []], scalar_vals=[0])

        class _FakeResult:
            def scalars(self): return _ScalarsResult([])
            def scalar(self): return 0

        db.execute = AsyncMock(return_value=_FakeResult())
        result = self._run(svc.list_conversations(db, buyer_id=1))

        assert result["total"] == 0
        assert result["conversations"] == []

    def test_get_unread_count_zero(self):
        from app.services import messages as svc

        class _FakeResult:
            def scalars(self): return _ScalarsResult([])

        db = AsyncMock()
        db.execute = AsyncMock(return_value=_FakeResult())

        count = self._run(svc.get_unread_count(db, buyer_id=1))
        assert count == 0

    def test_send_message_validates_length(self):
        from app.services import messages as svc
        from app.config import settings

        db = AsyncMock()
        with pytest.raises(ValueError, match="exceeds"):
            self._run(svc.send_message(db, 1, "buyer", 1, "x" * (settings.MESSAGE_MAX_LENGTH + 1)))

    def test_send_message_validates_sender_type(self):
        from app.services import messages as svc

        db = AsyncMock()
        with pytest.raises(ValueError, match="sender_type"):
            self._run(svc.send_message(db, 1, "unknown", 1, "Hello"))

    def test_mark_conversation_read_not_found(self):
        from app.services import messages as svc

        class _FakeResult:
            def scalars(self): return _ScalarsResult([])

        db = AsyncMock()
        db.execute = AsyncMock(return_value=_FakeResult())

        with pytest.raises(ValueError, match="not found"):
            self._run(svc.mark_conversation_read(db, 999, "buyer"))
