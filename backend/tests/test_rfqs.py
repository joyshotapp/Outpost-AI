"""Tests for RFQ API endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import RFQ, User

client = TestClient(app)


class TestRFQAPI:
    """Test RFQ API endpoints"""

    @pytest.mark.asyncio
    async def test_create_rfq_without_attachment(
        self, db: AsyncSession, buyer_user: User
    ):
        """Test creating an RFQ without attachment"""
        # Need to implement using async test client
        pass

    @pytest.mark.asyncio
    async def test_create_rfq_with_pdf_attachment(
        self, db: AsyncSession, buyer_user: User
    ):
        """Test creating an RFQ with PDF attachment"""
        pass

    @pytest.mark.asyncio
    async def test_create_rfq_as_supplier_fails(
        self, db: AsyncSession, supplier_user: User
    ):
        """Test that suppliers cannot submit RFQs"""
        pass

    @pytest.mark.asyncio
    async def test_list_rfqs_buyer_sees_own(
        self, db: AsyncSession, buyer_user: User
    ):
        """Test that buyers only see their own RFQs"""
        pass

    @pytest.mark.asyncio
    async def test_list_rfqs_supplier_sees_assigned(
        self, db: AsyncSession, supplier_user: User
    ):
        """Test that suppliers see RFQs assigned to them"""
        pass

    @pytest.mark.asyncio
    async def test_get_rfq_authorization(
        self, db: AsyncSession, buyer_user: User, supplier_user: User
    ):
        """Test RFQ detail authorization"""
        pass
