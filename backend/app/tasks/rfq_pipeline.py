"""Celery tasks for RFQ processing pipeline orchestration"""

import json
import logging
from typing import Dict, Any, Optional

from celery import shared_task

from app.services.claude import get_claude_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_rfq_complete_pipeline(self, rfq_id: int) -> Dict[str, Any]:
    """
    Complete RFQ processing pipeline: parse → analyze PDF → company research → score → generate reply

    Pipeline flow:
    1. Extract RFQ text and get buyer company info
    2. Analyze RFQ text with Claude (Task 3.3)
    3. Analyze PDF with vision + OCR (Task 3.4)
    4. Enrich buyer company profile with Apollo (Task 3.5)
    5. Calculate lead score (Task 3.6)
    6. Generate draft reply (Task 3.7)
    7. Update RFQ with all analysis results
    """
    try:
        logger.info(f"Starting RFQ pipeline for RFQ #{rfq_id}")

        # Get RFQ from database
        rfq = get_rfq_sync(rfq_id)
        if not rfq:
            logger.error(f"RFQ #{rfq_id} not found")
            return {"success": False, "error": "RFQ not found"}

        pipeline_results = {
            "rfq_id": rfq_id,
            "stages": {},
        }

        # Stage 1: Parse RFQ text with Claude
        logger.info(f"Stage 1/5: Parsing RFQ text for RFQ #{rfq_id}")
        parse_result = parse_rfq_text_task(rfq.description)
        if not parse_result.get("success"):
            logger.warning(f"RFQ text parsing failed for #{rfq_id}: {parse_result.get('error')}")
            parsed_data = {}
        else:
            parsed_data = parse_result.get("parsed_data", {})

        pipeline_results["stages"]["text_parsing"] = {
            "success": parse_result.get("success"),
            "data": parsed_data,
        }

        # Stage 2: Analyze PDF if attachment exists
        pdf_vision_data = None
        if rfq.attachment_url:
            logger.info(f"Stage 2/5: Analyzing PDF for RFQ #{rfq_id}")
            pdf_result = analyze_rfq_pdf_task(rfq.attachment_url, rfq.description)
            if pdf_result.get("success"):
                pdf_vision_data = pdf_result.get("vision_analysis")
                pipeline_results["stages"]["pdf_analysis"] = {
                    "success": True,
                    "pages_analyzed": pdf_result.get("pages_analyzed"),
                }
            else:
                pipeline_results["stages"]["pdf_analysis"] = {
                    "success": False,
                    "error": pdf_result.get("error"),
                }
        else:
            logger.info(f"No PDF attachment for RFQ #{rfq_id}, skipping Stage 2")
            pipeline_results["stages"]["pdf_analysis"] = {
                "success": True,
                "skipped": "No attachment",
            }

        # Stage 3: Research buyer company with Apollo
        buyer_company_name = parsed_data.get("buyer_company")
        logger.info(f"Stage 3/5: Researching buyer company for RFQ #{rfq_id}")
        company_result = enrich_buyer_company_task(buyer_company_name)
        company_data = None
        if company_result.get("success"):
            company_data = company_result.get("company")
            pipeline_results["stages"]["company_research"] = {
                "success": True,
                "company_name": company_data.get("company_name"),
                "cached": company_result.get("cached"),
            }
        else:
            logger.warning(f"Company research failed for #{rfq_id}: {company_result.get('error')}")
            pipeline_results["stages"]["company_research"] = {
                "success": False,
                "error": company_result.get("error"),
            }

        # Stage 4: Calculate lead score
        logger.info(f"Stage 4/5: Calculating lead score for RFQ #{rfq_id}")
        score_result = calculate_lead_score_task(
            rfq.description,
            buyer_company_name,
            parsed_data,
        )
        lead_score = 50
        lead_grade = "C"
        if score_result.get("success"):
            lead_score = score_result.get("lead_score")
            lead_grade = score_result.get("lead_grade")
            pipeline_results["stages"]["scoring"] = {
                "success": True,
                "score": lead_score,
                "grade": lead_grade,
                "breakdown": score_result.get("scores"),
            }
        else:
            logger.warning(f"Lead scoring failed for #{rfq_id}")
            pipeline_results["stages"]["scoring"] = {
                "success": False,
                "error": score_result.get("error"),
            }

        # Stage 5: Generate draft reply
        logger.info(f"Stage 5/5: Generating draft reply for RFQ #{rfq_id}")
        supplier_profile = {
            "company_name": "Your Company Name",  # Should come from current supplier
            "main_products": "Manufacturing",
        }
        reply_result = generate_draft_reply_task(
            parsed_data,
            supplier_profile,
            lead_grade,
        )
        draft_reply = None
        if reply_result.get("success"):
            draft_reply = reply_result.get("draft_reply")
            pipeline_results["stages"]["reply_generation"] = {
                "success": True,
                "reply_length": len(draft_reply),
            }
        else:
            logger.warning(f"Draft reply generation failed for #{rfq_id}")
            pipeline_results["stages"]["reply_generation"] = {
                "success": False,
                "error": reply_result.get("error"),
            }

        # Update RFQ with all results
        logger.info(f"Updating RFQ #{rfq_id} with pipeline results")
        update_rfq_with_results(
            rfq_id=rfq_id,
            parsed_data=parsed_data,
            pdf_vision_data=pdf_vision_data,
            lead_score=lead_score,
            lead_grade=lead_grade,
            draft_reply=draft_reply,
        )

        pipeline_results["success"] = True
        pipeline_results["timestamp"] = str(json.dumps({"completed": True}))

        logger.info(f"RFQ pipeline completed successfully for RFQ #{rfq_id} - Grade {lead_grade}, Score {lead_score}")

        return pipeline_results

    except Exception as e:
        logger.error(f"RFQ pipeline failed for #{rfq_id}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def parse_rfq_text_task(self, rfq_text: str) -> Dict[str, Any]:
    """Task 3.3: Parse RFQ text with Claude"""
    try:
        claude_service = get_claude_service()
        # Note: This would need to be made sync-compatible or use async_to_sync
        # For now, this is a placeholder that would be called from a sync context
        result = {
            "success": True,
            "parsed_data": {
                "product_name": "Parsed from RFQ",
                "quantity": None,
            },
        }
        return result
    except Exception as e:
        logger.error(f"Text parsing task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def analyze_rfq_pdf_task(self, attachment_url: str, rfq_text: str) -> Dict[str, Any]:
    """Task 3.4: Analyze PDF with vision and Textract"""
    try:
        # Extract S3 key from presigned URL
        # This is a simplified version - in production would parse the actual URL
        logger.info(f"Analyzing PDF from {attachment_url[:50]}...")

        result = {
            "success": True,
            "vision_analysis": {
                "dimensions": "Extracted from PDF",
            },
            "pages_analyzed": 2,
        }
        return result
    except Exception as e:
        logger.error(f"PDF analysis task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def enrich_buyer_company_task(self, company_name: Optional[str]) -> Dict[str, Any]:
    """Task 3.5: Research buyer company with Apollo"""
    try:
        if not company_name:
            logger.warning("No company name provided for Apollo enrichment")
            return {
                "success": False,
                "error": "No company name provided",
            }

        # In production, would call Apollo service
        result = {
            "success": True,
            "company": {
                "company_name": company_name,
                "employee_count": 500,
                "industry": "Manufacturing",
            },
            "cached": False,
        }
        return result
    except Exception as e:
        logger.error(f"Company enrichment task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def calculate_lead_score_task(
    self,
    rfq_text: str,
    buyer_company_name: Optional[str],
    parsed_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Task 3.6: Calculate lead score"""
    try:
        # In production, would call LeadScoringEngine
        score = 65
        grade = "B" if score >= 50 else "C"

        result = {
            "success": True,
            "lead_score": score,
            "lead_grade": grade,
            "scores": {
                "intent": 65,
                "company": 60,
                "rfq": 70,
            },
        }
        return result
    except Exception as e:
        logger.error(f"Lead scoring task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def generate_draft_reply_task(
    self,
    parsed_data: Dict[str, Any],
    supplier_profile: Dict[str, Any],
    lead_grade: str,
) -> Dict[str, Any]:
    """Task 3.7: Generate draft reply"""
    try:
        # In production, would call DraftReplyGenerator
        draft = f"Thank you for your RFQ. We can support this project at Grade {lead_grade}."

        result = {
            "success": True,
            "draft_reply": draft,
        }
        return result
    except Exception as e:
        logger.error(f"Draft reply task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


def get_rfq_sync(rfq_id: int) -> Optional[Dict[str, Any]]:
    """Get RFQ data synchronously (wrapper for sync context)"""
    # This would run in sync context via async_to_sync or similar
    # For now, returns mock data
    return {
        "id": rfq_id,
        "description": "Test RFQ",
        "attachment_url": None,
    }


def update_rfq_with_results(
    rfq_id: int,
    parsed_data: Dict[str, Any],
    pdf_vision_data: Optional[Dict[str, Any]],
    lead_score: int,
    lead_grade: str,
    draft_reply: Optional[str],
) -> bool:
    """Update RFQ database record with all analysis results"""
    try:
        # In production, would update the RFQ model in database
        logger.info(
            f"Updated RFQ #{rfq_id}: "
            f"Score={lead_score}, Grade={lead_grade}, "
            f"ParsedFields={len(parsed_data)}, "
            f"HasPDFVision={pdf_vision_data is not None}, "
            f"HasDraftReply={draft_reply is not None}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update RFQ #{rfq_id}: {str(e)}")
        return False


# Task monitoring and reporting
@shared_task
def monitor_pipeline_health() -> Dict[str, Any]:
    """Monitor pipeline task health and statistics"""
    # This would track completed tasks, failures, avg processing time, etc.
    return {
        "status": "healthy",
        "tasks_processed": 0,
        "avg_processing_time_seconds": 0,
    }
