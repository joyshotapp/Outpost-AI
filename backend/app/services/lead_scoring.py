"""Lead scoring engine combining Claude intent analysis + Apollo company scoring"""

import logging
import json
from typing import Optional, Dict, Any, Tuple

from app.services.claude import get_claude_service
from app.services.apollo import get_apollo_service

logger = logging.getLogger(__name__)


class LeadScoringEngine:
    """Engine for scoring manufacturing RFQs and assigning lead grades"""

    # Scoring weights (sum should = 100%)
    INTENT_WEIGHT = 0.40  # 40% from buyer intent analysis
    COMPANY_WEIGHT = 0.35  # 35% from buyer company profile
    RFQ_WEIGHT = 0.25     # 25% from RFQ specifications clarity

    # Grade thresholds
    GRADE_A_THRESHOLD = 70  # A grade: 70+
    GRADE_B_THRESHOLD = 50  # B grade: 50-69
    GRADE_C_THRESHOLD = 0   # C grade: 0-49

    def __init__(self):
        """Initialize scoring engine with Claude and Apollo services"""
        self.claude_service = get_claude_service()
        self.apollo_service = get_apollo_service()

    async def score_rfq(
        self,
        rfq_text: str,
        buyer_company_name: Optional[str] = None,
        buyer_domain: Optional[str] = None,
        parsed_rfq_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Score an RFQ and assign lead grade

        Args:
            rfq_text: Raw RFQ text
            buyer_company_name: Company name of buyer (optional)
            buyer_domain: Domain of buyer company (optional)
            parsed_rfq_data: Already parsed RFQ data (optional)

        Returns:
            Scoring result with lead_score (1-100) and lead_grade (A/B/C)
        """
        scores = {}
        details = {}

        # 1. Analyze buyer intent with Claude
        intent_score, intent_details = await self._score_intent(rfq_text)
        scores["intent"] = intent_score
        details["intent"] = intent_details

        # 2. Score buyer company profile with Apollo
        company_score, company_details = await self._score_company(
            buyer_company_name=buyer_company_name,
            buyer_domain=buyer_domain,
        )
        scores["company"] = company_score
        details["company"] = company_details

        # 3. Score RFQ specification clarity
        rfq_score, rfq_details = self._score_rfq_specifications(
            rfq_text=rfq_text,
            parsed_data=parsed_rfq_data,
        )
        scores["rfq"] = rfq_score
        details["rfq"] = rfq_details

        # 4. Calculate composite lead score
        lead_score = self._calculate_composite_score(scores)

        # 5. Assign lead grade
        lead_grade = self._assign_grade(lead_score)

        return {
            "success": True,
            "lead_score": lead_score,
            "lead_grade": lead_grade,
            "scores": scores,
            "details": details,
            "scoring_breakdown": {
                "intent": {
                    "score": intent_score,
                    "weight": self.INTENT_WEIGHT,
                    "weighted": intent_score * self.INTENT_WEIGHT,
                },
                "company": {
                    "score": company_score,
                    "weight": self.COMPANY_WEIGHT,
                    "weighted": company_score * self.COMPANY_WEIGHT,
                },
                "rfq": {
                    "score": rfq_score,
                    "weight": self.RFQ_WEIGHT,
                    "weighted": rfq_score * self.RFQ_WEIGHT,
                },
            },
        }

    async def _score_intent(self, rfq_text: str) -> Tuple[int, Dict[str, Any]]:
        """Score buyer's intent and urgency using Claude

        Evaluates:
        - Urgency level (1-10)
        - Specification clarity (1-10)
        - Purchase probability (1-10)
        - Budget defined (yes/no)

        Returns:
            (score: 0-100, details: dict)
        """
        try:
            intent_result = await self.claude_service.analyze_intent(rfq_text)

            if isinstance(intent_result, dict):
                urgency = intent_result.get("urgency", 5)
                clarity = intent_result.get("specification_clarity", 5)
                probability = intent_result.get("probability", 5)
                budget = intent_result.get("budget_defined", False)

                # Calculate intent score
                score = (urgency * 0.4 + clarity * 0.3 + probability * 0.3) * 10
                score = min(100, max(0, score))

                return int(score), {
                    "urgency": urgency,
                    "specification_clarity": clarity,
                    "purchase_probability": probability,
                    "budget_defined": budget,
                    "overall": int(score),
                }
            else:
                logger.warning("Invalid intent analysis result")
                return 50, {"error": "Invalid result format"}

        except Exception as e:
            logger.error(f"Failed to score intent: {str(e)}")
            return 50, {"error": str(e)}

    async def _score_company(
        self,
        buyer_company_name: Optional[str],
        buyer_domain: Optional[str],
    ) -> Tuple[int, Dict[str, Any]]:
        """Score buyer company profile using Apollo

        Evaluates:
        - Company size (employee count)
        - Industry match (manufacturing related)
        - Company maturity (founded year)
        - Geographic location

        Returns:
            (score: 0-100, details: dict)
        """
        # Default score if no company info provided
        if not buyer_company_name and not buyer_domain:
            return 50, {"note": "No company information provided"}

        try:
            company_result = await self.apollo_service.enrich_company_profile(
                company_name=buyer_company_name or "Unknown",
                domain=buyer_domain,
            )

            if not company_result.get("success"):
                return 40, {
                    "error": company_result.get("error", "Company not found"),
                    "cached": company_result.get("cached", False),
                }

            # Extract company metrics
            employee_count = company_result.get("employee_count", 0)
            industry = company_result.get("industry", "").lower()
            founded_year = company_result.get("founded_year", 2000)
            technologies = company_result.get("technologies", [])

            # Score components
            size_score = self._score_company_size(employee_count)
            industry_score = self._score_industry_match(industry, technologies)
            maturity_score = self._score_company_maturity(founded_year)
            location_score = 85  # Assume reasonable location if Apollo found it

            # Composite score
            overall = (size_score * 0.3 + industry_score * 0.4 +
                      maturity_score * 0.2 + location_score * 0.1)

            return int(overall), {
                "company_name": company_result.get("company_name"),
                "employee_count": employee_count,
                "industry": industry,
                "founded_year": founded_year,
                "size_score": size_score,
                "industry_score": industry_score,
                "maturity_score": maturity_score,
                "location_score": location_score,
                "overall": int(overall),
                "cached": company_result.get("cached", False),
            }

        except Exception as e:
            logger.error(f"Failed to score company: {str(e)}")
            return 40, {"error": str(e)}

    def _score_rfq_specifications(
        self,
        rfq_text: str,
        parsed_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """Score RFQ specification clarity

        Evaluates:
        - Required fields completeness (product, quantity, specs)
        - Specification detail level
        - Attachment presence (PDFs with drawings)
        - Lead time specificity

        Returns:
            (score: 0-100, details: dict)
        """
        if not rfq_text:
            return 0, {"error": "No RFQ text provided"}

        score = 0
        details = {}

        # Check for key specifications
        has_quantity = "quantity" in rfq_text.lower() or bool(
            parsed_data and parsed_data.get("quantity")
        )
        has_delivery = ("delivery" in rfq_text.lower() or "lead" in rfq_text.lower()) or bool(
            parsed_data and parsed_data.get("lead_time_days")
        )
        has_dimensions = ("dimension" in rfq_text.lower() or "size" in rfq_text.lower()) or bool(
            parsed_data and parsed_data.get("dimensions")
        )
        has_material = "material" in rfq_text.lower() or bool(
            parsed_data and parsed_data.get("materials")
        )
        has_tolerance = "tolerance" in rfq_text.lower() or bool(
            parsed_data and parsed_data.get("tolerances")
        )
        has_attachment = bool(parsed_data and parsed_data.get("pdf_vision_data") is not None)
        has_certifications = ("iso" in rfq_text.lower() or "certification" in rfq_text.lower()) or bool(
            parsed_data and parsed_data.get("certifications")
        )

        # Calculate score (each element = ~14 points)
        score += 14 if has_quantity else 0
        score += 14 if has_delivery else 0
        score += 15 if has_dimensions else 0
        score += 15 if has_material else 0
        score += 15 if has_tolerance else 0
        score += 12 if has_attachment else 0
        score += 13 if has_certifications else 0

        score = min(100, score)

        details = {
            "has_quantity": has_quantity,
            "has_delivery": has_delivery,
            "has_dimensions": has_dimensions,
            "has_material": has_material,
            "has_tolerance": has_tolerance,
            "has_attachment": has_attachment,
            "has_certifications": has_certifications,
            "text_length": len(rfq_text) if rfq_text else 0,
            "overall": score,
        }

        return score, details

    def _score_company_size(self, employee_count: int) -> int:
        """Score company based on employee count

        Preferences:
        - 50-500: Most likely to need subcontracting (90-95)
        - 500-5000: Good prospects (85-90)
        - 5000+: Established buyers (75-85)
        - <50: Micro buyers (60-70)
        """
        if not employee_count:
            return 50

        if 50 <= employee_count <= 500:
            return 92
        elif 500 < employee_count <= 5000:
            return 88
        elif 5000 < employee_count <= 50000:
            return 80
        elif employee_count > 50000:
            return 75
        else:  # < 50
            return 65

    def _score_industry_match(self, industry: str, technologies: list) -> int:
        """Score industry match for manufacturing buyers

        Looks for:
        - Manufacturing-related industries
        - Engineering/production technologies
        """
        score = 50  # Base score

        # Check industry keywords
        manufacturing_keywords = [
            "manufacturing", "production", "engineering", "industrial",
            "automotive", "aerospace", "medical", "electronics", "machinery",
            "metal", "plastic", "chemical", "construction", "consumer goods",
        ]

        if any(keyword in industry for keyword in manufacturing_keywords):
            score = 85

        # Check technology keywords
        tech_keywords = [
            "cnc", "cad", "cam", "erp", "mes", "plm", "autocad", "solidworks",
            "3d", "machining", "casting", "injection", "welding", "assembly",
        ]

        tech_score = sum(1 for tech in technologies
                        if any(keyword in tech.lower() for keyword in tech_keywords))
        tech_boost = min(15, tech_score * 3)
        score = min(100, score + tech_boost)

        return score

    def _score_company_maturity(self, founded_year: int) -> int:
        """Score company maturity based on age

        - Founded <5 years: Startup (60)
        - Founded 5-10 years: Growth (75)
        - Founded 10-20 years: Established (85)
        - Founded >20 years: Mature (90)
        """
        import datetime
        current_year = datetime.datetime.now().year
        years_old = current_year - founded_year

        if years_old < 5:
            return 60
        elif years_old < 10:
            return 75
        elif years_old < 20:
            return 85
        else:
            return 90

    def _calculate_composite_score(self, scores: Dict[str, int]) -> int:
        """Calculate weighted composite score"""
        composite = (
            scores.get("intent", 50) * self.INTENT_WEIGHT +
            scores.get("company", 50) * self.COMPANY_WEIGHT +
            scores.get("rfq", 50) * self.RFQ_WEIGHT
        )
        return min(100, max(0, int(composite)))

    def _assign_grade(self, lead_score: int) -> str:
        """Assign lead grade based on score"""
        if lead_score >= self.GRADE_A_THRESHOLD:
            return "A"
        elif lead_score >= self.GRADE_B_THRESHOLD:
            return "B"
        else:
            return "C"


# Singleton instance
_lead_scoring_engine: Optional[LeadScoringEngine] = None


def get_lead_scoring_engine() -> LeadScoringEngine:
    """Get or create lead scoring engine instance"""
    global _lead_scoring_engine
    if _lead_scoring_engine is None:
        _lead_scoring_engine = LeadScoringEngine()
    return _lead_scoring_engine
