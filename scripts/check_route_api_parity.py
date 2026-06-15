#!/usr/bin/env python3
"""Static route/API parity checker for Bitcoin Bastion integration evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "route_api_parity.json"

REQUIRED_ROUTERS = [
    "health", "auth", "news", "market_intelligence", "market_data", "market", "intelligence_timeline",
    "intelligence", "signals", "operator_signals", "onchain", "entities", "wallet", "fees", "treasury",
    "admin", "users", "policy", "privacy", "education", "evidence", "observability", "citadel",
    "trace", "public", "webhooks", "ws",
]
REQUIRED_TRACE = [
    "/lite/{address}", "/address/{address}", "/report/{report_id}", "/report/{report_id}/evidence",
    "/report/{report_id}/privacy-shield", "/report/{report_id}/origin-passport", "/report/{report_id}/source-summary",
    "/report/{report_id}/provider-disagreement", "/report/{report_id}/utxo-hygiene", "/report/{report_id}/dust-radar",
    "/report/{report_id}/counterparty-lens", "/report/{report_id}/policy-facts", "/status", "/events",
]
OPTIONAL_TRACE = ["/report/{report_id}/proof-packet"]
REQUIRED_PUBLIC = ["/trace/{report_id}/summary"]
REQUIRED_REFLEX = [
    "/", "/platform", "/developers", "/operations", "/manifesto", "/evidence", "/status", "/roadmap",
    "/security", "/docs", "/check", "/trace", "/trace/[report_id]", "/trace/[report_id]/proof-packet",
    "/console", "/console/trace", "/console/evidence", "/console/market-intelligence", "/console/time-machine",
    "/console/sovereign-grid", "/console/policy", "/console/audit", "/console/command-center",
]


def read(path: str) -> str:
    file_path = ROOT / path
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


def has_router(main: str, name: str) -> bool:
    return f"{name}_router" in main or f"{name}.router" in main


def main() -> int:
    main_py = read("app/main.py")
    trace_py = read("app/api/v1/trace.py")
    public_py = read("app/api/v1/public.py")
    reflex_app = read("reflex_frontend/bastion_ui/app.py")
    result = {
        "status": "implemented",
        "backend_routers": {name: "implemented" if has_router(main_py, name) else "blocked" for name in REQUIRED_ROUTERS},
        "trace_routes": {route: "implemented" if route in trace_py else "blocked" for route in REQUIRED_TRACE},
        "optional_trace_routes": {route: "implemented" if route in trace_py else "planned" for route in OPTIONAL_TRACE},
        "public_routes": {route: "implemented" if route in public_py else "blocked" for route in REQUIRED_PUBLIC},
        "reflex_routes": {route: "implemented" if f'route="{route}"' in reflex_app else "blocked" for route in REQUIRED_REFLEX},
    }
    blockers = []
    for section in ("backend_routers", "trace_routes", "public_routes", "reflex_routes"):
        blockers.extend(f"{section}:{key}" for key, value in result[section].items() if value == "blocked")
    result["blockers"] = blockers
    if blockers:
        result["status"] = "blocked"
    ARTIFACT.parent.mkdir(exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
