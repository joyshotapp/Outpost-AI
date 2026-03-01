#!/usr/bin/env python3
"""Sprint 5 preflight checker.

Checks local test readiness and required environment variables for live validation.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime


REQUIRED_ENV = [
    "API_BASE_URL",
    "RB2B_WEBHOOK_SECRET",
    "LEADFEEDER_WEBHOOK_SECRET",
    "CLAY_API_KEY",
    "SUPPLIER_JWT",
]

TEST_CMD = [
    "pytest",
    "tests/test_visitor_intent_api.py",
    "tests/test_sprint5_e2e_flow.py",
    "-q",
]


def run_tests() -> dict:
    proc = subprocess.run(TEST_CMD, capture_output=True, text=True)
    return {
        "command": " ".join(TEST_CMD),
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-10:]),
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-10:]),
        "passed": proc.returncode == 0,
    }


def check_env() -> dict:
    status = {}
    for key in REQUIRED_ENV:
        status[key] = bool(os.getenv(key))
    return status


def main() -> int:
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "tests": run_tests(),
        "env": check_env(),
    }

    report["env_ready_for_live_validation"] = all(report["env"].values())
    report["preflight_pass"] = report["tests"]["passed"]

    out = "sprint5_preflight_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nPreflight report written to: {out}")

    if report["preflight_pass"]:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
