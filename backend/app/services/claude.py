"""Claude API wrapper with Anthropic SDK, retry logic, and token tracking"""

import logging
import json
import base64
import io
from typing import Optional, Dict, Any, List
from datetime import datetime

import anthropic
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError
import boto3
from botocore.exceptions import ClientError
from pdf2image import convert_from_bytes

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeAPITracker:
    """Track Claude API usage and costs"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        self.start_time = datetime.utcnow()

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Record token usage from API call"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_calls += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": self._estimate_cost(),
            "start_time": self.start_time.isoformat(),
        }

    def _estimate_cost(self) -> float:
        """Estimate API cost based on token usage

        Prices as of March 2026:
        - Input: $3 per 1M tokens
        - Output: $15 per 1M tokens
        """
        input_cost = (self.total_input_tokens / 1_000_000) * 3
        output_cost = (self.total_output_tokens / 1_000_000) * 15
        return round(input_cost + output_cost, 4)


class ClaudeService:
    """Service for Claude API interactions with retry logic"""

    # Pricing per 1M tokens (as of March 2026)
    INPUT_PRICE_PER_1M = 3.0
    OUTPUT_PRICE_PER_1M = 15.0

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1

    # PDF processing config
    MAX_IMAGES_PER_PDF = 10  # Limit to first 10 pages for cost efficiency
    IMAGE_QUALITY = 150  # DPI for PDF to image conversion

    def __init__(self):
        """Initialize Claude client"""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.tracker = ClaudeAPITracker()
        self.textract_client = boto3.client(
            "textract",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    async def analyze_rfq_text(
        self,
        rfq_text: str,
        supplier_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze RFQ text using Claude API with manufacturing-specific prompt

        Args:
            rfq_text: Raw RFQ text from buyer
            supplier_context: Optional supplier context for personalization

        Returns:
            Dict with parsed RFQ data
        """
        system_prompt = """你是一位專業製造業採購顧問，擅長解析國際詢價單 (RFQ)。

你的任務是從詢價單中精確提取關鍵製造規格資訊。

【必須提取的字段】
1. product_name (產品名稱): 產品的完整名稱或簡稱
2. materials (材料): 所有提及的材料，可能包括 MATERIAL GRADE、牌號、規格等。返回為陣列
3. dimensions (尺寸): 提取所有尺寸數據，可能包括：
   - 長x寬x高 (Length x Width x Height)
   - 直徑 (Diameter)
   - 厚度 (Thickness)
   - 其他相關尺寸
   返回為對象或字符串，保留單位
4. tolerances (公差): 如 ±0.05mm, ±1mm, IT6 等，返回為字符串或陣列
5. surface_finish (表面處理): 如 RAW、磨砂、拋光、鍍鋅、電鍍、噴漆、陽極化等
6. quantity (數量): 詢價的數量
7. unit (單位): 如 PCS (件), KG (公斤), M (米) 等
8. lead_time_days (交期): 要求的交貨時間（天數），如果提及"ASAP"、"Urgent"、"Rush"等，評估為短期
9. certifications (認證): 如 ISO9001, CE, UL, RoHS, FDA 等，返回為陣列
10. special_requirements (特殊要求): 包括防銹、包裝、檢測要求、文件要求等
11. budget_range (預算): 如有提及的預算/成本目標，返回為字符串
12. application (應用): 產品最終應用場景或行業

【提取規則】
- 只提取文本中明確提及的信息，不做猜測
- 如果字段沒有信息，設為 null
- 保留單位和數值完整性
- 對於模糊的技術術語，保持原文
- 如果有單位混淆的跡象（如"1000 pieces"与"1000"），統一為數字
- 返回標准 JSON 格式

【範例 RFQ】
範例："We need 500 pcs of aluminum precision components, size 25x10x8mm, tolerance ±0.1mm, surface: bright anodize, material: 6061-T6, delivery needed within 30 days, must have ISO9001 certificate"
預期輸出：
{
  "product_name": "aluminum precision components",
  "materials": ["6061-T6"],
  "dimensions": "25x10x8mm",
  "tolerances": "±0.1mm",
  "surface_finish": "bright anodize",
  "quantity": 500,
  "unit": "pcs",
  "lead_time_days": 30,
  "certifications": ["ISO9001"],
  "special_requirements": null,
  "budget_range": null,
  "application": null
}
"""

        user_prompt = f"""請解析以下 RFQ 文本：

{rfq_text}

{f"買家背景：{supplier_context}" if supplier_context else ""}

請提取結構化信息並以 JSON 格式回應。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Track token usage
            self.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            logger.info(
                f"Claude API call succeeded - "
                f"Input: {response.usage.input_tokens}, "
                f"Output: {response.usage.output_tokens}"
            )

            # Parse response
            content = response.content[0].text
            try:
                # Try to extract JSON from response
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                # If direct parse fails, try to find JSON in the response
                import re
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                else:
                    # Return raw content if no JSON found
                    parsed_data = {"raw_response": content}

            return {
                "success": True,
                "parsed_data": parsed_data,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            }

        except RateLimitError as e:
            logger.warning(f"Rate limited by Claude API: {str(e)}")
            return {
                "success": False,
                "error": "rate_limited",
                "message": "Claude API rate limit exceeded. Please try again later.",
            }
        except APIConnectionError as e:
            logger.error(f"Connection error with Claude API: {str(e)}")
            return {
                "success": False,
                "error": "connection_error",
                "message": "Failed to connect to Claude API.",
            }
        except APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            return {
                "success": False,
                "error": "api_error",
                "message": f"Claude API error: {str(e)}",
            }

    async def generate_draft_reply(
        self,
        rfq_data: Dict[str, Any],
        supplier_profile: Dict[str, Any],
    ) -> str:
        """Generate draft reply based on RFQ and supplier profile

        Args:
            rfq_data: Parsed RFQ data
            supplier_profile: Supplier company information

        Returns:
            Draft reply text
        """
        system_prompt = """你是一位經驗豐富的 B2B 業務人員，代表製造廠商回覆來自國際採購商的詢價單。

