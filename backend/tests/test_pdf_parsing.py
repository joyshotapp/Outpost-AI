"""Tests for PDF vision and Textract OCR parsing"""

import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

from app.services.claude import ClaudeService


@pytest.mark.asyncio
class TestPDFParsing:
    """Test PDF parsing with Claude Vision and Textract"""

    @pytest.fixture
    async def claude_service(self):
        """Create Claude service instance"""
        return ClaudeService()

    @staticmethod
    def create_test_pdf():
        """Create a simple test PDF with technical specs"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO

            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)

            # Page 1: Dimensions and specs
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 750, "RFQ TECHNICAL SPECIFICATIONS")

            c.setFont("Helvetica", 10)
            y_pos = 720
            specs = [
                "Product: CNC Machined Steel Components",
                "Material: AISI 1045 Steel",
                "Dimensions: 150mm x 100mm x 50mm",
                "Tolerance: H7/g6 precision",
                "Surface Treatment: Chromium Plating",
                "Quantity: 2000 pieces",
                "Delivery: 14 days",
                "Certifications: ISO9001, ISO13485",
                "Special Requirements: 100% Inspection Required",
                "Surface Roughness: Ra 1.6 micrometers",
            ]

            for spec in specs:
                c.drawString(50, y_pos, spec)
                y_pos -= 20

            c.showPage()

            # Page 2: Additional notes
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 750, "MANUFACTURING NOTES")

            c.setFont("Helvetica", 10)
            y_pos = 720
            notes = [
                "- Heat treatment required after machining",
                "- Dimensional verification via CMM",
                "- Surface finish must be uniform",
                "- Material certificates required",
                "- Testing per ASTM D76 specification",
                "- Packaging: Foam wrapped in cartons",
            ]

            for note in notes:
                c.drawString(50, y_pos, note)
                y_pos -= 20

            c.showPage()
            c.save()

            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
        except ImportError:
            # If reportlab not available, return empty PDF marker
            return b"%PDF-1.4\n"

    @pytest.mark.asyncio
    async def test_extract_pdf_from_s3(self, claude_service):
        """Test extracting PDF content from S3"""
        pdf_content = self.create_test_pdf()

        with patch.object(claude_service.s3_client, "get_object") as mock_get:
            mock_get.return_value = {"Body": MagicMock(read=lambda: pdf_content)}

            result = await claude_service.extract_pdf_from_s3("rfqs/test.pdf")

            assert result is not None
            assert isinstance(result, bytes)
            assert len(result) > 0
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_pdf_from_s3_not_found(self, claude_service):
        """Test handling of missing PDF in S3"""
        from botocore.exceptions import ClientError

        with patch.object(claude_service.s3_client, "get_object") as mock_get:
            mock_get.side_effect = ClientError(
                {"Error": {"Code": "NoSuchKey"}},
                "GetObject"
            )

            result = await claude_service.extract_pdf_from_s3("rfqs/missing.pdf")

            assert result is None

    @pytest.mark.asyncio
    async def test_convert_pdf_to_images(self, claude_service):
        """Test converting PDF pages to images"""
        pdf_content = self.create_test_pdf()

        # Create a simple test image instead of using pdf2image
        with patch("app.services.claude.convert_from_bytes") as mock_convert:
            # Create mock PIL images
            test_image = Image.new("RGB", (100, 100), color="white")
            mock_convert.return_value = [test_image, test_image]

            result = await claude_service.convert_pdf_to_images(pdf_content)

            assert isinstance(result, list)
            assert len(result) == 2
            for img_b64 in result:
                assert isinstance(img_b64, str)
                # Check it's valid base64
                assert len(img_b64) > 0

    @pytest.mark.asyncio
    async def test_convert_pdf_to_images_empty_pdf(self, claude_service):
        """Test converting empty PDF"""
        with patch("app.services.claude.convert_from_bytes") as mock_convert:
            mock_convert.return_value = []

            result = await claude_service.convert_pdf_to_images(b"")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_analyze_pdf_with_vision(self, claude_service):
        """Test analyzing PDF images with Claude Vision"""
        # Create a simple base64 test image
        test_image = Image.new("RGB", (100, 100), color="white")
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        import base64
        b64_image = base64.standard_b64encode(img_bytes.getvalue()).decode()

        with patch.object(claude_service.client, "messages") as mock_messages:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"dimensions": "150x100x50mm", "materials": ["AISI 1045 steel"]}')]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 200
            mock_messages.create.return_value = mock_response

            result = await claude_service.analyze_pdf_with_vision([b64_image])

            assert result["success"] is True
            assert "vision_data" in result
            assert result["tokens_used"]["input"] == 1000
            assert result["tokens_used"]["output"] == 200

    @pytest.mark.asyncio
    async def test_analyze_pdf_with_vision_empty_images(self, claude_service):
        """Test vision analysis with no images"""
        result = await claude_service.analyze_pdf_with_vision([])

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_extract_text_with_textract(self, claude_service):
        """Test starting Textract job for PDF"""
        with patch.object(claude_service.textract_client, "start_document_text_detection") as mock_textract:
            mock_textract.return_value = {"JobId": "test-job-id-12345"}

            result = await claude_service.extract_text_with_textract("rfqs/test.pdf")

            assert result["success"] is True
            assert result["job_id"] == "test-job-id-12345"
            assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_extract_text_with_textract_error(self, claude_service):
        """Test Textract error handling"""
        from botocore.exceptions import ClientError

        with patch.object(claude_service.textract_client, "start_document_text_detection") as mock_textract:
            mock_textract.side_effect = ClientError(
                {"Error": {"Code": "ValidationException"}},
                "StartDocumentTextDetection"
            )

            result = await claude_service.extract_text_with_textract("rfqs/test.pdf")

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_rfq_pdf_complete_flow(self, claude_service):
        """Test complete RFQ PDF analysis flow"""
        pdf_content = self.create_test_pdf()

        with patch.object(claude_service, "extract_pdf_from_s3") as mock_extract, \
             patch.object(claude_service, "convert_pdf_to_images") as mock_convert, \
             patch.object(claude_service, "analyze_pdf_with_vision") as mock_vision, \
             patch.object(claude_service, "extract_text_with_textract") as mock_textract, \
             patch.object(claude_service, "analyze_rfq_text") as mock_text:

            # Setup mocks
            mock_extract.return_value = pdf_content
            mock_convert.return_value = ["fake_b64_image"]
            mock_vision.return_value = {
                "success": True,
                "vision_data": {"dimensions": "150x100x50mm"},
                "tokens_used": {"input": 1000, "output": 200},
            }
            mock_textract.return_value = {
                "success": True,
                "job_id": "job-123",
                "status": "processing",
            }
            mock_text.return_value = {
                "success": True,
                "parsed_data": {"product_name": "Test Product"},
                "tokens_used": {"input": 500, "output": 100},
            }

            # Run analysis
            result = await claude_service.analyze_rfq_pdf(
                "rfqs/test.pdf",
                rfq_text="Test RFQ"
            )

            # Verify result
            assert result["success"] is True
            assert result["pages_analyzed"] == 1
            assert result["textract_status"] == "processing"
            assert "text_analysis" in result
            assert result["vision_analysis"]["dimensions"] == "150x100x50mm"

    @pytest.mark.asyncio
    async def test_analyze_rfq_pdf_missing_s3_object(self, claude_service):
        """Test RFQ PDF analysis with missing S3 object"""
        with patch.object(claude_service, "extract_pdf_from_s3") as mock_extract:
            mock_extract.return_value = None

            result = await claude_service.analyze_rfq_pdf("rfqs/missing.pdf")

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_pdf_image_conversion_quality(self, claude_service):
        """Test PDF to image conversion uses correct DPI"""
        pdf_content = self.create_test_pdf()

        with patch("app.services.claude.convert_from_bytes") as mock_convert:
            mock_convert.return_value = [Image.new("RGB", (100, 100))]

            await claude_service.convert_pdf_to_images(pdf_content)

            # Verify DPI settings
            call_args = mock_convert.call_args
            assert call_args[1]["dpi"] == claude_service.IMAGE_QUALITY
            assert call_args[1]["last_page"] == claude_service.MAX_IMAGES_PER_PDF

    @pytest.mark.asyncio
    async def test_pdf_parsing_with_real_rfq_example(self, claude_service):
        """Test PDF parsing with realistic RFQ specs"""
        mock_vision_response = {
            "success": True,
            "vision_data": {
                "dimensions": {"length": 150, "width": 100, "height": 50, "unit": "mm"},
                "materials": ["AISI 1045 Steel"],
                "surface_finish": "Chromium Plating",
                "tolerances": "H7/g6",
                "certifications": ["ISO9001", "ISO13485"],
                "special_requirements": ["100% Inspection", "Heat treatment after machining"],
            },
            "tokens_used": {"input": 1500, "output": 300},
        }

        with patch.object(claude_service, "extract_pdf_from_s3") as mock_extract, \
             patch.object(claude_service, "convert_pdf_to_images") as mock_convert, \
             patch.object(claude_service, "analyze_pdf_with_vision") as mock_vision, \
             patch.object(claude_service, "extract_text_with_textract") as mock_textract:

            mock_extract.return_value = self.create_test_pdf()
            mock_convert.return_value = ["fake_b64_image", "fake_b64_image"]
            mock_vision.return_value = mock_vision_response
            mock_textract.return_value = {
                "success": True,
                "job_id": "job-456",
                "status": "processing",
            }

            result = await claude_service.analyze_rfq_pdf("rfqs/real_example.pdf")

            assert result["success"] is True
            assert result["pages_analyzed"] == 2
            assert result["vision_analysis"]["dimensions"]["length"] == 150
            assert "ISO9001" in result["vision_analysis"]["certifications"]
