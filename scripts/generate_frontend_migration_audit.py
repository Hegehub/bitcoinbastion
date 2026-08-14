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
from app.services.events.websocket_registry import WEBSOCKET_CONTRACTS  # noqa: E402
from scripts.stage1_fingerprints import manifest as stage1_manifest  # noqa: E402

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
DEFERRED_HTTP: dict[tuple[str, str], dict[str, str]] = {
    ("get", "/market-time-machine"): {
        "blocker_id": "P1R2-B01",
        "reason_code": "canonical_compatibility_ownership_unresolved",
        "future_owner": "Prompt 25/25",
        "reentry_condition": "API owner records canonical path, compatibility lifetime, and alias removal policy",
    },
    ("post", "/api/v1/access/api-keys/{key_id}/freeze"): {
        "blocker_id": "P1R2-B02",
        "reason_code": "access_security_contract_unresolved",
        "future_owner": "Prompt 17/25",
        "reentry_condition": "Access owner supplies tested scope, PoP/signing, intent, replay, audit, and reconciliation semantics",
    },
    ("post", "/api/v1/auth/login"): {
        "blocker_id": "P1R2-B03",
        "reason_code": "disabled_legacy_auth",
        "future_owner": "Prompt 25/25",
        "reentry_condition": "none; remove after compatibility window unless product owner establishes a non-password purpose",
    },
    ("post", "/api/v1/auth/register"): {
        "blocker_id": "P1R2-B04",
        "reason_code": "disabled_legacy_auth",
        "future_owner": "Prompt 25/25",
        "reentry_condition": "none; remove after compatibility window unless product owner establishes a non-password purpose",
    },
}


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
        return f"list[{ref(v.get('items', {})) or 'unknown'}]"
    return v.get("title") or v.get("type", "")


def prompt_for(path: str) -> int:
    p = path.lower()
    if "/market/similarity" in p:
        return 11
    if "/market/history" in p:
        return 10
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
        return (
            10 if any(x in p for x in ("timeline", "evidence", "narrative", "attribution")) else 9
        )
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
        ("policy", 19),
        ("audit", 19),
        ("treasury", 19),
        ("entit", 20),
        ("watch", 20),
        ("fees", 20),
        ("onchain", 20),
        ("wallet", 20),
        ("citadel", 20),
        ("privacy", 23),
        ("plugin", 21),
        ("webhook", 21),
        ("explorer", 21),
    ]
    for key, n in mapping:
        if key in p:
            return n
    return 8


def disposition(method: str, path: str) -> tuple[str, str, str]:
    p = path.lower()
    deferred = DEFERRED_HTTP.get((method, path))
    if deferred:
        return (
            "DEFERRED_WITH_REASON",
            deferred["reason_code"],
            ("Access" if "/access/" in p else "Core"),
        )
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


def has_untyped_schema(
    value: object, schemas: dict[str, Any], visited: set[str] | None = None
) -> bool:
    """Detect backend `Any` schema fragments without inventing a frontend type."""
    seen = visited or set()
    if isinstance(value, dict):
        meaningful = {
            "$ref",
            "type",
            "anyOf",
            "oneOf",
            "allOf",
            "enum",
            "const",
            "properties",
            "additionalProperties",
        }
        if (
            value
            and not meaningful.intersection(value)
            and set(value)
            <= {
                "title",
                "description",
                "default",
                "examples",
            }
        ):
            return True
        if not value:
            return True
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/components/schemas/"):
            name = reference.rsplit("/", 1)[-1]
            if name not in seen:
                seen.add(name)
                if has_untyped_schema(schemas[name], schemas, seen):
                    return True
        return any(
            has_untyped_schema(child, schemas, seen)
            for key, child in value.items()
            if key not in {"$ref", "default", "examples", "title", "description"}
        )
    if isinstance(value, list):
        return any(has_untyped_schema(child, schemas, seen) for child in value)
    return False


