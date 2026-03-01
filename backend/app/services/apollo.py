"""Apollo.io API wrapper for company background queries with caching"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from redis import asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class ApolloService:
    """Service for Apollo.io API integration with caching"""

    # API Configuration
    BASE_URL = "https://api.apollo.io/v1"
    REQUEST_TIMEOUT = 10  # seconds

    # Cache Configuration
    CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours
    CACHE_KEY_PREFIX = "apollo:company"

    def __init__(self):
        """Initialize Apollo service with Redis cache"""
        self.api_key = settings.APOLLO_API_KEY
        self.client = httpx.AsyncClient(
            timeout=self.REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )

        # Initialize async Redis client for caching (connection is lazy — no sync ping needed)
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            logger.info("Async Redis client initialized for Apollo caching")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {str(e)}. Caching disabled.")
            self.redis_client = None

    async def search_company(
        self,
        company_name: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for company information

        Args:
            company_name: Company name to search
            domain: Company domain (more reliable for exact matches)

        Returns:
            Company information from Apollo or cache
        """
        # Validate inputs
        if not company_name and not domain:
            return {
                "success": False,
                "error": "Either company_name or domain is required",
            }

        # Check cache first
        cache_key = self._get_cache_key(company_name, domain)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for {cache_key}")
            return cached_result

        try:
            # Prepare request
            params = {}
            if domain:
                params["domain"] = domain
            if company_name:
                params["name"] = company_name

            # Call Apollo API
            response = await self.client.get(
                f"{self.BASE_URL}/companies/search",
                params=params,
                headers={"X-Api-Key": self.api_key},
            )

            response.raise_for_status()
            data = response.json()

            # Extract company info
            if data.get("organizations") and len(data["organizations"]) > 0:
                company = data["organizations"][0]
                result = {
                    "success": True,
                    "company": self._normalize_company_data(company),
                    "matched_by": "domain" if domain else "name",
                    "cached": False,
                }
            else:
                result = {
                    "success": False,
                    "error": "Company not found",
                }

            # Cache successful results
            if result.get("success"):
                await self._set_cache(cache_key, result)

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Apollo API HTTP error: {str(e)}")
            if e.response.status_code == 401:
                return {
                    "success": False,
                    "error": "unauthorized",
                    "message": "Invalid Apollo API key",
                }
            elif e.response.status_code == 429:
                return {
                    "success": False,
                    "error": "rate_limited",
                    "message": "Apollo API rate limit exceeded",
                }
            else:
                return {
                    "success": False,
                    "error": "api_error",
                    "message": f"Apollo API error: {str(e)}",
                }

        except Exception as e:
            logger.error(f"Failed to search company: {str(e)}")
            return {
                "success": False,
                "error": "connection_error",
                "message": f"Failed to connect to Apollo API: {str(e)}",
            }

    async def enrich_company_profile(
        self,
        company_name: str,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich company profile with Apollo data

        Returns detailed company information including:
        - Company size (employee count)
        - Industry and sub-industry
        - Founded year
        - Revenue estimates
        - Technologies used
        - Company description
        - Key metrics
        """
        result = await self.search_company(
            company_name=company_name,
            domain=domain,
        )

        if not result.get("success"):
            return result

        company = result["company"]

        # Extract enrichment data
        enriched = {
            "success": True,
            "company_name": company.get("name"),
            "domain": company.get("domain"),
            "employee_count": company.get("employee_count"),
            "employee_count_range": company.get("employee_count_range"),
            "industry": company.get("industry"),
            "industry_tag": company.get("industry_tag"),
            "sub_industries": company.get("sub_industries"),
            "revenue_range": company.get("revenue"),
            "founded_year": company.get("founded_year"),
            "location": {
                "city": company.get("city"),
                "state": company.get("state"),
                "country": company.get("country"),
            },
            "description": company.get("description"),
            "website_url": company.get("website_url"),
            "linkedin_profile_url": company.get("linkedin_profile_url"),
            "technologies": company.get("technologies", []),
            "raw_data": company,
        }

        return enriched

    def _normalize_company_data(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Apollo company data to consistent format

        Args:
            company: Raw company data from Apollo API

        Returns:
            Normalized company data
        """
        return {
            "id": company.get("id"),
            "name": company.get("name"),
            "domain": company.get("domain"),
            "employee_count": company.get("employee_count"),
            "employee_count_range": company.get("employee_count_range"),
            "industry": company.get("industry"),
            "industry_tag": company.get("industry_tag"),
            "sub_industries": company.get("sub_industries"),
            "revenue": company.get("revenue"),
            "founded_year": company.get("founded_year"),
            "city": company.get("city"),
            "state": company.get("state"),
            "country": company.get("country"),
            "description": company.get("description"),
            "website_url": company.get("website_url"),
            "logo_url": company.get("logo_url"),
            "linkedin_profile_url": company.get("linkedin_profile_url"),
            "facebook_url": company.get("facebook_url"),
            "twitter_url": company.get("twitter_url"),
            "technologies": company.get("technologies", []),
        }

    def _get_cache_key(
        self,
        company_name: Optional[str],
        domain: Optional[str],
    ) -> str:
        """Generate cache key for company search result

        Args:
            company_name: Company name
            domain: Company domain

        Returns:
            Cache key string
        """
        # Prefer domain as it's more reliable
        if domain:
            return f"{self.CACHE_KEY_PREFIX}:domain:{domain.lower()}"
        else:
            return f"{self.CACHE_KEY_PREFIX}:name:{company_name.lower()}"

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from Redis cache

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                result["cached"] = True
                return result
        except Exception as e:
            logger.warning(f"Failed to get from cache: {str(e)}")

        return None

    async def _set_cache(
        self,
        cache_key: str,
        value: Dict[str, Any],
    ) -> bool:
        """Set result in Redis cache

        Args:
            cache_key: Cache key
            value: Value to cache

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(value, ensure_ascii=False),
            )
            logger.info(f"Cached result for {cache_key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache: {str(e)}")
            return False

    async def clear_cache(self, company_name: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """Clear cache entry for a company

        Args:
            company_name: Company name
            domain: Company domain

        Returns:
            Success status
        """
        if not self.redis_client or (not company_name and not domain):
            return False

        try:
            cache_key = self._get_cache_key(company_name, domain)
            deleted = await self.redis_client.delete(cache_key)
            if deleted:
                logger.info(f"Cleared cache for {cache_key}")
            return bool(deleted)
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_apollo_service: Optional[ApolloService] = None


def get_apollo_service() -> ApolloService:
    """Get or create Apollo service instance"""
    global _apollo_service
    if _apollo_service is None:
        _apollo_service = ApolloService()
    return _apollo_service
