"""Tests for RFQ API endpoints"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import RFQ

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
    execute_results = execute_results or []
    queue = list(execute_results)

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


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


class TestRFQAPI:
    """Test RFQ API endpoints"""

    def test_create_rfq_without_attachment(self):
        """Test creating an RFQ without attachment"""
        buyer_user = SimpleNamespace(id=100, role="buyer")
        db = _make_mock_db()
        _override_dependencies(buyer_user, db)

        response = client.post(
            "/api/v1/rfqs",
            data={
                "title": "CNC Parts",
                "description": "Need CNC aluminum parts",
                "quantity": "500",
                "unit": "pcs",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "CNC Parts"
        assert data["buyer_id"] == 100
        assert data["attachment_url"] is None
        db.add.assert_called_once()
        db.commit.assert_called()

    def test_create_rfq_with_pdf_attachment(self):
        """Test creating an RFQ with PDF attachment"""
        buyer_user = SimpleNamespace(id=101, role="buyer")
        db = _make_mock_db()
        _override_dependencies(buyer_user, db)

        with patch("app.api.v1.rfqs.S3Service.upload_rfq_attachment", new_callable=AsyncMock) as mock_upload, \
             patch("app.api.v1.rfqs.get_claude_service") as mock_get_claude:
            mock_upload.return_value = "https://s3.example.com/rfq/test.pdf"
            mock_claude_service = MagicMock()
            mock_claude_service.analyze_rfq_pdf = AsyncMock(return_value={"success": True, "summary": "ok"})
            mock_get_claude.return_value = mock_claude_service

            response = client.post(
                "/api/v1/rfqs",
                data={
                    "title": "Injection Mold",
                    "description": "Need mold with PDF drawing",
                },
                files={
                    "attachment": ("drawing.pdf", b"%PDF-1.4 test", "application/pdf"),
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["attachment_url"] == "https://s3.example.com/rfq/test.pdf"
        mock_upload.assert_awaited_once()
        mock_claude_service.analyze_rfq_pdf.assert_awaited_once()

    def test_create_rfq_as_supplier_fails(self):
        """Test that suppliers cannot submit RFQs"""
        supplier_user = SimpleNamespace(id=200, role="supplier")
        db = _make_mock_db()
        _override_dependencies(supplier_user, db)

        response = client.post(
            "/api/v1/rfqs",
            data={"title": "Should Fail", "description": "Suppliers cannot submit"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Only buyers can submit RFQs"

    def test_list_rfqs_buyer_sees_own(self):
        """Test that buyers only see their own RFQs"""
        buyer_user = SimpleNamespace(id=300, role="buyer")

        rfq = RFQ(
            id=11,
            buyer_id=300,
            title="Buyer RFQ",
            description="My RFQ",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db = _make_mock_db(execute_results=[[rfq]])
        _override_dependencies(buyer_user, db)

        response = client.get("/api/v1/rfqs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 11
        assert data[0]["buyer_id"] == 300

    def test_list_rfqs_supplier_sees_assigned(self):
        """Test that suppliers see RFQs assigned to them"""
        supplier_user = SimpleNamespace(id=400, role="supplier")
        supplier = SimpleNamespace(id=900, user_id=400)

        rfq = RFQ(
            id=22,
            buyer_id=301,
            supplier_id=900,
            title="Assigned RFQ",
            description="Assigned to supplier",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db = _make_mock_db(execute_results=[[supplier], [rfq]])
        _override_dependencies(supplier_user, db)

        response = client.get("/api/v1/rfqs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 22
        assert data[0]["supplier_id"] == 900

    def test_get_rfq_authorization(self):
        """Test RFQ detail authorization"""
        # Buyer requesting another buyer's RFQ should be forbidden
        buyer_user = SimpleNamespace(id=500, role="buyer")
        foreign_rfq = RFQ(
            id=33,
            buyer_id=999,
            title="Private RFQ",
            description="Not your RFQ",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db = _make_mock_db(execute_results=[[foreign_rfq]])
        _override_dependencies(buyer_user, db)

        response = client.get("/api/v1/rfqs/33")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authorized to view this RFQ"

        # Supplier without matching supplier profile should be forbidden
        supplier_user = SimpleNamespace(id=600, role="supplier")
        assigned_rfq = RFQ(
            id=34,
            buyer_id=501,
            supplier_id=777,
            title="Supplier RFQ",
            description="Restricted RFQ",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        supplier_profile = SimpleNamespace(id=888, user_id=600)
        db2 = _make_mock_db(execute_results=[[assigned_rfq], [supplier_profile]])
        _override_dependencies(supplier_user, db2)

        response2 = client.get("/api/v1/rfqs/34")
        assert response2.status_code == 403
        assert response2.json()["detail"] == "Not authorized to view this RFQ"