def main() -> None:
    spec = app.openapi()
    schemas = spec.get("components", {}).get("schemas", {})
    head = git("rev-parse", "HEAD")
    fingerprints = stage1_manifest()
    # Bind generated artifacts to the source revision rather than wall-clock time.
    # This preserves an auditable UTC timestamp while making regeneration at the
    # same HEAD byte-for-byte deterministic.
    stamp = git("show", "-s", "--format=%cI", head)
    ops = []
    ids = []
    generated_http_path = ROOT / "frontend/bastion_ui/transport/generated_http.py"
    generated_http = generated_http_path.read_text() if generated_http_path.exists() else ""
    authoritative_protected_operations = {
        "operations_list_incidents",
        "operations_get_incident",
        "operations_list_slo",
        "market_current_overview",
        "jobs_api_v1_operations_jobs_get",
        "market_history_attributions",
        "market_history_narratives",
        "market_history_replay_event",
        "market_history_sources",
        "market_history_timeline",
        "market_similarity_report",
    }
    # Prompt-12 reviewed mutation authority: public Feature-21 submit is a
    # synchronous, server-validated mutation with a required durable
    # Idempotency-Key. It intentionally requires neither PoP nor Human Intent.
    authoritative_mutation_operations = {
        "submit_trace_api_v1_trace_submit_post",
    }
    for path, item in sorted(spec["paths"].items()):
        for method in METHODS:
            if method not in item:
                continue
            op = item[method]
            oid = op.get("operationId", "")
            generated_owner = f"async def {oid}(" in generated_http
            ids.append(oid)
            disp, reason, product = disposition(method, path)
            req = ""
            body = op.get("requestBody", {})
            req = ref(body)
            responses = op.get("responses", {})
            success_status = next((code for code in sorted(responses) if code.startswith("2")), "")
            response = (
                "NoContent" if success_status == "204" else ref(responses.get(success_status, {}))
            )
            success_content = responses.get(success_status, {}).get("content", {})
            active_ui = disp in ("UI_REQUIRED", "UI_OPTIONAL")
            legacy_html = "text/html" in success_content and disp in {"UI_REQUIRED", "UI_OPTIONAL"}
            schema_authority_missing = active_ui and (
                bool(body)
                and has_untyped_schema(body, schemas)
                or has_untyped_schema(responses.get(success_status, {}), schemas)
            )
            protected = bool(op.get("security"))
            coverage = "NOT_STARTED"
            if generated_owner:
                coverage = "CLIENT_ONLY"
            deferred = DEFERRED_HTTP.get((method, path))
            unresolved_mutation = (
                active_ui
                and method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
                and oid not in authoritative_mutation_operations
            )
            unresolved_protected = (
                active_ui and protected and oid not in authoritative_protected_operations
            )
            contract_authority_deferred = unresolved_mutation or unresolved_protected
            if contract_authority_deferred:
                disp = "DEFERRED_WITH_REASON"
                missing = []
                if unresolved_protected:
                    missing.append("protected_security_contract_unresolved")
                if unresolved_mutation:
                    missing.append("mutation_safety_contract_unresolved")
                reason = "+".join(missing)
            elif legacy_html:
                disp = "DEFERRED_WITH_REASON"
                reason = "legacy_server_html_not_generic_reflex_transport"
            elif schema_authority_missing:
                disp = "DEFERRED_WITH_REASON"
                reason = "backend_schema_contains_untyped_any"
            # OpenAPI currently exposes no operation-specific safe error registry and the
            # migration audit has not completed dependency-level security semantics. A
            # descriptor name is not a generated typed client, so fail closed rather than
            # promoting all candidates to authoritative ownership.
            transport_contract_blocked = (
                active_ui
                and deferred is None
                and not contract_authority_deferred
                and not legacy_html
                and not schema_authority_missing
                and not generated_owner
                and oid not in authoritative_protected_operations
                and oid not in authoritative_mutation_operations
            )
            authority = (
                "DEFERRED_AUTHORITY"
                if deferred
                or transport_contract_blocked
                or contract_authority_deferred
                or legacy_html
                or schema_authority_missing
                else "AUTHORITATIVE_NOW"
            )
            blocker_id = (
                deferred["blocker_id"]
                if deferred
                else (
                    "P1B0-B01+B02"
                    if unresolved_protected and unresolved_mutation
                    else "P1B0-B01"
                    if unresolved_protected
                    else "P1B0-B02"
                    if unresolved_mutation
                    else "P1B0-B03-HTML"
                    if legacy_html
                    else "P1B0-B03-SCHEMA"
                    if schema_authority_missing
                    else "P1B-B01"
                    if transport_contract_blocked
                    else None
                )
            )
            future_owner = (
                deferred["future_owner"]
                if deferred
                else (
                    f"Prompt {prompt_for(path)}/25"
                    if contract_authority_deferred
                    else "Prompt 25/25"
                    if legacy_html
                    else "Prompt 1B/25"
                    if schema_authority_missing
                    else "Prompt 1B/25"
                    if transport_contract_blocked
                    else None
                )
            )
            reentry = (
                deferred["reentry_condition"]
                if deferred
                else (
                    "backend owner supplies tested security and mutation semantics before UI generation"
                    if contract_authority_deferred
                    else "migrate or remove legacy server HTML; do not expose as generic Reflex transport"
                    if legacy_html
                    else "backend owner replaces untyped Any schema fields with authoritative transport types"
                    if schema_authority_missing
                    else "generate strict request/success/error DTOs and encode reviewed dependency-level security metadata"
                    if transport_contract_blocked
                    else None
                )
            )
            ops.append(
                {
                    "matrix_id": f"HTTP-{len(ops) + 1:04d}",
                    "method": method.upper(),
                    "path": path,
                    "operation_id": oid,
                    "backend_owner": (op.get("tags") or ["unowned"])[0],
                    "request_schema": req or "none",
                    "response_schema": response or "unspecified",
                    "success_status": success_status or "unspecified",
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
                    "authority_status": authority,
                    "authority_blocker_id": blocker_id,
                    "authority_future_owner": future_owner,
                    "authority_reentry_condition": reentry,
                    "deferred_contract_kind": (
                        "protected_mutation"
                        if unresolved_protected and unresolved_mutation
                        else "protected"
                        if unresolved_protected
                        else "mutation"
                        if unresolved_mutation
                        else None
                    ),
                    "typed_client_owner": (
                        f"bastion_ui.transport.generated_http:{oid}" if generated_owner else "none"
                    ),
                    "product_boundary": product,
                    "frontend_surface": (
                        "TBD by assigned prompt" if disp.startswith("UI_") else "N/A"
                    ),
                    "client_method": oid if generated_owner else "not runtime-verified",
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
                        else (
                            int(deferred["future_owner"].split()[1].split("/")[0])
                            if deferred
                            else None
                        )
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
    ws_contracts = {contract.route: contract for contract in WEBSOCKET_CONTRACTS}
    for route in sorted(ws_router.routes, key=lambda r: getattr(r, "path", "")):
        if route.__class__.__name__ == "APIWebSocketRoute":
            path = f"{get_settings().api_prefix}{route.path}"
            disp = "UI_REQUIRED" if path != "/api/v1/ws/events" else "UI_OPTIONAL"
            contract = ws_contracts[path]
            ws.append(
                {
                    "matrix_id": f"WS-{len(ws) + 1:03d}",
                    "channel": path,
                    "operation_id": route.name,
                    "backend_owner": "websockets/events",
                    "message_schema": "WireFrame discriminated union from websocket_contracts",
                    "authority_status": "AUTHORITATIVE_NOW",
                    "authority_blocker_id": contract.blocker_id,
                    "authority_future_owner": "Prompt 4/25 (resolved)",
                    "authority_reentry_condition": "none; version changes follow documented compatibility policy",
                    "wire_version_authority": str(contract.wire_version),
                    "auth_contract": contract.security_profile,
                    "reconnect_fallback": "bounded exponential backoff, heartbeat 10–120s, visible stale state, HTTP fallback required; replay currently unavailable",
                    "disposition": disp,
                    "reason": "Live user-visible domain updates; generic event stream optional when specialized channels exist.",
                    "product_boundary": (
                        "Operator Console"
                        if any(x in path for x in ("treasury", "provider"))
                        else "Core"
                    ),
                    "frontend_surface": "assigned domain screen",
                    "coverage_state": "CLIENT_ONLY",
                    "implementation_prompt": 4,
                    "privacy_policy": "limit_payload=true; no session/secret material persisted",
                    "contract_test": "tests/contract/test_websocket_versioned_contracts.py",
                    "browser_e2e": "not verified",
                    "rollback_disable": "disable subscription and retain visible polling/unavailable state",
                }
            )
    norm = {
        "metadata": {
            "head": head,
            "contract_source_fingerprint": fingerprints["contract_source_fingerprint"],
            "generator_fingerprint": fingerprints["generator_fingerprint"],
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
    authoritative = [
        {
            "matrix_id": op["matrix_id"],
            "operation_id": op["operation_id"],
            "method": op["method"],
            "path": op["path"],
            "request_schema": op["request_schema"],
            "success_schema": op["response_schema"],
            "success_status": op["success_status"],
            "error_schema": op["error_envelope"],
            "security": op["required_plan_scope_poa_pop_signing_human_intent"],
            "product": op["product_boundary"],
            "owner": op["typed_client_owner"],
            "transport_engine": "frontend.bastion_ui.transport.generated_transport",
            "retry_policy": "safe reads only; mutations require explicit idempotency contract",
        }
        for op in ops
        if op["authority_status"] == "AUTHORITATIVE_NOW"
        and op["disposition"] in ("UI_REQUIRED", "UI_OPTIONAL")
    ]
    blocked_candidates = [
        {
            "matrix_id": op["matrix_id"],
            "operation_id": op["operation_id"],
            "method": op["method"],
            "path": op["path"],
            "request_schema": op["request_schema"],
            "success_schema": op["response_schema"],
            "error_schema": op["error_envelope"],
            "security": op["required_plan_scope_poa_pop_signing_human_intent"],
            "blocker_id": op["authority_blocker_id"],
            "future_owner": op["authority_future_owner"],
            "reentry_condition": op["authority_reentry_condition"],
        }
        for op in ops
        if op["authority_blocker_id"] == "P1B-B01"
    ]
    ownership = {
        "metadata": norm["metadata"],
        "architecture": "generated typed operation descriptors over one shared injectable transport engine",
        "authoritative_http_operations": authoritative,
        "blocked_http_candidates": blocked_candidates,
        "deferred_http_operations": [
            {
                "matrix_id": op["matrix_id"],
                "operation_id": op["operation_id"],
                "method": op["method"],
                "path": op["path"],
                "blocker_id": op["authority_blocker_id"],
                "reason": op["reason"],
                "future_owner": op["authority_future_owner"],
                "reentry_condition": op["authority_reentry_condition"],
            }
            for op in ops
            if op["authority_status"] == "DEFERRED_AUTHORITY"
        ],
        "authoritative_websocket_contracts": ws,
        "deferred_websocket_protocols": [],
    }
    (OUT / "01_HTTP_CLIENT_OWNERSHIP_INPUT.json").write_text(
        json.dumps(ownership, indent=2, sort_keys=True) + "\n"
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
