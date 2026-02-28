"""Tests for draft reply generator service"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.draft_reply_generator import DraftReplyGenerator


@pytest.mark.asyncio
class TestDraftReplyGenerator:
    """Test draft reply generator"""

    @pytest.fixture
    def generator(self):
        """Create draft reply generator instance"""
        return DraftReplyGenerator()

    @pytest.fixture
    def sample_rfq_data(self):
        """Sample RFQ data"""
        return {
            "product_name": "Aluminum Precision Components",
            "quantity": 500,
            "lead_time_days": 30,
            "special_requirements": "100% inspection required",
            "certifications": ["ISO9001"],
        }

    @pytest.fixture
    def sample_supplier_profile(self):
        """Sample supplier profile"""
        return {
            "company_name": "Premier Manufacturing Co.",
            "main_products": "CNC machined components, assemblies",
            "number_of_employees": 250,
            "certifications": "ISO9001, ISO13485",
            "country": "China",
            "city": "Shenzhen",
        }

    @pytest.mark.asyncio
    async def test_generate_reply_high_quality_lead(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating reply for high-quality lead (Grade A)"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Thank you for your inquiry...")]
            mock_response.usage.input_tokens = 500
            mock_response.usage.output_tokens = 200
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
                lead_grade="A",
                include_technical_details=True,
            )

            assert result["success"] is True
            assert "draft_reply" in result
            assert len(result["draft_reply"]) > 0
            assert result["metadata"]["lead_grade"] == "A"

    @pytest.mark.asyncio
    async def test_generate_reply_medium_quality_lead(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating reply for medium-quality lead (Grade B)"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="We appreciate your RFQ...")]
            mock_response.usage.input_tokens = 450
            mock_response.usage.output_tokens = 180
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
                lead_grade="B",
            )

            assert result["success"] is True
            assert result["metadata"]["lead_grade"] == "B"

    @pytest.mark.asyncio
    async def test_generate_reply_low_quality_lead(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating reply for low-quality lead (Grade C)"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Thank you for reaching out...")]
            mock_response.usage.input_tokens = 400
            mock_response.usage.output_tokens = 150
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
                lead_grade="C",
            )

            assert result["success"] is True
            assert result["metadata"]["lead_grade"] == "C"

    @pytest.mark.asyncio
    async def test_generate_reply_without_lead_grade(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating reply without specifying lead grade"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Professional reply...")]
            mock_response.usage.input_tokens = 400
            mock_response.usage.output_tokens = 150
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
            )

            assert result["success"] is True
            assert result["metadata"]["lead_grade"] is None

    @pytest.mark.asyncio
    async def test_generate_reply_without_technical_details(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating reply without technical details"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Commercial reply...")]
            mock_response.usage.input_tokens = 350
            mock_response.usage.output_tokens = 130
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
                include_technical_details=False,
            )

            assert result["success"] is True
            assert result["metadata"]["include_technical"] is False

    @pytest.mark.asyncio
    async def test_generate_follow_up_reply(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test generating follow-up reply to buyer's question"""
        original_reply = "Thank you for your inquiry. We can provide competitive pricing..."
        buyer_followup = "Can you provide samples? What's your MOQ?"

        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="We can provide samples...")]
            mock_response.usage.input_tokens = 400
            mock_response.usage.output_tokens = 100
            mock_messages.create.return_value = mock_response

            result = await generator.generate_follow_up_reply(
                original_rfq=sample_rfq_data,
                original_reply=original_reply,
                buyer_followup=buyer_followup,
                supplier_profile=sample_supplier_profile,
            )

            assert result["success"] is True
            assert "follow_up_reply" in result
            assert len(result["follow_up_reply"]) > 0

    @pytest.mark.asyncio
    async def test_refine_draft_reply(
        self,
        generator,
        sample_supplier_profile,
    ):
        """Test refining a draft reply based on feedback"""
        original_draft = "Thank you for your inquiry..."
        refinement_request = "Make it more enthusiastic and highlight our 20 years of experience"

        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="With 20 years of expertise...")]
            mock_response.usage.input_tokens = 300
            mock_response.usage.output_tokens = 150
            mock_messages.create.return_value = mock_response

            result = await generator.refine_draft_reply(
                draft_reply=original_draft,
                refinement_request=refinement_request,
                supplier_profile=sample_supplier_profile,
            )

            assert result["success"] is True
            assert "refined_reply" in result
            assert len(result["refined_reply"]) > 0

    @pytest.mark.asyncio
    async def test_generate_reply_error_handling(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test error handling in reply generation"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_messages.create.side_effect = Exception("API error")

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
            )

            assert result["success"] is False
            assert "error" in result

    def test_get_system_prompt_grade_a(self, generator):
        """Test system prompt for Grade A leads"""
        prompt = generator._get_system_prompt("A", include_technical=True)

        assert "高質量" in prompt or "專業經驗" in prompt or "成功案例" in prompt

    def test_get_system_prompt_grade_b(self, generator):
        """Test system prompt for Grade B leads"""
        prompt = generator._get_system_prompt("B", include_technical=True)

        assert "中等" in prompt or "核心能力" in prompt or "有潛力" in prompt

    def test_get_system_prompt_grade_c(self, generator):
        """Test system prompt for Grade C leads"""
        prompt = generator._get_system_prompt("C", include_technical=True)

        assert "專業" in prompt

    def test_get_system_prompt_without_technical(self, generator):
        """Test system prompt when excluding technical details"""
        prompt = generator._get_system_prompt("A", include_technical=False)

        assert "商業" in prompt or "技術" in prompt

    def test_build_user_prompt_with_grade(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test building user prompt with lead grade"""
        prompt = generator._build_user_prompt(
            rfq_data=sample_rfq_data,
            supplier_profile=sample_supplier_profile,
            lead_grade="A",
        )

        assert "Aluminum Precision Components" in prompt
        assert "500" in prompt
        assert "Premier Manufacturing" in prompt
        assert "【線索等級】A" in prompt

    def test_build_user_prompt_without_grade(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test building user prompt without lead grade"""
        prompt = generator._build_user_prompt(
            rfq_data=sample_rfq_data,
            supplier_profile=sample_supplier_profile,
            lead_grade=None,
        )

        assert "Aluminum Precision Components" in prompt
        assert "【線索等級】" not in prompt

    @pytest.mark.asyncio
    async def test_reply_with_minimal_rfq_data(
        self,
        generator,
        sample_supplier_profile,
    ):
        """Test generating reply with minimal RFQ data"""
        minimal_rfq = {
            "product_name": "Components",
            "quantity": None,
        }

        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="We can help with your inquiry...")]
            mock_response.usage.input_tokens = 300
            mock_response.usage.output_tokens = 100
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=minimal_rfq,
                supplier_profile=sample_supplier_profile,
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_token_usage_tracking(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test that token usage is properly tracked"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Reply text")]
            mock_response.usage.input_tokens = 1234
            mock_response.usage.output_tokens = 5678
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
            )

            assert result["tokens_used"]["input"] == 1234
            assert result["tokens_used"]["output"] == 5678

    @pytest.mark.asyncio
    async def test_reply_length_in_metadata(
        self,
        generator,
        sample_rfq_data,
        sample_supplier_profile,
    ):
        """Test that reply length is recorded in metadata"""
        with patch.object(generator.claude_service.client, "messages") as mock_messages:
            test_reply = "This is a test reply with some length." * 10
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=test_reply)]
            mock_response.usage.input_tokens = 300
            mock_response.usage.output_tokens = 100
            mock_messages.create.return_value = mock_response

            result = await generator.generate_reply(
                rfq_data=sample_rfq_data,
                supplier_profile=sample_supplier_profile,
            )

            assert result["metadata"]["reply_length"] == len(test_reply)
            assert result["metadata"]["reply_length"] > 100