你的責任是：
1. 確認已收到詢價單並感謝對方的信任
2. 簡潔確認對方的主要需求
3. 介紹你的公司能力和相關經驗
4. 承諾提供報價和技術方案
5. 詢問是否需要額外信息或技術討論
6. 友善、專業的語氣，彰顯可靠性

回複應該是英文，專業但不過於正式，展現真誠的商業意圖。"""

        user_prompt = f"""詢價單內容摘要：
{json.dumps(rfq_data, indent=2, ensure_ascii=False)}

我們公司資訊：
{json.dumps(supplier_profile, indent=2, ensure_ascii=False)}

請幫我生成一份簡潔的回覆草稿（200-300字）。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            self.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Failed to generate draft reply: {str(e)}")
            raise

    async def analyze_intent(self, rfq_text: str) -> Dict[str, Any]:
        """Analyze buyer's intent and urgency from RFQ text

        Args:
            rfq_text: RFQ text

        Returns:
            Intent analysis with urgency score
        """
        system_prompt = """分析以下詢價單買家的商業意圖，評估以下維度：

1. 規格具體度 (specification_clarity): 1-10，越高表示規格越詳細明確
2. 數量確定性 (quantity_certainty): 1-10，越高表示數量越明確
3. 急迫性 (urgency): 1-10，越高表示越急迫
4. 企業規模 (company_scale_apparent): 1-10，根據詢價方式推測

回應為 JSON 格式。"""

        user_prompt = f"""分析此詢價單：{rfq_text}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            self.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            content = response.content[0].text
            try:
                intent_data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                intent_data = (
                    json.loads(json_match.group())
                    if json_match
                    else {"raw_response": content}
                )

            return intent_data

        except Exception as e:
            logger.error(f"Failed to analyze intent: {str(e)}")
            return {}

    async def extract_pdf_from_s3(self, s3_object_key: str) -> Optional[bytes]:
        """Extract PDF file from S3

        Args:
            s3_object_key: S3 object key path

        Returns:
            PDF file content as bytes, or None if failed
        """
        try:
            response = self.s3_client.get_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_object_key
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to extract PDF from S3: {str(e)}")
            return None

    async def convert_pdf_to_images(self, pdf_content: bytes) -> List[str]:
        """Convert PDF pages to base64-encoded images

        Args:
            pdf_content: PDF file content as bytes

        Returns:
            List of base64-encoded images
        """
        try:
            # Convert PDF pages to PIL images
            images = convert_from_bytes(
                pdf_content,
                dpi=self.IMAGE_QUALITY,
                first_page=1,
                last_page=self.MAX_IMAGES_PER_PDF,
            )

            # Convert images to base64
            base64_images = []
            for image in images:
                # Convert PIL image to bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                # Encode to base64
                b64_image = base64.standard_b64encode(img_bytes.getvalue()).decode()
                base64_images.append(b64_image)

            logger.info(f"Converted {len(base64_images)} PDF pages to images")
            return base64_images

        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            return []

    async def analyze_pdf_with_vision(self, base64_images: List[str]) -> Dict[str, Any]:
        """Analyze PDF images using Claude Vision

        Args:
            base64_images: List of base64-encoded images

        Returns:
            Vision analysis results
        """
        if not base64_images:
            return {"success": False, "error": "No images provided"}

        try:
            # Build image messages
            image_messages = []
            for idx, b64_image in enumerate(base64_images):
                image_messages.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64_image,
                    },
                })

            # Add text prompt
            image_messages.append({
                "type": "text",
                "text": """請分析這些製造業技術圖紙和文檔。提取以下信息：

1. 尺寸和規格（包括長/寬/高/直徑等）
2. 材料和材質等級（如果可見）
3. 表面處理和涂層（如電鍍、陽極化等）
4. 公差和精度要求
5. 特殊製造工藝或要求
6. 質量標準或認證標記
7. 任何可識別的零件編號或型號
8. 裝配或功能說明（如果適用）

