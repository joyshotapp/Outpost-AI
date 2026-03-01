"""Celery tasks for RFQ processing pipeline orchestration"""

import asyncio
import concurrent.futures
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from celery import shared_task
from sqlalchemy import select

from app.database import async_session_maker
from app.models.rfq import RFQ
from app.services.claude import get_claude_service
from app.services.apollo import get_apollo_service
from app.services.lead_scoring import get_lead_scoring_engine
from app.services.draft_reply_generator import get_draft_reply_generator
from app.services.slack import get_slack_service

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task context.

    Handles both standard (prefork) and async-based (gevent/eventlet) Celery workers
    by detecting whether an event loop is already running and spawning a thread if so.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


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
                "company_name": company_data.get("company_name") if company_data else None,
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

        # Send Slack notification for A-grade leads
        if lead_grade == "A":
            try:
                slack_service = get_slack_service()
                slack_result = _run_async(slack_service.send_lead_notification(
                    rfq_id=rfq_id,
                    lead_grade=lead_grade,
                    lead_score=lead_score,
                    buyer_company_name=parsed_data.get("buyer_company"),
                    product_summary=parsed_data.get("product_name"),
                    rfq_text_preview=rfq.description[:200] if rfq.description else None,
                    scoring_breakdown=pipeline_results["stages"]["scoring"].get("breakdown"),
                ))
                pipeline_results["slack_notification"] = slack_result
                if slack_result.get("success"):
                    logger.info(f"Slack notification sent for A-grade RFQ #{rfq_id}")
            except Exception as e:
                logger.error(f"Failed to send Slack notification for RFQ #{rfq_id}: {str(e)}")
                pipeline_results["slack_notification"] = {
                    "success": False,
                    "error": str(e),
                }

        return pipeline_results

    except Exception as e:
        logger.error(f"RFQ pipeline failed for #{rfq_id}: {str(e)}")

        # Send error notification to Slack
        try:
            slack_service = get_slack_service()
            _run_async(slack_service.send_pipeline_error_notification(
                rfq_id=rfq_id,
                failed_stage="complete_pipeline",
                error_message=str(e),
            ))
        except Exception as slack_error:
            logger.error(f"Failed to send error notification for RFQ #{rfq_id}: {str(slack_error)}")

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def parse_rfq_text_task(self, rfq_text: str) -> Dict[str, Any]:
    """Task 3.3: Parse RFQ text with Claude"""
    try:
        claude_service = get_claude_service()
        result = _run_async(claude_service.analyze_rfq_text(rfq_text))
        return result
    except Exception as e:
        logger.error(f"Text parsing task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
def analyze_rfq_pdf_task(self, attachment_url: str, rfq_text: str) -> Dict[str, Any]:
    """Task 3.4: Analyze PDF with vision and Textract"""
    try:
        # Extract S3 object key from presigned URL path component
        parsed = urlparse(attachment_url)
        s3_key = parsed.path.lstrip('/')

        logger.info(f"Analyzing PDF from S3 key: {s3_key[:50]}...")

        claude_service = get_claude_service()
        result = _run_async(claude_service.analyze_rfq_pdf(s3_key, rfq_text))
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

        apollo_service = get_apollo_service()
        result = _run_async(apollo_service.enrich_company_profile(company_name))
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
        scoring_engine = get_lead_scoring_engine()
        result = _run_async(scoring_engine.score_rfq(
            rfq_text=rfq_text,
            buyer_company_name=buyer_company_name,
            parsed_rfq_data=parsed_data,
        ))
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
        generator = get_draft_reply_generator()
        result = _run_async(generator.generate_reply(
            rfq_data=parsed_data,
            supplier_profile=supplier_profile,
            lead_grade=lead_grade,
        ))
        return result
    except Exception as e:
        logger.error(f"Draft reply task failed: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


async def _get_rfq_async(rfq_id: int) -> Optional[RFQ]:
    """Fetch RFQ from database asynchronously."""
    async with async_session_maker() as session:
        result = await session.get(RFQ, rfq_id)
        return result


def get_rfq_sync(rfq_id: int) -> Optional[RFQ]:
    """Get RFQ record synchronously for Celery task context."""
    return _run_async(_get_rfq_async(rfq_id))


async def _update_rfq_async(
    rfq_id: int,
    parsed_data: Optional[Dict[str, Any]],
    pdf_vision_data: Optional[Dict[str, Any]],
    lead_score: int,
    lead_grade: str,
    draft_reply: Optional[str],
) -> bool:
    """Update RFQ database record asynchronously."""
    async with async_session_maker() as session:
        rfq = await session.get(RFQ, rfq_id)
        if not rfq:
            logger.error(f"RFQ #{rfq_id} not found for update")
            return False

        if parsed_data:
            rfq.parsed_data = json.dumps(parsed_data, ensure_ascii=False)
        if pdf_vision_data:
            rfq.pdf_vision_data = json.dumps(pdf_vision_data, ensure_ascii=False)
        rfq.lead_score = lead_score
        rfq.lead_grade = lead_grade
        if draft_reply:
            rfq.draft_reply = draft_reply

        await session.commit()
        logger.info(
            f"Updated RFQ #{rfq_id}: "
            f"Score={lead_score}, Grade={lead_grade}, "
            f"ParsedFields={len(parsed_data) if parsed_data else 0}, "
            f"HasPDFVision={pdf_vision_data is not None}, "
            f"HasDraftReply={draft_reply is not None}"
        )
        return True


def update_rfq_with_results(
    rfq_id: int,
    parsed_data: Optional[Dict[str, Any]],
    pdf_vision_data: Optional[Dict[str, Any]],
    lead_score: int,
    lead_grade: str,
    draft_reply: Optional[str],
) -> bool:
    """Update RFQ database record with all analysis results."""
    try:
        return _run_async(_update_rfq_async(
            rfq_id=rfq_id,
            parsed_data=parsed_data,
            pdf_vision_data=pdf_vision_data,
            lead_score=lead_score,
            lead_grade=lead_grade,
            draft_reply=draft_reply,
        ))
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
