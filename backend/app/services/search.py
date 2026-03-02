"""Elasticsearch search service — Sprint 10 (Task 10.1).

Responsibilities:
  10.1  Index supplier profiles into Elasticsearch
  10.2  Full-text search + multi-dimensional filters (industry/country/certs)
        with sub-200ms response target (deterministic stub when ES unavailable)

Design decisions:
  - Stub mode when ES is unreachable (dev/test environments without ES running)
  - Index mapping uses `keyword` sub-fields for exact filtering and
    `text` for full-text multi-match queries
  - Autocomplete uses ES prefix-match on `suggest` completion field
  - `index_supplier()` is idempotent (upsert via ES document ID = supplier.id)
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# ── Index mapping ─────────────────────────────────────────────────────────────

SUPPLIER_INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "edge_ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"],
                },
            },
            "tokenizer": {
                "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"],
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "company_name": {
                "type": "text",
                "analyzer": "edge_ngram_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "company_slug": {"type": "keyword"},
            "company_description": {"type": "text"},
            "main_products": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "certifications": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "industry": {"type": "keyword"},
            "country": {"type": "keyword"},
            "city": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "is_verified": {"type": "boolean"},
            "is_active": {"type": "boolean"},
            "manufacturing_capacity": {"type": "text"},
            "lead_time_days": {"type": "integer"},
            "number_of_employees": {"type": "integer"},
            "established_year": {"type": "integer"},
            "view_count": {"type": "integer"},
            # Completion suggester
            "suggest": {"type": "completion"},
        }
    },
}

# ── Stub helpers ──────────────────────────────────────────────────────────────

_STUB_SUPPLIERS: list[dict[str, Any]] = [
    {
        "id": i + 1,
        "company_name": name,
        "company_slug": name.lower().replace(" ", "-"),
        "company_description": f"Leading {ind} manufacturer with ISO 9001 certification.",
        "main_products": products,
        "certifications": "ISO 9001,ISO 14001",
        "industry": ind,
        "country": country,
        "city": city,
        "is_verified": True,
        "is_active": True,
        "manufacturing_capacity": "5000 units/month",
        "lead_time_days": 14,
        "number_of_employees": 200,
        "established_year": 2005,
        "view_count": 100 + i * 17,
    }
    for i, (name, ind, country, city, products) in enumerate([
        ("Precision Parts Co", "Automotive", "DE", "Stuttgart", "CNC parts,Molds"),
        ("TechForge GmbH", "Electronics", "DE", "Munich", "PCB assemblies,Enclosures"),
        ("AsiaMetals Ltd", "Metals", "CN", "Shenzhen", "Castings,Stampings"),
        ("AutoPlast Taiwan", "Plastics", "TW", "Taichung", "Injection molding,Rubber parts"),
        ("Nordic Precision", "Aerospace", "SE", "Gothenburg", "Titanium parts,Composites"),
        ("SteelWorks Berlin", "Steel", "DE", "Berlin", "Structural steel,Fasteners"),
        ("EastAsia Tooling", "Tooling", "CN", "Dongguan", "Die casting,Stamping dies"),
        ("MediDevice Taiwan", "Medical", "TW", "Hsinchu", "Surgical tools,Implants"),
        ("FutureFab Korea", "Semiconductors", "KR", "Seoul", "Wafer processing,MEMS"),
        ("Iberian Composites", "Aerospace", "ES", "Barcelona", "Carbon fiber,Composites"),
    ])
]


def _stub_search(
    q: str,
    industry: str | None,
    country: str | None,
    certifications: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Return deterministic stub results filtered in-memory."""
    results = _STUB_SUPPLIERS[:]
    if q:
        qlow = q.lower()
        results = [
            s for s in results
            if qlow in s["company_name"].lower()
            or qlow in s["company_description"].lower()
            or qlow in s["main_products"].lower()
            or qlow in s["industry"].lower()
        ]
    if industry:
        results = [s for s in results if s["industry"].lower() == industry.lower()]
    if country:
        results = [s for s in results if s["country"].upper() == country.upper()]
    if certifications:
        cert_set = {c.strip().upper() for c in certifications.split(",")}
        results = [
            s for s in results
            if cert_set & {c.strip().upper() for c in s["certifications"].split(",")}
        ]
    total = len(results)
    start = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),
        "results": results[start : start + page_size],
        "_stub": True,
    }


