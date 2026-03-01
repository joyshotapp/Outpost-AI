"""Tests for Slack webhook integration service"""

import pytest
import json
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from datetime import datetime

from app.services.slack import SlackService


@pytest.mark.asyncio
class TestSlackService:
    """Test Slack webhook integration"""

    @pytest.fixture
    async def slack_service(self):
        """Create Slack service instance with mocked webhook URL"""
        with patch("app.services.slack.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
            return SlackService()

    @pytest.mark.asyncio
    async def test_send_a_grade_lead_notification(self, slack_service):
        """Test sending A-grade lead notification to Slack"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_service.send_lead_notification(
                rfq_id=1,
                lead_grade="A",
                lead_score=85,
                buyer_company_name="TechCorp Manufacturing",
                product_summary="CNC machined aluminum components",
                rfq_text_preview="We are looking for precision CNC parts...",
                scoring_breakdown={
                    "intent": {"score": 90, "weight": 0.40},
                    "company": {"score": 80, "weight": 0.35},
                    "rfq": {"score": 85, "weight": 0.25},
                },
            )

            assert result["success"] is True
            assert result["message_ts"] == "1234567890.123456"

    @pytest.mark.asyncio
    async def test_skip_b_grade_notification(self, slack_service):
        """Test that B-grade leads are skipped (only A-grade notified)"""
        result = await slack_service.send_lead_notification(
            rfq_id=2,
            lead_grade="B",
            lead_score=65,
            buyer_company_name="MidMarket Inc",
            product_summary="Steel components",
            rfq_text_preview="Looking for steel parts...",
        )

        assert result["success"] is True
        assert result["skipped"] is True
        assert "B" in result["reason"]

    @pytest.mark.asyncio
    async def test_skip_c_grade_notification(self, slack_service):
        """Test that C-grade leads are skipped"""
        result = await slack_service.send_lead_notification(
            rfq_id=3,
            lead_grade="C",
            lead_score=35,
            buyer_company_name="Startup Labs",
            product_summary="General parts",
            rfq_text_preview="Need some parts...",
        )

        assert result["success"] is True
        assert result["skipped"] is True

    @pytest.mark.asyncio
    async def test_webhook_connection_error(self, slack_service):
        """Test handling of webhook connection error"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            import aiohttp
            mock_post.side_effect = aiohttp.ClientError("Connection refused")

            result = await slack_service.send_lead_notification(
                rfq_id=4,
                lead_grade="A",
                lead_score=75,
                buyer_company_name="Test Corp",
                product_summary="Test product",
                rfq_text_preview="Test RFQ",
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_webhook_ssl_error(self, slack_service):
        """Test handling of SSL error"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = aiohttp.ClientError("SSL certificate verification failed")

            result = await slack_service.send_lead_notification(
                rfq_id=5,
                lead_grade="A",
                lead_score=80,
                buyer_company_name="Secure Corp",
                product_summary="Secure product",
                rfq_text_preview="Secure RFQ",
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_webhook_http_error(self, slack_service):
        """Test handling of HTTP error response"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Invalid payload")
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_service.send_lead_notification(
                rfq_id=6,
                lead_grade="A",
                lead_score=70,
                buyer_company_name="Error Corp",
                product_summary="Error product",
                rfq_text_preview="Error RFQ",
            )

            assert result["success"] is False
            assert "400" in result["error"]

    @pytest.mark.asyncio
    async def test_webhook_not_configured(self):
        """Test behavior when webhook URL is not configured"""
        with patch("app.services.slack.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = None
            service = SlackService()

            result = await service.send_lead_notification(
                rfq_id=7,
                lead_grade="A",
                lead_score=90,
                buyer_company_name="Config Test Corp",
                product_summary="Config test",
                rfq_text_preview="Config test",
            )

            assert result["success"] is False
            assert "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_send_pipeline_error_notification(self, slack_service):
        """Test sending pipeline error notification"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_service.send_pipeline_error_notification(
                rfq_id=8,
                failed_stage="text_parsing",
                error_message="Claude API timeout after 30s",
            )

            assert result["success"] is True
            assert result["message_ts"] == "1234567890.123456"

    @pytest.mark.asyncio
    async def test_build_lead_message_format(self, slack_service):
        """Test that message payload is properly formatted"""
        message = slack_service._build_lead_message(
            rfq_id=9,
            lead_grade="A",
            lead_score=88,
            buyer_company_name="Format Test Corp",
            product_summary="Precision components",
            rfq_text_preview="Looking for precision CNC parts with tolerance ±0.01mm",
            scoring_breakdown={
                "intent": {"score": 85, "weight": 0.40},
                "company": {"score": 90, "weight": 0.35},
                "rfq": {"score": 88, "weight": 0.25},
            },
        )

        assert "attachments" in message
        assert len(message["attachments"]) == 1
        attachment = message["attachments"][0]
        assert attachment["color"] == "#2ecc71"  # Green for A-grade
        assert attachment["title"] == "RFQ #9 - Grade A"
        assert len(attachment["fields"]) >= 5  # RFQ ID, Grade, Score, Company, Product, Preview, Breakdown

    @pytest.mark.asyncio
    async def test_build_lead_message_without_optional_fields(self, slack_service):
        """Test message building with minimal required fields"""
        message = slack_service._build_lead_message(
            rfq_id=10,
            lead_grade="A",
            lead_score=72,
            buyer_company_name=None,
            product_summary=None,
            rfq_text_preview=None,
            scoring_breakdown=None,
        )

        assert "attachments" in message
        assert len(message["attachments"]) == 1
        attachment = message["attachments"][0]
        # Should have at least RFQ ID, Grade, and Score fields
        assert len(attachment["fields"]) >= 3

    @pytest.mark.asyncio
    async def test_format_scoring_breakdown(self, slack_service):
        """Test scoring breakdown formatting"""
        breakdown = {
            "intent": {"score": 80, "weight": 0.40},
            "company": {"score": 75, "weight": 0.35},
            "rfq": {"score": 85, "weight": 0.25},
        }

        formatted = slack_service._format_scoring_breakdown(breakdown)

        assert "Intent: 80/100" in formatted
        assert "Company: 75/100" in formatted
        assert "RFQ: 85/100" in formatted
        assert "40%" in formatted or "40.0%" in formatted

    @pytest.mark.asyncio
    async def test_format_scoring_breakdown_empty(self, slack_service):
        """Test scoring breakdown formatting with empty data"""
        formatted = slack_service._format_scoring_breakdown({})

        assert formatted == "N/A"

    @pytest.mark.asyncio
    async def test_send_lead_notification_with_long_text(self, slack_service):
        """Test that long text is truncated properly"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            long_preview = "x" * 1000  # Very long RFQ text

            result = await slack_service.send_lead_notification(
                rfq_id=11,
                lead_grade="A",
                lead_score=80,
                buyer_company_name="Long Text Corp",
                product_summary="x" * 500,
                rfq_text_preview=long_preview,
            )

            assert result["success"] is True
            # Verify the message was sent with truncated text
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_sequential_notifications(self, slack_service):
        """Test sending multiple notifications in sequence"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            for i in range(3):
                result = await slack_service.send_lead_notification(
                    rfq_id=100 + i,
                    lead_grade="A",
                    lead_score=75 + i * 5,
                    buyer_company_name=f"Company {i}",
                    product_summary=f"Product {i}",
                    rfq_text_preview=f"RFQ text {i}",
                )
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_color_mapping_for_different_grades(self, slack_service):
        """Test that color is correct for each grade"""
        colors = {}
        for grade in ["A", "B", "C"]:
            message = slack_service._build_lead_message(
                rfq_id=200,
                lead_grade=grade,
                lead_score=70,
                buyer_company_name="Color Test",
                product_summary="Test",
                rfq_text_preview="Test",
            )
            colors[grade] = message["attachments"][0]["color"]

        assert colors["A"] == "#2ecc71"  # Green
        assert colors["B"] == "#f39c12"  # Orange
        assert colors["C"] == "#e74c3c"  # Red

    @pytest.mark.asyncio
    async def test_webhook_timeout_handling(self, slack_service):
        """Test handling of webhook timeout"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")

            result = await slack_service.send_lead_notification(
                rfq_id=12,
                lead_grade="A",
                lead_score=80,
                buyer_company_name="Timeout Corp",
                product_summary="Timeout test",
                rfq_text_preview="Timeout test",
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_error_notification_format(self, slack_service):
        """Test error notification message format"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_service.send_pipeline_error_notification(
                rfq_id=13,
                failed_stage="pdf_analysis",
                error_message="PDF file corrupted or not readable",
            )

            assert result["success"] is True
            # Verify the message was sent
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_send_high_intent_visitor_notification(self, slack_service):
        """Test sending high-intent visitor notification"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"ts": "1234567890.123456"})
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await slack_service.send_high_intent_visitor_notification(
                supplier_id=7,
                visitor_session_id="visitor-abc",
                event_type="rfq_submit_click",
                intent_score=88,
                page_url="/suppliers/acme/rfq",
                visitor_company="Acme Inc",
            )

            assert result["success"] is True
            assert result["message_ts"] == "1234567890.123456"

    @pytest.mark.asyncio
    async def test_send_high_intent_visitor_notification_skips_without_webhook(self):
        """Test high-intent notification returns skipped when webhook missing"""
        with patch("app.services.slack.settings") as mock_settings:
            mock_settings.SLACK_WEBHOOK_URL = None
            service = SlackService()

            result = await service.send_high_intent_visitor_notification(
                supplier_id=7,
                visitor_session_id="visitor-abc",
                event_type="rfq_submit_click",
                intent_score=88,
            )

            assert result["success"] is True
            assert result["skipped"] is True
