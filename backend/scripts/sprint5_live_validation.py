#!/usr/bin/env python3
"""Sprint 5 live validation script.

This script verifies RB2B / Leadfeeder webhook ingestion with real secrets,
then fetches benchmark and ops metrics from API for acceptance reporting.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime

import httpx


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _sign(secret: str, payload_bytes: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _build_rb2b_payload(supplier_id: int) -> dict:
    return {
        "supplier_id": supplier_id,
        "session_id": f"rb2b-live-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "event_type": "rfq_page_enter",
        "url": "/suppliers/live/rfq",
        "email": "live-buyer@example.com",
        "company": "Live Validation Inc",
        "country": "us",
    }


def _build_leadfeeder_payload(supplier_id: int) -> dict:
    return {
        "supplier_id": supplier_id,
        "visit_id": f"lead-live-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "event_type": "company_identified",
        "company": {
            "id": "live-company-1",
            "name": "Live GmbH",
            "country": "de",
            "domain": "live.example.de",
            "industry": "Manufacturing",
        },
        "contact": {
            "email": "procurement@live.example.de",
        },
    }


def _get_headers(token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint 5 live validation")
    parser.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--supplier-id", type=int, required=True)
    parser.add_argument("--token", default=os.getenv("SUPPLIER_JWT"))
    parser.add_argument("--benchmark-days", type=int, default=14)
    parser.add_argument("--ops-hours", type=int, default=24)
    parser.add_argument("--out", default="sprint5_live_validation_report.json")
    args = parser.parse_args()

    rb2b_secret = _required_env("RB2B_WEBHOOK_SECRET")
    lead_secret = _required_env("LEADFEEDER_WEBHOOK_SECRET")

    rb2b_payload = _build_rb2b_payload(args.supplier_id)
    lead_payload = _build_leadfeeder_payload(args.supplier_id)

    rb2b_raw = json.dumps(rb2b_payload).encode("utf-8")
    lead_raw = json.dumps(lead_payload).encode("utf-8")

    report: dict = {
        "generated_at": datetime.utcnow().isoformat(),
        "base_url": args.base_url,
        "supplier_id": args.supplier_id,
        "webhook_results": {},
        "benchmark": None,
        "ops_metrics": None,
    }

    with httpx.Client(timeout=20.0) as client:
        rb2b_resp = client.post(
            f"{args.base_url}/api/v1/visitor-intent/webhooks/rb2b",
            content=rb2b_raw,
            headers={
                "Content-Type": "application/json",
                "X-RB2B-Signature": _sign(rb2b_secret, rb2b_raw),
            },
        )
        report["webhook_results"]["rb2b"] = {
            "status_code": rb2b_resp.status_code,
            "response": rb2b_resp.json() if rb2b_resp.headers.get("content-type", "").startswith("application/json") else rb2b_resp.text,
        }

        lead_resp = client.post(
            f"{args.base_url}/api/v1/visitor-intent/webhooks/leadfeeder",
            content=lead_raw,
            headers={
                "Content-Type": "application/json",
                "X-Leadfeeder-Signature": _sign(lead_secret, lead_raw).replace("sha256=", ""),
            },
        )
        report["webhook_results"]["leadfeeder"] = {
            "status_code": lead_resp.status_code,
            "response": lead_resp.json() if lead_resp.headers.get("content-type", "").startswith("application/json") else lead_resp.text,
        }

        if args.token:
            auth_headers = _get_headers(args.token)
            benchmark_resp = client.get(
                f"{args.base_url}/api/v1/visitor-intent/benchmark",
                params={"days": args.benchmark_days},
                headers=auth_headers,
            )
            ops_resp = client.get(
                f"{args.base_url}/api/v1/visitor-intent/ops-metrics",
                params={"hours": args.ops_hours},
                headers=auth_headers,
            )
            report["benchmark"] = {
                "status_code": benchmark_resp.status_code,
                "response": benchmark_resp.json() if benchmark_resp.headers.get("content-type", "").startswith("application/json") else benchmark_resp.text,
            }
            report["ops_metrics"] = {
                "status_code": ops_resp.status_code,
                "response": ops_resp.json() if ops_resp.headers.get("content-type", "").startswith("application/json") else ops_resp.text,
            }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Live validation report generated: {args.out}")

    rb2b_ok = report["webhook_results"]["rb2b"]["status_code"] == 202
    lead_ok = report["webhook_results"]["leadfeeder"]["status_code"] == 202
    if not (rb2b_ok and lead_ok):
        print("Webhook validation failed. Check report for details.")
        return 1

    print("Webhook validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Validation failed: {exc}")
        raise SystemExit(1)
