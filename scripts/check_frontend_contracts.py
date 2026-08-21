#!/usr/bin/env python3
"""Validate Reflex/FastAPI boundaries and the absence of the legacy Next.js app."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "frontend_contract_validation.json"
REFLEX_ROUTES = ["/check", "/trace", "/trace/[report_id]", "/trace/[report_id]/proof-packet", "/console", "/console/trace", "/console/evidence", "/console/market-intelligence", "/console/time-machine", "/console/sovereign-grid", "/console/policy", "/console/audit", "/console/command-center"]
REQUIRED_COPY = ["Advisory-only", "Not legal verification", "Not Bitcoin consensus proof", "No custody", "Public Bitcoin addresses only", "Never enter seed phrases, private keys, wallet files or signing material"]
FORBIDDEN_LINKS = ["/products", "/self-host"]
LEGACY_NEXTJS_MARKERS = [
    "frontend/package.json",
    "frontend/next.config.js",
    "frontend/next.config.mjs",
    "frontend/next.config.ts",
]


def read(path: str) -> str:
    file_path = ROOT / path
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


def main() -> int:
    app_py = read("frontend/bastion_ui/app.py")
    rxconfig = read("frontend/rxconfig.py")
    env_example = read("frontend/.env.example")
    safety = read("frontend/bastion_ui/security/safety_copy.py") + read("frontend/bastion_ui/components/ui/safety_banner.py")
    command_palette = read("frontend/bastion_ui/components/layout/command_palette.py")
    command_registry = read("frontend/bastion_ui/command_registry.py")
    route_topology = read("frontend/bastion_ui/topology.py")
    market_router_present = (ROOT / "app/web/routes.py").exists() or (ROOT / "app/web/market_routes.py").exists()
    result = {
        "status": "implemented",
        "reflex_core_files": {p: (ROOT / p).exists() for p in ["frontend/rxconfig.py", "frontend/pyproject.toml", "frontend/README.md", "frontend/.env.example", "frontend/Dockerfile", "frontend/bastion_ui/app.py"]},
        "reflex_ports": {"frontend_3001": "frontend_port=3001" in rxconfig.replace(" ", ""), "backend_8001": "backend_port=8001" in rxconfig.replace(" ", "")},
        "env": {"BB_API_BASE_URL": "BB_API_BASE_URL" in env_example, "BB_REQUEST_TIMEOUT_SECONDS": "BB_REQUEST_TIMEOUT_SECONDS" in env_example},
        "reflex_routes": {route: f'route="{route}"' in app_py for route in REFLEX_ROUTES},
        "safety_copy": {copy: copy in safety for copy in REQUIRED_COPY},
        "navigation": {
            # Palette commands are intentionally derived from canonical route metadata;
            # route paths must not be duplicated in the presentation component.
            "registry_derived": "from bastion_ui.topology import ROUTES" in command_registry,
            "platform": '("/platform", "Platform", "platform_page")' in route_topology,
            "operations": '("/operations", "Operations", "operations_page")' in route_topology,
            "no_products": "/products" not in command_palette,
            "no_self_host": "/self-host" not in command_palette,
        },
        "legacy_nextjs_absent": {
            path: not (ROOT / path).exists() for path in LEGACY_NEXTJS_MARKERS
        },
        "market_fastapi_jinja_present": market_router_present,
    }
    blockers = []
    for section in (
        "reflex_core_files",
        "reflex_ports",
        "env",
        "reflex_routes",
        "safety_copy",
        "navigation",
        "legacy_nextjs_absent",
    ):
        blockers += [f"{section}:{k}" for k, v in result[section].items() if not v]
    result["blockers"] = blockers
    if blockers:
        result["status"] = "blocked"
    ARTIFACT.parent.mkdir(exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
