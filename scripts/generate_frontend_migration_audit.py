#!/usr/bin/env python3
"""Generate Prompt-0 read-only API/frontend migration evidence.

This intentionally does not assert implementation parity. It derives the runtime
OpenAPI and Starlette WebSocket registrations, then emits deterministic planning
records. Human-authored policy lives in the companion Markdown audit files.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.main import app  # noqa: E402
from app.api.v1.ws import router as ws_router  # noqa: E402
from app.core.config import get_settings  # noqa: E402

OUT = ROOT / "docs/frontend/migration"
METHODS = ("delete", "get", "head", "options", "patch", "post", "put", "trace")
CALLBACK_MARKERS = ("callback", "webhook", "well-known", "/verify", "settlement")
PROTOCOL_MARKERS = ("/lnurl", "/wallet-auth", "/auth/challenge", "/auth/session", "/.well-known")
SEPARATE_MARKERS = ("payregister",)
ADMIN_MARKERS = (
    "/admin",
    "/operations",
    "/observability",
    "/storage",
    "/audit",
    "/operator",
    "/treasury",
    "/plugins",
    "/webhooks",
)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def ref(v: Any) -> str:
    if not isinstance(v, dict):
        return ""
    if "$ref" in v:
        return v["$ref"].rsplit("/", 1)[-1]
    if "schema" in v:
        return ref(v["schema"])
    if "content" in v:
        c = v["content"]
        return ref(c.get("application/json", next(iter(c.values()), {})))
    if v.get("type") == "array":
        return f"list[{ref(v.get('items',{})) or 'unknown'}]"
    return v.get("title") or v.get("type", "")


def prompt_for(path: str) -> int:
    p = path.lower()
    if "payregister" in p:
        return 22
    if "lnurl" in p or "business-lightning" in p:
        return 22
    if "/access" in p or "wallet-auth" in p:
        if any(x in p for x in ("recovery", "revoke", "lockdown", "session")):
            return 18
        if any(x in p for x in ("profile", "entitlement", "delegat", "limit")):
            return 17
        return 16
    if "trace" in p:
        return 13 if any(x in p for x in ("event", "graph", "privacy", "topology")) else 12
    if "evidence" in p:
        return 15 if any(x in p for x in ("replay", "verify", "lineage", "export")) else 14
    if any(x in p for x in ("market", "signal", "news", "intelligence", "timeline")):
        return 10 if any(x in p for x in ("timeline", "evidence", "narrative", "attribution")) else 9
    if any(
        x in p
        for x in (
            "health",
            "status",
            "operations",
            "observability",
            "storage",
            "incident",
            "slo",
            "job",
        )
    ):
        return 9 if any(x in p for x in ("incident", "slo", "job")) else 8
    mapping = [
        ("policy", 19), ("audit", 19), ("treasury", 19),
        ("entit", 20), ("watch", 20), ("fees", 20), ("onchain", 20),
        ("wallet", 20), ("citadel", 20), ("privacy", 23),
        ("plugin", 21), ("webhook", 21), ("explorer", 21),
    ]
    for key, n in mapping:
        if key in p:
            return n
    return 8


def disposition(method: str, path: str) -> tuple[str, str, str]:
    p = path.lower()
    if any(x in p for x in SEPARATE_MARKERS):
        return (
            "SEPARATE_PRODUCT",
            "PayRegister is feature-flagged and outside core navigation.",
            "PayRegister",
        )
    if any(x in p for x in CALLBACK_MARKERS):
        return (
            "CALLBACK_ONLY",
            "Receiver/callback is invoked by an external service or protocol, not a generic user action.",
            "backend-only",
        )
    if any(x in p for x in PROTOCOL_MARKERS):
        return (
            "PROTOCOL_ONLY",
            "Proof/handshake lifecycle remains protocol-owned; only its operator workflow may render.",
            "Access" if "lnurl" not in p else "LNURL",
        )
    if path in ("/metrics", "/health"):
        return "BACKEND_ONLY", "Machine probe/metrics surface.", "backend-only"
    if method in ("post", "patch", "put", "delete") and any(
        x in p for x in ("admin", "execute", "rotate", "revoke", "lockdown", "recover")
    ):
        return (
            "UI_OPTIONAL",
            "Mutation requires actor, intent, confirmation, idempotency and audit contract before UI exposure.",
            "Operator Console",
        )
    product = (
        "Operator Console"
        if any(x in p for x in ADMIN_MARKERS)
        else ("Access" if "/access" in p else "Core")
    )
    return (
        (
            "UI_REQUIRED"
            if method == "get" or any(x in p for x in ("trace", "evidence", "checkout", "estimate"))
            else "UI_OPTIONAL"
        ),
        "User-visible read model or bounded workflow; implementation still requires all ten parity links.",
        product,
    )


def frontend_literals() -> tuple[list[str], dict[str, list[str]]]:
    found: dict[str, list[str]] = {}
    rx = re.compile(r"""[fru]*["'](/(?:api/)?v1/[^"'?# ]+)""")
    for f in sorted((ROOT / "frontend/bastion_ui").rglob("*.py")):
        if "/tests/" in f.as_posix():
            continue
        for m in rx.finditer(f.read_text(errors="ignore")):
            val = re.sub(r"\{[^}]+\}", r"{param}", m.group(1)).rstrip("/") or "/"
            found.setdefault(val, []).append(str(f.relative_to(ROOT)))
    return sorted(found), found


def main() -> None:
    spec = app.openapi()
    head = git("rev-parse", "HEAD")
    # Bind generated artifacts to the source revision rather than wall-clock time.
    # This preserves an auditable UTC timestamp while making regeneration at the
    # same HEAD byte-for-byte deterministic.
    stamp = git("show", "-s", "--format=%cI", head)
    ops = []
    ids = []
    for path, item in sorted(spec["paths"].items()):
        for method in METHODS:
            if method not in item:
                continue
            op = item[method]
            oid = op.get("operationId", "")
            ids.append(oid)
            disp, reason, product = disposition(method, path)
            req = ""
            body = op.get("requestBody", {})
            req = ref(body)
            responses = op.get("responses", {})
            response = ref(
                responses.get("200") or responses.get("201") or responses.get("202") or {}
            )
            protected = bool(op.get("security"))
            coverage = "NOT_STARTED"
            ops.append(
                {
                    "matrix_id": f"HTTP-{len(ops)+1:04d}",
                    "method": method.upper(),
                    "path": path,
                    "operation_id": oid,
                    "backend_owner": (op.get("tags") or ["unowned"])[0],
                    "request_schema": req or "none",
                    "response_schema": response or "unspecified",
                    "error_envelope": "HTTP validation/error response; typed frontend normalization not verified",
                    "access_class": (
                        "protected"
                        if protected
                        else (
                            "callback/protocol"
                            if disp in ("CALLBACK_ONLY", "PROTOCOL_ONLY")
                            else "public/unverified"
                        )
                    ),
                    "required_plan_scope_poa_pop_signing_human_intent": (
                        "derive from dependency/policy in Prompt 1; MUST NOT weaken Proof-of-Access"
                        if protected
                        else "none observed in OpenAPI; runtime dependency review required"
                    ),
                    "mutation_idempotency_confirmation": (
                        "required and unverified"
                        if method not in ("GET", "HEAD", "OPTIONS")
                        else "read-only"
                    ),
                    "disposition": disp,
                    "reason": reason,
                    "product_boundary": product,
                    "frontend_surface": (
                        "TBD by assigned prompt" if disp.startswith("UI_") else "N/A"
                    ),
                    "client_method": "not runtime-verified",
                    "verified_url": path,
                    "adapter_view_model": "none verified",
                    "trigger_subscription": "none verified",
                    "rendered_component_fields": "none verified",
                    "state_behavior": "loading/empty/partial/stale/degraded/conflicting/401/403/expired/429/offline/error required",
                    "privacy_policy": "safe-field allowlist; no secrets in URL/storage/telemetry/clipboard/share",
                    "contract_test": "not verified",
                    "browser_e2e": "not verified",
                    "implementation_prompt": (
                        prompt_for(path)
                        if disp in ("UI_REQUIRED", "UI_OPTIONAL", "SEPARATE_PRODUCT")
                        else None
                    ),
                    "coverage_state": (
                        coverage
                        if disp.startswith("UI_") or disp == "SEPARATE_PRODUCT"
                        else "NOT_APPLICABLE"
                    ),
                    "rollback_disable": "route/domain feature flag; backend registration unchanged by frontend migration",
                }
            )
    # Starlette registrations are runtime truth; OpenAPI omits WS.
    ws = []
    for route in sorted(ws_router.routes, key=lambda r: getattr(r, "path", "")):
        if route.__class__.__name__ == "APIWebSocketRoute":
            path = f"{get_settings().api_prefix}{route.path}"
            disp = "UI_REQUIRED" if path != "/api/v1/ws/events" else "UI_OPTIONAL"
            ws.append(
                {
                    "matrix_id": f"WS-{len(ws)+1:03d}",
                    "channel": path,
                    "operation_id": route.name,
                    "backend_owner": "websockets/events",
                    "message_schema": "system/error/event JSON from websocket_serialization and broker",
                    "auth_contract": "no OpenAPI security metadata; runtime origin/Proof-of-Access review required",
                    "reconnect_fallback": "bounded exponential backoff, heartbeat 10–120s, visible stale state, HTTP fallback required; replay currently unavailable",
                    "disposition": disp,
                    "reason": "Live user-visible domain updates; generic event stream optional when specialized channels exist.",
                    "product_boundary": (
                        "Operator Console"
                        if any(x in path for x in ("treasury", "provider"))
                        else "Core"
                    ),
                    "frontend_surface": "assigned domain screen",
                    "coverage_state": "NOT_STARTED",
                    "implementation_prompt": 4,
                    "privacy_policy": "limit_payload=true; no session/secret material persisted",
                    "contract_test": "backend tests only; frontend subscriber not found",
                    "browser_e2e": "not verified",
                    "rollback_disable": "disable subscription and retain visible polling/unavailable state",
                }
            )
    norm = {
        "metadata": {
            "head": head,
            "branch": git("branch", "--show-current"),
            "generated_at_utc": stamp,
            "profile": "current environment / app.core.config defaults",
            "command": "python scripts/generate_frontend_migration_audit.py",
            "python": subprocess.check_output(["python", "--version"], text=True).strip(),
        },
        "counts": {
            "paths": len(spec["paths"]),
            "operations": len(ops),
            "api_v1_paths": sum(p.startswith("/api/v1") for p in spec["paths"]),
            "api_v1_operations": sum(o["path"].startswith("/api/v1") for o in ops),
            "schemas": len(spec.get("components", {}).get("schemas", {})),
            "security_schemes": sorted(spec.get("components", {}).get("securitySchemes", {})),
            "websockets": len(ws),
            "duplicate_operation_ids": sorted(k for k, v in Counter(ids).items() if v > 1),
        },
        "openapi": spec,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "00_OPENAPI_SNAPSHOT.json").write_text(json.dumps(norm, indent=2, sort_keys=True) + "\n")
    payload = {
        "metadata": norm["metadata"],
        "counts": norm["counts"],
        "http_operations": ops,
        "websocket_channels": ws,
    }
    (OUT / "00_openapi_frontend_rendering_matrix.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    literals, sources = frontend_literals()
    paths = set(spec["paths"])
    stale = []
    matched = []
    for lit in literals:
        canonical = re.escape(lit).replace(r"\{param\}", r"\{[^/]+\}")
        hit = any(
            re.fullmatch(canonical, p) or re.fullmatch(canonical, p.removeprefix("/api"))
            for p in paths
        )
        (matched if hit else stale).append(lit)
    summary = {
        "literal_count": len(literals),
        "matched_count": len(matched),
        "stale_or_absent_count": len(stale),
        "matched": matched,
        "stale_or_absent": stale,
        "sources": sources,
    }
    (OUT / "00_FRONTEND_URL_AUDIT.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    rows = [
        "# OpenAPI → Frontend Rendering Matrix",
        "",
        "Generated by `python scripts/generate_frontend_migration_audit.py`. Runtime evidence, not an implementation claim.",
        "",
        f"**HEAD:** `{head}` · **HTTP:** {len(ops)} · **WS:** {len(ws)} · **frontend literals:** {len(literals)} ({len(stale)} stale/absent)",
        "",
        "| ID | Method/path | Disposition | Product | Coverage | Prompt |",
        "|---|---|---|---|---|---:|",
    ]
    rows += [
        f"| {o['matrix_id']} | `{o['method']} {o['path']}` | {o['disposition']} | {o['product_boundary']} | {o['coverage_state']} | {o['implementation_prompt'] or 'N/A'} |"
        for o in ops
    ]
    rows += [
        "",
        "## WebSockets",
        "",
        "| ID | Channel | Disposition | Coverage | Prompt |",
        "|---|---|---|---|---:|",
    ] + [
        f"| {w['matrix_id']} | `{w['channel']}` | {w['disposition']} | {w['coverage_state']} | {w['implementation_prompt']} |"
        for w in ws
    ]
    (OUT / "00_OPENAPI_FRONTEND_RENDERING_MATRIX.md").write_text("\n".join(rows) + "\n")
    disp = Counter(o["disposition"] for o in ops)
    disp.update(w["disposition"] for w in ws)
    reg = (
        [
            "# Endpoint Disposition Register",
            "",
            f"Generated at `{stamp}` from `{head}`. Each runtime operation/channel occurs once in the machine matrix.",
            "",
            "## Totals",
            "",
        ]
        + [f"- **{k}:** {v}" for k, v in sorted(disp.items())]
        + [
            "",
            "## Rules",
            "",
            "- Callback and protocol receivers remain backend-owned; operator workflows may use separate read models.",
            "- PayRegister remains a separate feature-flagged product and is not core navigation.",
            "- UI mutations remain ineligible until authorization, Human Intent, idempotency, audit, confirmation, error and rollback are proven.",
            "- `NOT_STARTED` is deliberately conservative: source presence is not request-to-render evidence.",
            "",
            "See `00_openapi_frontend_rendering_matrix.json` for complete records and reasons.",
        ]
    )
    (OUT / "00_ENDPOINT_DISPOSITION_REGISTER.md").write_text("\n".join(reg) + "\n")
    print(
        json.dumps(
            {
                "counts": norm["counts"],
                "dispositions": dict(sorted(disp.items())),
                "frontend_urls": summary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
