"""Tests for lead scoring engine"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.lead_scoring import LeadScoringEngine


@pytest.mark.asyncio
class TestLeadScoringEngine:
    """Test lead scoring engine"""

    @pytest.fixture
    def lead_scoring_engine(self):
        """Create lead scoring engine instance"""
        return LeadScoringEngine()

    @pytest.mark.asyncio
    async def test_score_rfq_complete(self, lead_scoring_engine):
        """Test scoring an RFQ with all data"""
        rfq_text = """We need 500 pcs of aluminum precision components.
Size 25x10x8mm, tolerance ±0.1mm.
Material: 6061-T6, surface: bright anodize.
Delivery needed within 30 days.
Must have ISO9001 certificate.
Budget: $10,000-$15,000."""

        parsed_data = {
            "quantity": 500,
            "lead_time_days": 30,
            "dimensions": "25x10x8mm",
            "tolerances": "±0.1mm",
            "materials": ["6061-T6"],
            "certifications": ["ISO9001"],
        }

        with patch.object(lead_scoring_engine.claude_service, "analyze_intent") as mock_intent, \
             patch.object(lead_scoring_engine.apollo_service, "enrich_company_profile") as mock_company:

            mock_intent.return_value = {
                "urgency": 7,
                "specification_clarity": 8,
                "purchase_probability": 7,
                "budget_defined": True,
            }

            mock_company.return_value = {
                "success": True,
                "company_name": "Test Buyer Corp",
                "employee_count": 500,
                "industry": "Manufacturing",
                "founded_year": 2010,
                "technologies": ["CAD", "CNC", "ERP"],
            }

            result = await lead_scoring_engine.score_rfq(
                rfq_text=rfq_text,
                buyer_company_name="Test Buyer Corp",
                parsed_rfq_data=parsed_data,
            )

            assert result["success"] is True
            assert 0 <= result["lead_score"] <= 100
            assert result["lead_grade"] in ["A", "B", "C"]
            assert "scores" in result
            assert "details" in result

    @pytest.mark.asyncio
    async def test_score_intent_high_urgency(self, lead_scoring_engine):
        """Test intent scoring with high urgency"""
        rfq_text = "URGENT: Need parts ASAP, within 5 days maximum."

        with patch.object(lead_scoring_engine.claude_service, "analyze_intent") as mock_intent:
            mock_intent.return_value = {
                "urgency": 9,
                "specification_clarity": 6,
                "purchase_probability": 8,
            }

            score, details = await lead_scoring_engine._score_intent(rfq_text)

            assert score > 60
            assert details["urgency"] == 9
            assert details["overall"] > 60

    @pytest.mark.asyncio
    async def test_score_intent_low_clarity(self, lead_scoring_engine):
        """Test intent scoring with low specification clarity"""
        rfq_text = "We might need some parts in the future, not sure yet."

        with patch.object(lead_scoring_engine.claude_service, "analyze_intent") as mock_intent:
            mock_intent.return_value = {
                "urgency": 3,
                "specification_clarity": 2,
                "purchase_probability": 2,
            }

            score, details = await lead_scoring_engine._score_intent(rfq_text)

            assert score < 40
            assert details["specification_clarity"] == 2

    @pytest.mark.asyncio
    async def test_score_company_large_manufacturer(self, lead_scoring_engine):
        """Test company scoring for large manufacturer"""
        with patch.object(lead_scoring_engine.apollo_service, "enrich_company_profile") as mock_company:
            mock_company.return_value = {
                "success": True,
                "company_name": "Fortune 500 Manufacturer",
                "employee_count": 50000,
                "industry": "Manufacturing",
                "founded_year": 1950,
                "technologies": ["CAD", "CNC", "AI Quality Control", "ERP", "MES"],
            }

            score, details = await lead_scoring_engine._score_company(
                buyer_company_name="Fortune 500 Manufacturer",
                buyer_domain=None,
            )

            assert score >= 70  # Should be solid score for large established manufacturer
            assert details["company_name"] == "Fortune 500 Manufacturer"
            assert details["industry"] == "manufacturing"

    @pytest.mark.asyncio
    async def test_score_company_not_found(self, lead_scoring_engine):
        """Test company scoring when company not found in Apollo"""
        with patch.object(lead_scoring_engine.apollo_service, "enrich_company_profile") as mock_company:
            mock_company.return_value = {
                "success": False,
                "error": "Company not found",
            }

            score, details = await lead_scoring_engine._score_company(
                buyer_company_name="NonexistentCorp",
                buyer_domain=None,
            )

            assert score == 40  # Default lower score
            assert "error" in details

    def test_score_rfq_specifications_complete(self, lead_scoring_engine):
        """Test RFQ specification scoring with all details"""
        rfq_text = """Quantity: 1000 units
