"""Slack webhook integration for sending RFQ notifications"""

import logging
import json
import aiohttp
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Service for sending notifications to Slack"""

    def __init__(self):
        """Initialize Slack service with webhook URL"""
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured, Slack notifications disabled")

    async def send_lead_notification(
        self,
        rfq_id: int,
        lead_grade: str,
        lead_score: int,
        buyer_company_name: Optional[str],
        product_summary: Optional[str],
        rfq_text_preview: Optional[str],
        scoring_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send A-grade lead notification to Slack

        Args:
            rfq_id: RFQ ID
            lead_grade: Lead grade (A/B/C)
            lead_score: Lead score (0-100)
            buyer_company_name: Name of buying company
            product_summary: Brief product summary
            rfq_text_preview: Preview of RFQ text (first 200 chars)
            scoring_breakdown: Detailed scoring breakdown

        Returns:
            Dict with success status and message ID
        """
        if not self.webhook_url:
            return {
                "success": False,
                "error": "Slack webhook URL not configured",
            }

        if lead_grade != "A":
            logger.info(f"RFQ #{rfq_id} has grade {lead_grade}, skipping Slack notification (only A-grade)")
            return {
                "success": True,
                "skipped": True,
                "reason": f"Lead grade {lead_grade} is not A",
            }

        try:
            message = self._build_lead_message(
                rfq_id=rfq_id,
                lead_grade=lead_grade,
                lead_score=lead_score,
                buyer_company_name=buyer_company_name,
                product_summary=product_summary,
                rfq_text_preview=rfq_text_preview,
                scoring_breakdown=scoring_breakdown,
            )

            result = await self._send_webhook(message)

            if result.get("success"):
                logger.info(f"A-grade lead notification sent for RFQ #{rfq_id} to Slack")

            return result

        except Exception as e:
            logger.error(f"Failed to send Slack notification for RFQ #{rfq_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def send_pipeline_error_notification(
        self,
        rfq_id: int,
        failed_stage: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """Send error notification for failed pipeline stage

        Args:
            rfq_id: RFQ ID
            failed_stage: Name of stage that failed
            error_message: Error details

        Returns:
            Dict with success status
        """
        if not self.webhook_url:
            return {
                "success": False,
                "error": "Slack webhook URL not configured",
            }

        try:
            message = {
                "text": "⚠️ RFQ Pipeline Error",
                "attachments": [
                    {
                        "color": "#ff6b6b",
                        "title": f"Pipeline Error - RFQ #{rfq_id}",
                        "fields": [
                            {
                                "title": "Failed Stage",
                                "value": failed_stage,
                                "short": True,
                            },
                            {
                                "title": "Error",
                                "value": error_message[:300],
                                "short": False,
                            },
                        ],
                        "ts": int(__import__("time").time()),
                    }
                ],
            }

            result = await self._send_webhook(message)

            if result.get("success"):
                logger.info(f"Pipeline error notification sent for RFQ #{rfq_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to send error notification for RFQ #{rfq_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    def _build_lead_message(
        self,
        rfq_id: int,
        lead_grade: str,
        lead_score: int,
        buyer_company_name: Optional[str],
        product_summary: Optional[str],
        rfq_text_preview: Optional[str],
        scoring_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build Slack message payload for A-grade lead"""
        color_map = {
            "A": "#2ecc71",  # Green for A-grade
            "B": "#f39c12",  # Orange for B-grade
            "C": "#e74c3c",  # Red for C-grade
        }

        fields = [
            {
                "title": "RFQ ID",
                "value": f"#{rfq_id}",
                "short": True,
            },
            {
                "title": "Lead Grade",
                "value": lead_grade,
                "short": True,
            },
            {
                "title": "Lead Score",
                "value": f"{lead_score}/100",
                "short": True,
            },
        ]

        if buyer_company_name:
            fields.append({
                "title": "Buyer Company",
                "value": buyer_company_name,
                "short": True,
            })

        if product_summary:
            fields.append({
                "title": "Product",
                "value": product_summary[:150],
                "short": False,
            })

        if rfq_text_preview:
            fields.append({
                "title": "RFQ Preview",
                "value": rfq_text_preview[:200],
                "short": False,
            })

        # Add scoring breakdown if available
        if scoring_breakdown:
            breakdown_str = self._format_scoring_breakdown(scoring_breakdown)
            fields.append({
                "title": "Scoring Breakdown",
                "value": breakdown_str,
                "short": False,
            })

        return {
            "text": f"🎯 High-Quality Lead (Grade A) - RFQ #{rfq_id}",
            "attachments": [
                {
                    "color": color_map[lead_grade],
                    "title": f"RFQ #{rfq_id} - Grade {lead_grade}",
                    "title_link": f"{settings.APP_URL}/rfq/{rfq_id}" if hasattr(settings, 'APP_URL') else None,
                    "fields": fields,
                    "footer": "Outpost AI - RFQ Pipeline",
                    "ts": int(__import__("time").time()),
                }
            ],
        }

    def _format_scoring_breakdown(self, scoring_breakdown: Dict[str, Any]) -> str:
        """Format scoring breakdown for Slack message"""
        lines = []

        if "intent" in scoring_breakdown:
            intent = scoring_breakdown["intent"]
            lines.append(f"Intent: {intent.get('score', 0)}/100 ({intent.get('weight', 0)*100:.0f}%)")

        if "company" in scoring_breakdown:
            company = scoring_breakdown["company"]
            lines.append(f"Company: {company.get('score', 0)}/100 ({company.get('weight', 0)*100:.0f}%)")

        if "rfq" in scoring_breakdown:
            rfq = scoring_breakdown["rfq"]
            lines.append(f"RFQ: {rfq.get('score', 0)}/100 ({rfq.get('weight', 0)*100:.0f}%)")

        return "\n".join(lines) if lines else "N/A"

    async def _send_webhook(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to Slack webhook

        Args:
            message: Slack message payload

        Returns:
            Dict with success status and optional message_ts
        """
        if not self.webhook_url:
            return {
                "success": False,
                "error": "Webhook URL not configured",
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return {
                            "success": True,
                            "message_ts": response_data.get("ts"),
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack webhook error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "details": error_text[:200],
                        }

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Slack webhook connection error: {str(e)}")
            return {
                "success": False,
                "error": "connection_error",
                "message": str(e),
            }

        except aiohttp.ClientSSLError as e:
            logger.error(f"Slack webhook SSL error: {str(e)}")
            return {
                "success": False,
                "error": "ssl_error",
                "message": str(e),
            }

        except aiohttp.ClientError as e:
            logger.error(f"Slack webhook client error: {str(e)}")
            return {
                "success": False,
                "error": "client_error",
                "message": str(e),
            }

        except Exception as e:
            logger.error(f"Unexpected Slack webhook error: {str(e)}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": str(e),
            }


# Singleton instance
_slack_service: Optional[SlackService] = None


def get_slack_service() -> SlackService:
    """Get or create Slack service instance"""
    global _slack_service
    if _slack_service is None:
        _slack_service = SlackService()
    return _slack_service