返回結構化JSON格式：
{
  "dimensions": {...},
  "materials": {...},
  "surface_finish": {...},
  "tolerances": {...},
  "special_requirements": [...],
  "certifications": [...],
  "part_numbers": [...],
  "assembly_notes": [...],
  "confidence_level": 0.0-1.0,
  "notes": "..."
}"""
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": image_messages,
                    }
                ],
            )

            # Track token usage
            self.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            # Parse response
            content = response.content[0].text
            try:
                vision_data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                vision_data = (
                    json.loads(json_match.group())
                    if json_match
                    else {"raw_response": content}
                )

            return {
                "success": True,
                "vision_data": vision_data,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Failed to analyze PDF with vision: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def extract_text_with_textract(
        self, s3_object_key: str
    ) -> Dict[str, Any]:
        """Extract text from PDF using AWS Textract

        Args:
            s3_object_key: S3 object key path

        Returns:
            Extracted text and metadata
        """
        try:
            # Call Textract asynchronously
            response = self.textract_client.start_document_text_detection(
                DocumentLocation={
                    "S3Object": {
                        "Bucket": settings.AWS_S3_BUCKET,
                        "Name": s3_object_key,
                    }
                }
            )

            job_id = response["JobId"]
            logger.info(f"Started Textract job: {job_id}")

            # For now, return job ID for async processing
            # In production, would poll or use SNS notification
            return {
                "success": True,
                "job_id": job_id,
                "status": "processing",
            }

        except ClientError as e:
            logger.error(f"Failed to start Textract job: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def analyze_rfq_pdf(
        self,
        s3_object_key: str,
        rfq_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze RFQ PDF with vision and OCR

        Args:
            s3_object_key: S3 path to RFQ PDF
            rfq_text: Optional extracted text from PDF

        Returns:
            Combined analysis from vision and text extraction
        """
        try:
            # Extract PDF from S3
            pdf_content = await self.extract_pdf_from_s3(s3_object_key)
            if not pdf_content:
                return {
                    "success": False,
                    "error": "Failed to extract PDF from S3",
                }

            # Convert PDF to images for vision analysis
            base64_images = await self.convert_pdf_to_images(pdf_content)

            # Analyze with Claude Vision
            vision_result = await self.analyze_pdf_with_vision(base64_images)

            # Start Textract for OCR
            textract_result = await self.extract_text_with_textract(s3_object_key)

            # Combine results
            combined_analysis = {
                "success": True,
                "vision_analysis": vision_result.get("vision_data"),
                "textract_job_id": textract_result.get("job_id"),
                "textract_status": textract_result.get("status"),
                "tokens_used": vision_result.get("tokens_used"),
                "pages_analyzed": len(base64_images),
            }

            # If RFQ text provided, enhance with text analysis
            if rfq_text:
                text_analysis = await self.analyze_rfq_text(rfq_text)
                if text_analysis.get("success"):
                    combined_analysis["text_analysis"] = text_analysis.get("parsed_data")

            return combined_analysis

        except Exception as e:
            logger.error(f"Failed to analyze RFQ PDF: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def generate_linkedin_opener(
        self,
        full_name: str,
        company_name: str,
        job_title: str,
        industry: str = "",
        seniority: str = "",
        max_chars: int = 300,
    ) -> str:
        """Generate a personalised LinkedIn connection request message (opener).

        The opener must:
        - Address the person by first name only
        - Reference their role / company naturally
        - Mention a relevant pain point for manufacturing buyers
        - Feel human, NOT AI-generated
        - Be ≤ 300 characters (LinkedIn connection note limit)

        Returns the opener string, or a safe fallback if the API is unavailable.
        """
        if not settings.ANTHROPIC_API_KEY:
            first = full_name.split()[0] if full_name else "there"
            return (
                f"Hi {first}, I came across {company_name} and would love to connect "
                "to share how we help manufacturing teams source faster. Cheers!"
        )[:max_chars]

        prompt = (
            f"Write a LinkedIn connection request note for:\n"
            f"  Name: {full_name}\n"
            f"  Title: {job_title} at {company_name}\n"
            f"  Industry: {industry}\n"
            f"  Seniority: {seniority}\n\n"
            "Requirements:\n"
            "- Use first name only\n"
            "- Max 300 characters (absolutely critical)\n"
            "- Sound natural and human, NOT like AI\n"
            "- Reference a real manufacturing sourcing challenge\n"
            "- DO NOT start with 'Hi, I noticed...' or generic intros\n"
            "- Output ONLY the message text, no quotes, no explanation"
        )

        try:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=120,
                messages=[{"role": "user", "content": prompt}],
            )
            self.tracker.add_usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            opener = response.content[0].text.strip()
            # Hard truncate to LinkedIn limit
            return opener[:max_chars]
        except Exception as exc:
            logger.warning("generate_linkedin_opener failed: %s", exc)
            first = full_name.split()[0] if full_name else "there"
            return (
                f"Hi {first}, impressed by {company_name}'s work in {industry}. "
                "Would love to connect and explore synergies in manufacturing sourcing."
            )[:max_chars]

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        return self.tracker.get_stats()

    def reset_tracker(self):
        """Reset usage tracker"""
        self.tracker = ClaudeAPITracker()


# Singleton instance
_claude_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance"""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service
