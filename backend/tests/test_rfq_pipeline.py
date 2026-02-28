"""Tests for RFQ processing pipeline"""

import pytest
from unittest.mock import patch, MagicMock

from app.tasks.rfq_pipeline import (
    process_rfq_complete_pipeline,
    parse_rfq_text_task,
    analyze_rfq_pdf_task,
    enrich_buyer_company_task,
    calculate_lead_score_task,
    generate_draft_reply_task,
    monitor_pipeline_health,
)


class TestRFQPipeline:
    """Test RFQ processing pipeline tasks"""

    def test_process_rfq_complete_pipeline_success(self):
        """Test successful complete RFQ pipeline processing"""
        rfq_id = 123

        with patch("app.tasks.rfq_pipeline.get_rfq_sync") as mock_get_rfq, \
             patch("app.tasks.rfq_pipeline.parse_rfq_text_task") as mock_parse, \
             patch("app.tasks.rfq_pipeline.analyze_rfq_pdf_task") as mock_pdf, \
             patch("app.tasks.rfq_pipeline.enrich_buyer_company_task") as mock_company, \
             patch("app.tasks.rfq_pipeline.calculate_lead_score_task") as mock_score, \
             patch("app.tasks.rfq_pipeline.generate_draft_reply_task") as mock_reply, \
             patch("app.tasks.rfq_pipeline.update_rfq_with_results") as mock_update:

            # Setup mocks
            mock_rfq = MagicMock()
            mock_rfq.description = "Test RFQ"
            mock_rfq.attachment_url = None
            mock_get_rfq.return_value = mock_rfq

            mock_parse.return_value = {
                "success": True,
                "parsed_data": {"quantity": 500},
            }

            mock_pdf.return_value = {
                "success": True,
                "vision_analysis": {},
                "pages_analyzed": 0,
            }

            mock_company.return_value = {
                "success": True,
                "company": {"company_name": "Test Corp"},
                "cached": False,
            }

            mock_score.return_value = {
                "success": True,
                "lead_score": 75,
                "lead_grade": "A",
                "scores": {},
            }

            mock_reply.return_value = {
                "success": True,
                "draft_reply": "Thank you for your RFQ...",
            }

            mock_update.return_value = True

            # Run pipeline (need to mock Celery task binding)
            with patch.object(process_rfq_complete_pipeline, "retry"):
                result = process_rfq_complete_pipeline(rfq_id)

            assert result["success"] is True
            assert result["rfq_id"] == rfq_id
            assert "stages" in result
            assert mock_update.called

    def test_process_rfq_pipeline_rfq_not_found(self):
        """Test pipeline when RFQ is not found"""
        rfq_id = 999

        with patch("app.tasks.rfq_pipeline.get_rfq_sync") as mock_get_rfq:
            mock_get_rfq.return_value = None

            with patch.object(process_rfq_complete_pipeline, "retry"):
                result = process_rfq_complete_pipeline(rfq_id)

            assert result["success"] is False
            assert "RFQ not found" in result["error"]

    def test_parse_rfq_text_task(self):
        """Test RFQ text parsing task"""
        rfq_text = "We need 500 aluminum parts"

        result = parse_rfq_text_task(rfq_text)

        assert result["success"] is True
        assert "parsed_data" in result

    def test_analyze_rfq_pdf_task_with_url(self):
        """Test PDF analysis task with attachment URL"""
        attachment_url = "https://s3.example.com/rfq.pdf"
        rfq_text = "PDF RFQ content"

        result = analyze_rfq_pdf_task(attachment_url, rfq_text)

        assert result["success"] is True
        assert "vision_analysis" in result

    def test_enrich_buyer_company_task_with_name(self):
        """Test buyer company enrichment task"""
        company_name = "Acme Manufacturing"

        result = enrich_buyer_company_task(company_name)

        assert result["success"] is True
        assert result["company"]["company_name"] == company_name

    def test_enrich_buyer_company_task_without_name(self):
        """Test buyer enrichment when no company name provided"""
        result = enrich_buyer_company_task(None)

        assert result["success"] is False
        assert "error" in result

    def test_calculate_lead_score_task(self):
        """Test lead scoring task"""
        rfq_text = "Urgent RFQ with specific requirements"
        company_name = "Tech Corp"
        parsed_data = {"quantity": 1000, "lead_time_days": 30}

        result = calculate_lead_score_task(rfq_text, company_name, parsed_data)

        assert result["success"] is True
        assert "lead_score" in result
        assert "lead_grade" in result
        assert 0 <= result["lead_score"] <= 100
        assert result["lead_grade"] in ["A", "B", "C"]

    def test_generate_draft_reply_task(self):
        """Test draft reply generation task"""
        parsed_data = {"product_name": "Components", "quantity": 500}
        supplier_profile = {"company_name": "Our Company"}
        lead_grade = "A"

        result = generate_draft_reply_task(parsed_data, supplier_profile, lead_grade)

        assert result["success"] is True
        assert "draft_reply" in result
        assert len(result["draft_reply"]) > 0

    def test_monitor_pipeline_health(self):
        """Test pipeline health monitoring task"""
        result = monitor_pipeline_health()

        assert "status" in result
        assert "tasks_processed" in result
        assert "avg_processing_time_seconds" in result

    def test_pipeline_stage_tracking(self):
        """Test that pipeline tracks all processing stages"""
        rfq_id = 456

        with patch("app.tasks.rfq_pipeline.get_rfq_sync") as mock_get_rfq, \
             patch("app.tasks.rfq_pipeline.update_rfq_with_results"):

            mock_rfq = MagicMock()
            mock_rfq.description = "Multi-stage test"
            mock_rfq.attachment_url = "https://example.com/rfq.pdf"
            mock_get_rfq.return_value = mock_rfq

            with patch.object(process_rfq_complete_pipeline, "retry"):
                result = process_rfq_complete_pipeline(rfq_id)

            stages = result.get("stages", {})
            assert "text_parsing" in stages
            assert "pdf_analysis" in stages
            assert "company_research" in stages
            assert "scoring" in stages
            assert "reply_generation" in stages

    def test_pipeline_handles_partial_failures(self):
        """Test that pipeline continues even if some stages fail"""
        rfq_id = 789

        with patch("app.tasks.rfq_pipeline.get_rfq_sync") as mock_get_rfq, \
             patch("app.tasks.rfq_pipeline.parse_rfq_text_task") as mock_parse, \
             patch("app.tasks.rfq_pipeline.analyze_rfq_pdf_task") as mock_pdf, \
             patch("app.tasks.rfq_pipeline.update_rfq_with_results"):

            mock_rfq = MagicMock()
            mock_rfq.description = "Test"
            mock_rfq.attachment_url = "https://example.com/rfq.pdf"
            mock_get_rfq.return_value = mock_rfq

            # Make PDF analysis fail, but others succeed
            mock_parse.return_value = {"success": True, "parsed_data": {}}
            mock_pdf.return_value = {"success": False, "error": "PDF processing failed"}

            with patch.object(process_rfq_complete_pipeline, "retry"):
                result = process_rfq_complete_pipeline(rfq_id)

            # Pipeline should still complete despite PDF failure
            assert result["success"] is True
            assert not result["stages"]["pdf_analysis"]["success"]

    def test_lead_score_boundaries(self):
        """Test lead score calculation produces valid values"""
        rfq_text = "Test RFQ"
        company_name = "Test Company"
        parsed_data = {}

        result = calculate_lead_score_task(rfq_text, company_name, parsed_data)

        score = result["lead_score"]
        grade = result["lead_grade"]

        # Verify score is in valid range
        assert 0 <= score <= 100
        # Verify grade matches score
        if score >= 70:
            assert grade == "A"
        elif score >= 50:
            assert grade == "B"
        else:
            assert grade == "C"

    def test_draft_reply_includes_lead_grade_context(self):
        """Test that draft reply generation considers lead grade"""
        parsed_data = {"product_name": "Test"}
        supplier_profile = {"company_name": "Test Supplier"}

        # Test with Grade A
        result_a = generate_draft_reply_task(
            parsed_data, supplier_profile, "A"
        )
        assert result_a["success"] is True

        # Test with Grade C
        result_c = generate_draft_reply_task(
            parsed_data, supplier_profile, "C"
        )
        assert result_c["success"] is True

        # Both should have replies but could differ in tone
        assert len(result_a["draft_reply"]) > 0
        assert len(result_c["draft_reply"]) > 0

    def test_celery_task_configuration(self):
        """Test Celery app configuration"""
        from app.celery_app import celery_app

        # Verify broker is configured
        assert celery_app.conf.broker_url is not None

        # Verify task routes
        assert "task_routes" in celery_app.conf
        routes = celery_app.conf.get("task_routes", {})
        assert "app.tasks.rfq_pipeline.process_rfq_complete_pipeline" in routes

        # Verify queue configuration
        rfq_pipeline_queue = routes.get("app.tasks.rfq_pipeline.process_rfq_complete_pipeline", {})
        assert "queue" in rfq_pipeline_queue
