"""Tests for Claude RFQ parsing accuracy

This test suite validates RFQ text parsing with manufacturing-specific test cases.
Target accuracy: ≥ 80%
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.claude import ClaudeService

# Real RFQ examples for testing
REAL_RFQ_EXAMPLES = [
    {
        "rfq_text": """We need 500 pcs of aluminum precision components, size 25x10x8mm, tolerance ±0.1mm,
surface: bright anodize, material: 6061-T6, delivery needed within 30 days, must have ISO9001 certificate""",
        "expected_fields": {
            "product_name": "aluminum precision components",
            "materials": ["6061-T6"],
            "dimensions": "25x10x8mm",
            "quantity": 500,
            "unit": "pcs",
            "lead_time_days": 30,
            "surface_finish": "bright anodize",
            "certifications": ["ISO9001"],
        },
    },
    {
        "rfq_text": """Request for Quotation:
Product: Plastic injection molded housing
Quantity: 10,000 units
Material: ABS plastic, black color
Dimensions: 150mm x 100mm x 50mm
Tolerance: ±0.5mm
Surface: Smooth finish, glossy
Delivery: 45 days
Certifications needed: ISO9001, RoHS compliant""",
        "expected_fields": {
            "product_name": "Plastic injection molded housing",
            "materials": ["ABS plastic"],
            "dimensions": "150mm x 100mm x 50mm",
            "quantity": 10000,
            "unit": "units",
            "lead_time_days": 45,
            "surface_finish": "glossy",
            "certifications": ["ISO9001", "RoHS"],
        },
    },
    {
        "rfq_text": """Dear Supplier,
We are looking for CNC machined steel parts:
- Material: AISI 1045 steel
- Shape: Cylindrical shafts, diameter 30mm, length 100mm
- Tolerance: H7/g6
- Surface treatment: Plating (chromium)
- Quantity: 2000 pieces
- Required delivery: ASAP (within 14 days preferred)
- Must pass 100% inspection
- Requirement: ISO9001 and ISO13485 certification""",
        "expected_fields": {
            "product_name": "CNC machined steel parts",
            "materials": ["AISI 1045 steel"],
            "quantity": 2000,
            "lead_time_days": 14,
            "tolerances": "H7/g6",
            "surface_finish": "chromium plating",
            "certifications": ["ISO9001", "ISO13485"],
        },
    },
]


@pytest.mark.asyncio
class TestClaudeRFQParsing:
    """Test Claude RFQ parsing accuracy"""

    @pytest.fixture
    async def claude_service(self):
        """Create Claude service instance"""
        return ClaudeService()

    @pytest.mark.asyncio
    async def test_parse_rfq_example_1(self, claude_service):
        """Test parsing RFQ example 1"""
        example = REAL_RFQ_EXAMPLES[0]

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(example["expected_fields"]))]
            mock_response.usage.input_tokens = 500
            mock_response.usage.output_tokens = 150
            mock_messages.create.return_value = mock_response

            result = await claude_service.analyze_rfq_text(example["rfq_text"])

            assert result["success"] is True
            parsed = result["parsed_data"]

            # Validate key fields
            assert parsed.get("product_name") is not None
            assert parsed.get("quantity") == example["expected_fields"]["quantity"]
            assert parsed.get("lead_time_days") == example["expected_fields"]["lead_time_days"]

    @pytest.mark.asyncio
    async def test_parse_rfq_example_2(self, claude_service):
        """Test parsing RFQ example 2"""
        example = REAL_RFQ_EXAMPLES[1]

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(example["expected_fields"]))]
            mock_response.usage.input_tokens = 500
            mock_response.usage.output_tokens = 150
            mock_messages.create.return_value = mock_response

            result = await claude_service.analyze_rfq_text(example["rfq_text"])

            assert result["success"] is True
            parsed = result["parsed_data"]
            assert parsed.get("quantity") == example["expected_fields"]["quantity"]

    @pytest.mark.asyncio
    async def test_parse_rfq_example_3(self, claude_service):
        """Test parsing RFQ example 3 with complex specs"""
        example = REAL_RFQ_EXAMPLES[2]

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(example["expected_fields"]))]
            mock_response.usage.input_tokens = 600
            mock_response.usage.output_tokens = 200
            mock_messages.create.return_value = mock_response

            result = await claude_service.analyze_rfq_text(example["rfq_text"])

            assert result["success"] is True
            parsed = result["parsed_data"]

            # Verify tolerances extracted (dimension precision specs)
            assert parsed.get("tolerances") is not None

    @pytest.mark.asyncio
    async def test_api_token_tracking(self, claude_service):
        """Test that API token usage is tracked correctly"""
        initial_stats = claude_service.get_usage_stats()
        initial_calls = initial_stats["total_calls"]

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"product_name": "Test"}')]
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_messages.create.return_value = mock_response

            # Make an API call
            result = await claude_service.analyze_rfq_text("Test RFQ")

            final_stats = claude_service.get_usage_stats()

            # Verify tracker was updated
            assert final_stats["total_calls"] == initial_calls + 1
            assert final_stats["total_input_tokens"] > 0
            assert final_stats["total_output_tokens"] > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, claude_service):
        """Test API error handling with APIError"""
        from anthropic import APIConnectionError

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_messages.create.side_effect = APIConnectionError(
                request=MagicMock(),
                message="Connection failed"
            )

            # Empty RFQ should still be handled gracefully
            result = await claude_service.analyze_rfq_text("")

            # Should return error response
            assert result["success"] is False
            assert "error" in result
            assert result["error"] == "connection_error"
