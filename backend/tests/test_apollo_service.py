"""Tests for Apollo.io API service with caching"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from datetime import datetime

from app.services.apollo import ApolloService


@pytest.mark.asyncio
class TestApolloService:
    """Test Apollo.io API service"""

    @pytest.fixture
    async def apollo_service(self):
        """Create Apollo service instance"""
        service = ApolloService()
        service.redis_client = None
        return service

    @pytest.mark.asyncio
    async def test_search_company_by_domain(self, apollo_service):
        """Test searching company by domain"""
        mock_response_data = {
            "organizations": [
                {
                    "id": "org-123",
                    "name": "Test Manufacturing Corp",
                    "domain": "testmanufacturing.com",
                    "employee_count": 500,
                    "employee_count_range": "201-500",
                    "industry": "Manufacturing",
                    "industry_tag": "manufacturing",
                    "revenue": "$50M-$100M",
                    "founded_year": 2010,
                    "city": "Shanghai",
                    "state": "Shanghai",
                    "country": "China",
                    "description": "Leading precision component manufacturer",
                    "website_url": "https://testmanufacturing.com",
                    "technologies": ["CNC", "CAD", "ERP"],
                }
            ]
        }

        with patch.object(apollo_service.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = await apollo_service.search_company(domain="testmanufacturing.com")

            assert result["success"] is True
            assert result["company"]["name"] == "Test Manufacturing Corp"
            assert result["company"]["employee_count"] == 500
            assert result["matched_by"] == "domain"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_company_by_name(self, apollo_service):
        """Test searching company by name"""
        mock_response_data = {
            "organizations": [
                {
                    "id": "org-456",
                    "name": "Advanced Steel Industries",
                    "domain": "advancedsteel.cn",
                    "employee_count": 1200,
                    "industry": "Manufacturing",
                }
            ]
        }

        with patch.object(apollo_service.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = await apollo_service.search_company(company_name="Advanced Steel Industries")

            assert result["success"] is True
            assert result["company"]["name"] == "Advanced Steel Industries"
            assert result["matched_by"] == "name"

    @pytest.mark.asyncio
    async def test_search_company_not_found(self, apollo_service):
        """Test searching for non-existent company"""
        mock_response_data = {"organizations": []}

        with patch.object(apollo_service.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = await apollo_service.search_company(company_name="NonExistentCorp123")

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_search_company_no_inputs(self, apollo_service):
        """Test search with missing inputs"""
        result = await apollo_service.search_company()

        assert result["success"] is False
        assert "Either company_name or domain is required" in result["error"]

    @pytest.mark.asyncio
    async def test_search_company_connection_error(self, apollo_service):
        """Test handling of connection error"""
        with patch.object(apollo_service.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection timeout")

            result = await apollo_service.search_company(domain="test.com")

            assert result["success"] is False
            assert result["error"] == "connection_error"
            assert "message" in result

    @pytest.mark.asyncio
    async def test_search_company_rate_limit_error(self, apollo_service):
        """Test handling of rate limit error"""
        with patch.object(apollo_service.client, "get") as mock_get:
            mock_get.side_effect = Exception("Rate limited")

            result = await apollo_service.search_company(domain="test.com")

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_enrich_company_profile(self, apollo_service):
        """Test company profile enrichment"""
        mock_response_data = {
            "organizations": [
                {
                    "id": "org-789",
                    "name": "Premier Machinery Ltd",
                    "domain": "premiermachinery.com",
                    "employee_count": 2500,
                    "employee_count_range": "1001-5000",
                    "industry": "Manufacturing",
                    "industry_tag": "manufacturing",
                    "sub_industries": ["Heavy Equipment", "Industrial Machinery"],
                    "revenue": "$100M-$500M",
                    "founded_year": 2005,
                    "city": "Shenzhen",
                    "state": "Guangdong",
                    "country": "China",
                    "description": "Global leader in precision machinery manufacturing",
                    "website_url": "https://premiermachinery.com",
                    "linkedin_profile_url": "https://linkedin.com/company/premier-machinery",
                    "technologies": ["CAD", "CNC", "3D Printing", "AI Quality Control"],
                }
            ]
        }

        with patch.object(apollo_service.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = await apollo_service.enrich_company_profile(
                company_name="Premier Machinery Ltd",
                domain="premiermachinery.com",
            )

            assert result["success"] is True
            assert result["company_name"] == "Premier Machinery Ltd"
            assert result["employee_count"] == 2500
            assert result["industry"] == "Manufacturing"
            assert len(result["sub_industries"]) == 2
            assert result["founded_year"] == 2005
            assert len(result["technologies"]) == 4

    @pytest.mark.asyncio
    async def test_cache_hit_on_repeated_search(self, apollo_service):
        """Test that cache returns previously fetched results"""
        company_domain = "testcorp.com"
        mock_response_data = {
            "organizations": [
                {
                    "id": "org-111",
                    "name": "Test Corp",
                    "domain": company_domain,
                    "employee_count": 300,
                }
            ]
        }

        with patch.object(apollo_service.client, "get") as mock_get, \
             patch.object(apollo_service, "redis_client") as mock_redis:

            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            # First call - should hit API
            mock_redis.get.return_value = None
            result1 = await apollo_service.search_company(domain=company_domain)
            assert result1["success"] is True

            # Second call - should hit cache
            cached_data = {
                "success": True,
                "company": mock_response_data["organizations"][0],
                "matched_by": "domain",
            }
            mock_redis.get.return_value = json.dumps(cached_data)

            result2 = await apollo_service.search_company(domain=company_domain)

            # Cache key should be called twice (both searches)
            assert mock_redis.get.call_count == 2

    @pytest.mark.asyncio
    async def test_normalize_company_data(self, apollo_service):
        """Test company data normalization"""
        raw_company = {
            "id": "org-test",
            "name": "Test Manufacturing",
            "domain": "testmfg.com",
            "employee_count": 500,
            "industry": "Manufacturing",
            "revenue": "$50M-$100M",
            "founded_year": 2010,
            "city": "Shanghai",
            "country": "China",
            "technologies": ["CNC", "CAD"],
            "extra_field": "should be excluded",
        }

        normalized = apollo_service._normalize_company_data(raw_company)

        assert normalized["name"] == "Test Manufacturing"
        assert normalized["employee_count"] == 500
        assert "extra_field" not in normalized
        assert normalized["technologies"] == ["CNC", "CAD"]

    @pytest.mark.asyncio
    async def test_cache_key_generation_domain(self, apollo_service):
        """Test cache key generation for domain-based search"""
        cache_key = apollo_service._get_cache_key(
            company_name=None,
            domain="TestCorp.COM",
        )

        assert cache_key == "apollo:company:domain:testcorp.com"

    @pytest.mark.asyncio
    async def test_cache_key_generation_name(self, apollo_service):
        """Test cache key generation for name-based search"""
        cache_key = apollo_service._get_cache_key(
            company_name="Test Manufacturing Inc",
            domain=None,
        )

        assert cache_key == "apollo:company:name:test manufacturing inc"

    @pytest.mark.asyncio
    async def test_clear_cache_success(self, apollo_service):
        """Test clearing cache for a company"""
        with patch.object(apollo_service, "redis_client") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)

            result = await apollo_service.clear_cache(domain="testcorp.com")

            assert result is True
            mock_redis.delete.assert_called_once_with("apollo:company:domain:testcorp.com")

    @pytest.mark.asyncio
    async def test_clear_cache_no_inputs(self, apollo_service):
        """Test clearing cache with no inputs"""
        result = await apollo_service.clear_cache()

        assert result is False

    @pytest.mark.asyncio
    async def test_redis_connection_failure_fallback(self):
        """Test graceful fallback when Redis is unavailable"""
        with patch("app.services.apollo.aioredis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")

            service = ApolloService()

            # Service should still be usable, just without caching
            assert service.redis_client is None

    @pytest.mark.asyncio
    async def test_cache_with_multiple_searches(self, apollo_service):
        """Test caching behavior with multiple company searches"""
        companies = [
            {
                "name": "Company A",
                "domain": "companya.com",
                "employee_count": 100,
            },
            {
                "name": "Company B",
                "domain": "companyb.com",
                "employee_count": 200,
            },
        ]

        with patch.object(apollo_service.client, "get") as mock_get:
            for company in companies:
                mock_response = MagicMock()
                mock_response.json.return_value = {"organizations": [company]}
                mock_get.return_value = mock_response

                result = await apollo_service.search_company(domain=company["domain"])

                assert result["success"] is True
                assert result["company"]["name"] == company["name"]

    @pytest.mark.asyncio
    async def test_company_profile_enrichment_with_all_fields(self, apollo_service):
        """Test enrichment with all available company fields"""
        complete_company = {
            "id": "org-complete",
            "name": "Complete Manufacturing Co",
            "domain": "complete-mfg.com",
            "employee_count": 1500,
            "employee_count_range": "501-1000",
            "industry": "Manufacturing",
            "industry_tag": "manufacturing",
            "sub_industries": ["Precision Components", "Medical Devices"],
            "revenue": "$50M-$100M",
            "founded_year": 2008,
            "city": "Shenzhen",
            "state": "Guangdong",
            "country": "China",
            "description": "Specialized in precision medical device components",
            "website_url": "https://complete-mfg.com",
            "logo_url": "https://complete-mfg.com/logo.png",
            "linkedin_profile_url": "https://linkedin.com/company/complete-mfg",
            "facebook_url": "https://facebook.com/completemfg",
            "twitter_url": "https://twitter.com/completemfg",
            "technologies": ["CNC Machining", "5-axis", "Metrology", "Cleanroom Assembly"],
        }

        with patch.object(apollo_service.client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"organizations": [complete_company]}
            mock_get.return_value = mock_response

            result = await apollo_service.enrich_company_profile(
                company_name="Complete Manufacturing Co",
                domain="complete-mfg.com",
            )

            assert result["success"] is True
            assert result["company_name"] == "Complete Manufacturing Co"
            assert result["employee_count"] == 1500
            assert result["revenue_range"] == "$50M-$100M"
            assert result["location"]["city"] == "Shenzhen"
            assert len(result["technologies"]) == 4
            assert result["raw_data"]["id"] == "org-complete"