Dimensions: 100mm x 50mm x 25mm
Tolerance: ±0.5mm
Material: Stainless Steel 304
Surface: Polished
Delivery: 60 days
Certifications: ISO9001, RoHS
Quality: 100% inspection required
Drawing attached."""

        parsed_data = {
            "quantity": 1000,
            "dimensions": "100x50x25mm",
            "tolerances": "±0.5mm",
            "materials": ["Stainless Steel 304"],
            "lead_time_days": 60,
            "certifications": ["ISO9001", "RoHS"],
            "pdf_vision_data": {"extracted": True},
        }

        score, details = lead_scoring_engine._score_rfq_specifications(
            rfq_text=rfq_text,
            parsed_data=parsed_data,
        )

        assert score > 85  # Should have high score with all specs
        assert details["has_quantity"] is True
        assert details["has_delivery"] is True
        assert details["has_dimensions"] is True
        assert details["has_attachment"] is True

    def test_score_rfq_specifications_minimal(self, lead_scoring_engine):
        """Test RFQ specification scoring with minimal details"""
        rfq_text = "We need some parts."

        score, details = lead_scoring_engine._score_rfq_specifications(
            rfq_text=rfq_text,
            parsed_data={},
        )

        assert score == 0  # Should have no score with no specs
        assert details["has_quantity"] is False
        assert details["has_dimensions"] is False

    def test_score_company_size_ranges(self, lead_scoring_engine):
        """Test company size scoring for different employee ranges"""
        # Micro company
        score = lead_scoring_engine._score_company_size(20)
        assert 60 <= score <= 70

        # Small-medium
        score = lead_scoring_engine._score_company_size(200)
        assert 90 <= score <= 95

        # Medium-large
        score = lead_scoring_engine._score_company_size(2000)
        assert 85 <= score <= 90

        # Enterprise
        score = lead_scoring_engine._score_company_size(50000)
        assert 70 <= score <= 85

        # No data
        score = lead_scoring_engine._score_company_size(0)
        assert score == 50

    def test_score_industry_match_manufacturing(self, lead_scoring_engine):
        """Test industry matching for manufacturing companies"""
        # Perfect match
        score = lead_scoring_engine._score_industry_match(
            "manufacturing",
            ["CNC", "CAD", "ERP"],
        )
        assert score >= 85

        # Good match with technologies
        score = lead_scoring_engine._score_industry_match(
            "industrial electronics",
            ["CAD", "CAM"],
        )
        assert score >= 70

        # Non-manufacturing
        score = lead_scoring_engine._score_industry_match(
            "retail",
            [],
        )
        assert score == 50

    def test_score_company_maturity(self, lead_scoring_engine):
        """Test company maturity scoring based on founded year"""
        current_year = datetime.now().year

        # Startup (< 5 years)
        score = lead_scoring_engine._score_company_maturity(current_year - 3)
        assert score == 60

        # Growth (5-10 years)
        score = lead_scoring_engine._score_company_maturity(current_year - 7)
        assert score == 75

        # Established (10-20 years)
        score = lead_scoring_engine._score_company_maturity(current_year - 15)
        assert score == 85

        # Mature (> 20 years)
        score = lead_scoring_engine._score_company_maturity(current_year - 30)
        assert score == 90

    def test_calculate_composite_score(self, lead_scoring_engine):
        """Test composite score calculation"""
        scores = {
            "intent": 80,
            "company": 70,
            "rfq": 90,
        }

        composite = lead_scoring_engine._calculate_composite_score(scores)

        expected = int(80 * 0.40 + 70 * 0.35 + 90 * 0.25)
        assert composite == expected

    def test_assign_grade_a(self, lead_scoring_engine):
        """Test grade A assignment"""
        grade = lead_scoring_engine._assign_grade(75)
        assert grade == "A"

    def test_assign_grade_b(self, lead_scoring_engine):
        """Test grade B assignment"""
        grade = lead_scoring_engine._assign_grade(60)
        assert grade == "B"

    def test_assign_grade_c(self, lead_scoring_engine):
        """Test grade C assignment"""
        grade = lead_scoring_engine._assign_grade(30)
        assert grade == "C"

    @pytest.mark.asyncio
    async def test_score_rfq_no_company_info(self, lead_scoring_engine):
        """Test scoring RFQ without company information"""
        rfq_text = "Need 100 aluminum parts, 50x30x10mm, ±0.1mm tolerance."

        with patch.object(lead_scoring_engine.claude_service, "analyze_intent") as mock_intent:
            mock_intent.return_value = {
                "urgency": 5,
                "specification_clarity": 6,
                "purchase_probability": 5,
            }

            result = await lead_scoring_engine.score_rfq(
                rfq_text=rfq_text,
                buyer_company_name=None,
                buyer_domain=None,
                parsed_rfq_data=None,
            )

            assert result["success"] is True
            assert "lead_score" in result
            # Score should be moderate since company info is missing
            assert result["details"]["company"]["note"] == "No company information provided"

    @pytest.mark.asyncio
    async def test_scoring_weights_sum_to_one(self, lead_scoring_engine):
        """Test that scoring weights sum to 1.0"""
        total_weight = (
            lead_scoring_engine.INTENT_WEIGHT +
            lead_scoring_engine.COMPANY_WEIGHT +
            lead_scoring_engine.RFQ_WEIGHT
        )

        assert abs(total_weight - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_rfq_intent_error_fallback(self, lead_scoring_engine):
        """Test fallback when intent analysis fails"""
        rfq_text = "Need parts ASAP"

        with patch.object(lead_scoring_engine.claude_service, "analyze_intent") as mock_intent, \
             patch.object(lead_scoring_engine.apollo_service, "enrich_company_profile") as mock_company:

            mock_intent.side_effect = Exception("API error")
            mock_company.return_value = {
                "success": False,
                "error": "Not found",
            }

            result = await lead_scoring_engine.score_rfq(
                rfq_text=rfq_text,
                buyer_company_name="Unknown",
            )

            # Should still succeed with fallback scores
            assert result["success"] is True
            assert 0 <= result["lead_score"] <= 100
            assert result["lead_grade"] in ["A", "B", "C"]

    def test_grade_threshold_boundaries(self, lead_scoring_engine):
        """Test grade thresholds at boundary values"""
        # Just below A threshold
        assert lead_scoring_engine._assign_grade(69) == "B"

        # At A threshold
        assert lead_scoring_engine._assign_grade(70) == "A"

        # Just below B threshold
        assert lead_scoring_engine._assign_grade(49) == "C"

        # At B threshold
        assert lead_scoring_engine._assign_grade(50) == "B"