# ── Service ───────────────────────────────────────────────────────────────────

class ElasticsearchSearchService:
    """Wrapper around Elasticsearch for supplier indexing and search.

    Stub mode is activated when the ES cluster is unreachable or
    ``ELASTICSEARCH_URL`` points to a non-running server.
    """

    def __init__(self, es_url: str | None = None) -> None:
        self._url: str = es_url or settings.ELASTICSEARCH_URL
        self._index: str = settings.ES_SUPPLIERS_INDEX
        self._client: Any = None
        self.stub_mode: bool = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            from elasticsearch import Elasticsearch

            self._client = Elasticsearch(
                self._url,
                max_retries=1,
                retry_on_timeout=False,
                request_timeout=5,
            )
            # Test connectivity
            info = self._client.info()
            logger.info("Elasticsearch connected: %s", info.get("version", {}).get("number"))
        except Exception as exc:
            logger.warning(
                "Elasticsearch unavailable (%s) — running in stub mode", exc
            )
            self._client = None
            self.stub_mode = True

    # ── Index management ──────────────────────────────────────────────────────

    def ensure_index(self) -> None:
        """Create the suppliers index with mapping if it doesn't exist."""
        if self.stub_mode:
            return
        try:
            if not self._client.indices.exists(index=self._index):
                self._client.indices.create(index=self._index, body=SUPPLIER_INDEX_MAPPING)
                logger.info("Created ES index: %s", self._index)
        except Exception as exc:
            logger.error("ensure_index failed: %s", exc)

    def index_supplier(self, supplier: Any) -> None:
        """Index (upsert) a single supplier document.

        Args:
            supplier: SQLAlchemy Supplier instance or dict-like object
        """
        if self.stub_mode:
            return

        def _val(attr: str, default: Any = None) -> Any:
            return getattr(supplier, attr, default) or default

        doc: dict[str, Any] = {
            "id": _val("id"),
            "company_name": _val("company_name", ""),
            "company_slug": _val("company_slug", ""),
            "company_description": _val("company_description", ""),
            "main_products": _val("main_products", ""),
            "certifications": _val("certifications", ""),
            "industry": _val("industry", ""),
            "country": _val("country", ""),
            "city": _val("city", ""),
            "is_verified": bool(_val("is_verified", False)),
            "is_active": bool(_val("is_active", True)),
            "manufacturing_capacity": _val("manufacturing_capacity", ""),
            "lead_time_days": _val("lead_time_days"),
            "number_of_employees": _val("number_of_employees"),
            "established_year": _val("established_year"),
            "view_count": _val("view_count", 0),
            "suggest": {
                "input": [
                    _val("company_name", ""),
                    _val("industry", ""),
                    _val("city", ""),
                ],
            },
        }
        try:
            self._client.index(index=self._index, id=doc["id"], document=doc)
        except Exception as exc:
            logger.error("index_supplier failed for id=%s: %s", doc["id"], exc)

    def delete_supplier(self, supplier_id: int) -> None:
        if self.stub_mode:
            return
        try:
            self._client.delete(index=self._index, id=supplier_id, ignore=[404])
        except Exception as exc:
            logger.error("delete_supplier failed for id=%s: %s", supplier_id, exc)

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        q: str = "",
        industry: str | None = None,
        country: str | None = None,
        certifications: str | None = None,
        is_verified: bool | None = None,
        min_employees: int | None = None,
        max_lead_time_days: int | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "_score",   # _score | view_count | lead_time_days
    ) -> dict[str, Any]:
        """Full-text supplier search with multi-dimensional filtering.

        Returns:
            {total, page, page_size, pages, results: [...], _stub: bool}
        """
        if self.stub_mode:
            return _stub_search(q, industry, country, certifications, page, page_size)

        # Build ES query
        must_clauses: list[dict] = [{"term": {"is_active": True}}]
        if q:
            must_clauses.append({
                "multi_match": {
                    "query": q,
                    "fields": [
                        "company_name^3",
                        "main_products^2",
                        "company_description",
                        "certifications",
                        "industry",
                        "city",
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })

        filter_clauses: list[dict] = []
        if industry:
            filter_clauses.append({"term": {"industry": industry}})
        if country:
            filter_clauses.append({"term": {"country": country.upper()}})
        if is_verified is not None:
            filter_clauses.append({"term": {"is_verified": is_verified}})
        if certifications:
            for cert in certifications.split(","):
                cert = cert.strip()
                if cert:
                    filter_clauses.append({"match_phrase": {"certifications": cert}})
        if min_employees:
            filter_clauses.append({"range": {"number_of_employees": {"gte": min_employees}}})
        if max_lead_time_days:
            filter_clauses.append({"range": {"lead_time_days": {"lte": max_lead_time_days}}})

        es_query: dict[str, Any] = {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        }

        # Sort
        sort_map = {
            "_score": [{"_score": {"order": "desc"}}],
            "view_count": [{"view_count": {"order": "desc"}}],
            "lead_time_days": [{"lead_time_days": {"order": "asc"}}],
            "newest": [{"established_year": {"order": "desc"}}],
        }
        sort = sort_map.get(sort_by, sort_map["_score"])

        try:
            t0 = time.perf_counter()
            resp = self._client.search(
                index=self._index,
                query=es_query,
                sort=sort,
                from_=(page - 1) * page_size,
                size=page_size,
                _source=True,
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.debug("ES search took %sms", elapsed_ms)

            hits = resp["hits"]
            total = hits["total"]["value"] if isinstance(hits["total"], dict) else hits["total"]
            results = [h["_source"] for h in hits["hits"]]

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": max(1, -(-total // page_size)),
                "results": results,
                "took_ms": elapsed_ms,
                "_stub": False,
            }
        except Exception as exc:
            logger.error("ES search error: %s — falling back to stub", exc)
            return _stub_search(q, industry, country, certifications, page, page_size)

    # ── Autocomplete ──────────────────────────────────────────────────────────

    def suggest(self, prefix: str, size: int = 5) -> list[str]:
        """Return company name suggestions for the given prefix."""
        if not prefix:
            return []
        if self.stub_mode:
            return [
                s["company_name"]
                for s in _STUB_SUPPLIERS
                if s["company_name"].lower().startswith(prefix.lower())
            ][:size]

        try:
            resp = self._client.search(
                index=self._index,
                suggest={
                    "company_suggest": {
                        "prefix": prefix,
                        "completion": {"field": "suggest", "size": size},
                    }
                },
                _source=False,
            )
            options = resp.get("suggest", {}).get("company_suggest", [{}])[0].get("options", [])
            return [o["text"] for o in options]
        except Exception as exc:
            logger.error("ES suggest error: %s", exc)
            return []

    # ── Bulk reindex ──────────────────────────────────────────────────────────

    def reindex_all(self, suppliers: list[Any]) -> int:
        """Bulk-index a list of supplier objects. Returns count indexed."""
        if self.stub_mode:
            return len(suppliers)
        indexed = 0
        for supplier in suppliers:
            try:
                self.index_supplier(supplier)
                indexed += 1
            except Exception as exc:
                logger.warning("reindex skip supplier %s: %s", getattr(supplier, "id"), exc)
        logger.info("reindex_all: indexed %d suppliers", indexed)
        return indexed


# ── Module-level singleton ────────────────────────────────────────────────────

_search_svc: ElasticsearchSearchService | None = None


def get_search_service() -> ElasticsearchSearchService:
    global _search_svc
    if _search_svc is None:
        _search_svc = ElasticsearchSearchService()
    return _search_svc
