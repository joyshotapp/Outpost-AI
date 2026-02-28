"""Draft reply generation service for RFQ responses with B2B business tone"""

import logging
from typing import Optional, Dict, Any

from app.services.claude import get_claude_service

logger = logging.getLogger(__name__)


class DraftReplyGenerator:
    """Service for generating professional B2B RFQ replies"""

    def __init__(self):
        """Initialize draft reply generator"""
        self.claude_service = get_claude_service()

    async def generate_reply(
        self,
        rfq_data: Dict[str, Any],
        supplier_profile: Dict[str, Any],
        lead_grade: Optional[str] = None,
        include_technical_details: bool = True,
    ) -> Dict[str, Any]:
        """Generate a professional draft reply to an RFQ

        Args:
            rfq_data: Parsed RFQ data including product, quantity, timeline
            supplier_profile: Supplier company information
            lead_grade: Lead quality grade (A, B, C) - affects tone and detail level
            include_technical_details: Whether to include technical capabilities

        Returns:
            Dict with draft reply text and metadata
        """
        try:
            # Get system prompt based on lead grade
            system_prompt = self._get_system_prompt(lead_grade, include_technical_details)

            # Get user prompt with contextual information
            user_prompt = self._build_user_prompt(rfq_data, supplier_profile, lead_grade)

            # Generate reply
            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Track token usage
            self.claude_service.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            reply_text = response.content[0].text

            return {
                "success": True,
                "draft_reply": reply_text,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                "metadata": {
                    "lead_grade": lead_grade,
                    "include_technical": include_technical_details,
                    "reply_length": len(reply_text),
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate draft reply: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def generate_follow_up_reply(
        self,
        original_rfq: Dict[str, Any],
        original_reply: str,
        buyer_followup: str,
        supplier_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a follow-up reply to buyer's questions

        Args:
            original_rfq: Original parsed RFQ data
            original_reply: Previously sent reply
            buyer_followup: Buyer's follow-up question/feedback
            supplier_profile: Supplier company information

        Returns:
            Dict with follow-up reply text
        """
        try:
            system_prompt = """你是一位製造業B2B業務人員，正在回覆採購商的後續提問。

你的目標是：
1. 直接回答採購商的具體問題
2. 提供技術或商業細節
3. 維持友好專業的語氣
4. 推動報價和合作進展

回覆應該清晰、簡潔、專業。"""

            user_prompt = f"""原始詢價單摘要：
{buyer_followup[:500]}

我們之前的回覆：
{original_reply[:500]}

採購商的後續問題/反饋：
{buyer_followup}

請提供一份簡潔的後續回覆（150-250字）。"""

            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            self.claude_service.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return {
                "success": True,
                "follow_up_reply": response.content[0].text,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate follow-up reply: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def refine_draft_reply(
        self,
        draft_reply: str,
        refinement_request: str,
        supplier_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Refine an existing draft reply based on feedback

        Args:
            draft_reply: Original draft reply
            refinement_request: Description of desired changes
            supplier_profile: Supplier information for context

        Returns:
            Dict with refined reply text
        """
        try:
            system_prompt = """你是一位資深B2B業務文案編輯，負責優化製造商的RFQ回覆。

你的任務是根據反饋意見改進回覆文案，同時保持：
1. 專業可信的語氣
2. 清晰有力的溝通
3. 適當的商業禮儀
4. 真誠的合作意願

改進後的文案應該更有說服力和吸引力。"""

            user_prompt = f"""公司背景：{supplier_profile.get('company_name', 'Unknown Company')}

原始草稿：
{draft_reply}

優化要求：
{refinement_request}

請根據優化要求改進上述草稿。"""

            response = self.claude_service.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            self.claude_service.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return {
                "success": True,
                "refined_reply": response.content[0].text,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Failed to refine draft reply: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    def _get_system_prompt(self, lead_grade: Optional[str], include_technical: bool) -> str:
        """Get system prompt based on lead grade and options"""
        base_prompt = """你是一位經驗豐富的B2B製造業業務人員，代表一家製造商回覆來自國際採購商的詢價單。

你的核心職責：
1. 表示感謝並確認收到詢價單
2. 簡要確認對方的主要需求
3. 展示公司的相關能力和經驗
4. 提供有信心的報價承諾
5. 提出後續技術討論和報價步驟
6. 保持友善專業的語氣，展現可靠性

回覆風格：
- 應該用英文撰寫
- 專業但不過於正式或死板
- 真誠表達商業合作的意願
- 簡潔清晰，避免冗長"""

        if lead_grade == "A":
            return base_prompt + """
【針對高質量潛在客戶的特別指示】
這是一個高價值的機會。應該：
- 突出我們在這個行業的專業經驗
- 詳細展示相關的成功案例
- 提供個性化的解決方案想法
- 明確表達對這個項目的熱情
- 提議進行深度技術討論或視頻會議"""

        elif lead_grade == "B":
            return base_prompt + """
【針對中等質量潛在客戶的指示】
這是一個有潛力的機會。應該：
- 介紹我們的核心能力
- 展示相關的生產經驗
- 承諾提供詳細報價和時間表
- 邀請任何技術澄清需要
- 保持專業友善的後續溝通態度"""

        else:  # Grade C or default
            return base_prompt + """
【針對所有潛在客戶的基本指示】
保持標準的專業回覆模式。應該：
- 簡要介紹公司和基本能力
- 確認我們可以處理這類工作
- 承諾後續的詳細報價
- 主動提出問題解答
- 留下聯絡方式供後續跟進"""

        if not include_technical:
            return base_prompt + "\n\n注意：本回覆應該專注於商業層面，不包含詳細的技術規格討論。"

        return base_prompt

    def _build_user_prompt(
        self,
        rfq_data: Dict[str, Any],
        supplier_profile: Dict[str, Any],
        lead_grade: Optional[str],
    ) -> str:
        """Build user prompt with RFQ and supplier context"""
        import json

        prompt = f"""請基於以下信息生成一份RFQ回覆草稿（200-300字）：

【採購商的詢價單摘要】
產品：{rfq_data.get('product_name', 'Not specified')}
數量：{rfq_data.get('quantity', 'Not specified')}
交期：{rfq_data.get('lead_time_days', 'Not specified')} days
特殊要求：{rfq_data.get('special_requirements', 'None')}
認證需求：{rfq_data.get('certifications', 'None')}

【我們公司信息】
公司名稱：{supplier_profile.get('company_name', 'Our Company')}
主營業務：{supplier_profile.get('main_products', 'Manufacturing')}
公司規模：{supplier_profile.get('number_of_employees', 'Moderate size')} employees
主要認證：{supplier_profile.get('certifications', 'ISO certified')}
地區：{supplier_profile.get('country', 'China')}, {supplier_profile.get('city', 'City')}"""

        if lead_grade:
            prompt += f"\n\n【線索等級】{lead_grade}（{'高質量機會' if lead_grade == 'A' else '中等質量' if lead_grade == 'B' else '機會'}）"

        prompt += "\n\n請生成一份真誠、專業、令人信服的回覆。"

        return prompt


# Singleton instance
_draft_reply_generator: Optional[DraftReplyGenerator] = None


def get_draft_reply_generator() -> DraftReplyGenerator:
    """Get or create draft reply generator instance"""
    global _draft_reply_generator
    if _draft_reply_generator is None:
        _draft_reply_generator = DraftReplyGenerator()
    return _draft_reply_generator
