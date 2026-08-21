"""Canonical route and navigation topology for Features 55 and 56."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import quote

from bastion_ui.feature_flags import FLAGS, FeatureFlagId, RolloutState

_PUBLIC = (
    ("/", "Bitcoin Bastion", "home_page"),
    ("/platform", "Platform", "platform_page"),
    ("/access", "Bastion Access", "access_page"),
    ("/access/plans", "Access Plans", "access_plans_page"),
    ("/access/checkout", "Access Checkout", "access_checkout_page"),
    ("/access/payment", "Payment", "access_payment_page"),
    ("/access/payment/pending", "Payment Pending", "access_payment_pending_page"),
    ("/access/payment/success", "Access Success", "access_success_page"),
    ("/access/certificate", "Access Certificate", "access_certificate_page"),
    ("/access/offline", "Offline Validity", "access_offline_page"),
    ("/wallet-auth", "Wallet Authentication", "wallet_auth_page"),
    ("/wallet-auth/register", "Wallet Registration", "wallet_register_page"),
    ("/wallet-auth/login", "Wallet Login", "wallet_login_page"),
    ("/wallet-auth/lnurl", "Lightning Login", "wallet_lnurl_page"),
    ("/wallet-auth/bitcoin", "Bitcoin Wallet Login", "wallet_bitcoin_page"),
    ("/wallet-auth/session", "PoP Session", "wallet_session_page"),
    ("/wallet-auth/devices", "Devices", "wallet_devices_page"),
    ("/wallet-auth/entitlements", "Entitlements", "wallet_entitlements_page"),
    ("/wallet-auth/subscription", "Subscription", "wallet_subscription_page"),
    ("/wallet-auth/step-up", "Step-up", "wallet_step_up_page"),
    ("/wallet-auth/recovery", "Recovery Capsule", "wallet_recovery_page"),
    ("/wallet-auth/lockdown", "Emergency Lockdown", "wallet_lockdown_page"),
    ("/wallet-auth/lightning", "Lightning Wallet", "wallet_lightning_page"),
    ("/wallet-auth/lightning/pay", "Lightning Payment", "wallet_lightning_pay_page"),
    ("/wallet-auth/lightning/withdraw", "Lightning Withdraw", "wallet_lightning_withdraw_page"),
    ("/wallet-auth/lightning/addresses", "Lightning Addresses", "wallet_lightning_addresses_page"),
    ("/wallet-auth/security", "Wallet Security", "wallet_security_page"),
    ("/lnurl/auth", "LNURL-auth", "lnurl_auth_page"),
    ("/lnurl/pay", "LNURL-pay", "lnurl_pay_page"),
    ("/lnurl/payment-status", "LNURL Payment Status", "lnurl_payment_status_page"),
    ("/business/access", "Business Access", "business_access_page"),
    ("/business/devices", "Business Devices", "business_devices_page"),
    ("/business/security", "Business Security", "business_security_page"),
    ("/register/access", "PayRegister Access", "register_access_page"),
    ("/register/devices", "PayRegister Devices", "register_devices_page"),
    ("/register/refunds", "PayRegister Refunds", "register_refunds_page"),
    ("/check", "Check Bitcoin Address", "check_page"),
    ("/trace", "Bastion Trace", "trace_page"),
    ("/developers", "Developers", "developers_page"),
    ("/operations", "Operations", "operations_page"),
    ("/operations/health", "Operations Health", "operations_health_page"),
    ("/operations/providers", "Operations Providers", "operations_providers_page"),
    ("/operations/storage", "Operations Storage", "operations_storage_page"),
    ("/operations/incidents", "Operations Incidents", "operations_incidents_page"),
    ("/operations/jobs", "Operations Jobs", "operations_jobs_page"),
    ("/operations/slo", "Operations SLO", "operations_slo_page"),
    ("/manifesto", "Manifesto", "manifesto_page"),
    ("/evidence", "Evidence", "evidence_page"),
    ("/status", "Status", "status_page"),
    ("/roadmap", "Roadmap", "roadmap_page"),
    ("/security", "Security", "security_page"),
    ("/access/security-posture", "Access Security Posture", "security_posture_page"),
    ("/websocket-lab", "WebSocket Contract Laboratory", "websocket_lab_page"),
    ("/docs", "Docs", "docs_page"),
)


class Product(StrEnum):
    CORE = "Bitcoin Bastion Core"
    PAYREGISTER = "PayRegister"


class RouteClass(StrEnum):
    PUBLIC = "PUBLIC"
    ACCESS_AWARE = "ACCESS_AWARE"
    PROTECTED = "PROTECTED"
    OPERATOR_ONLY = "OPERATOR_ONLY"
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
    SEPARATE_PRODUCT = "SEPARATE_PRODUCT"
    DEFERRED = "DEFERRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AvailabilityPolicy(StrEnum):
    RENDER = "RENDER"
    DISABLED_STATE = "DISABLED_STATE"
    LIFECYCLE_UNAVAILABLE = "LIFECYCLE_UNAVAILABLE"


class RouteOutcome(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    REDIRECT = "REDIRECT"
    NOT_FOUND = "NOT_FOUND"


class AliasStatus(StrEnum):
    COMPATIBILITY_ALIAS = "COMPATIBILITY_ALIAS"
    DEPRECATED_ALIAS = "DEPRECATED_ALIAS"


@dataclass(frozen=True)
class RouteAlias:
    path: str
    canonical_route_id: str
    status: AliasStatus


@dataclass(frozen=True)
class RouteRecord:
    id: str
    path: str
    product: Product
    domain: str
    component: str
    title: str
    route_class: RouteClass
    security_requirement_id: str
    feature_flag_id: FeatureFlagId
    nav_group: str | None = None
    nav_order: int = 0
    breadcrumb_parent: str | None = None
    nav_visible: bool = False
    mobile_eligible: bool = False
    availability_policy: AvailabilityPolicy = AvailabilityPolicy.RENDER
    http_operations: tuple[str, ...] = ()
    ws_families: tuple[str, ...] = ()
    future_prompt: int = 8
    aliases: tuple[str, ...] = ()


def _route_id(path: str) -> str:
    if path == "/":
        return "overview.home"
    return path.strip("/").replace("[", "").replace("]", "").replace("/", ".").replace("-", "_")


def _domain(path: str) -> str:
    first = path.strip("/").split("/", 1)[0] or "overview"
    return {"wallet-auth": "Access", "business": "Access", "register": "PayRegister"}.get(
        first, first.title()
    )


_NAV_PATHS = {
    "/",
    "/platform",
    "/access",
    "/trace",
    "/evidence",
    "/status",
    "/operations",
    "/operations/health",
    "/operations/providers",
    "/operations/storage",
    "/operations/incidents",
    "/operations/jobs",
    "/operations/slo",
    "/developers",
    "/docs",
    "/security",
    "/roadmap",
    "/market",
    "/console",
}


def _public_records() -> list[RouteRecord]:
    records: list[RouteRecord] = []
    public_paths = {item[0] for item in _PUBLIC}
    for index, (path, title, component) in enumerate(_PUBLIC):
        separate = path.startswith("/register/")
        development = path == "/websocket-lab"
        protected = path == "/access/security-posture" or path in {
            "/operations/incidents",
            "/operations/slo",
        }
        route_class = (
            RouteClass.SEPARATE_PRODUCT
            if separate
            else RouteClass.DEVELOPMENT_ONLY
            if development
            else RouteClass.PROTECTED
            if protected
            else RouteClass.PUBLIC
        )
        parent_path = "/" + path.strip("/").split("/", 1)[0] if path.count("/") > 1 else None
        records.append(
            RouteRecord(
                id=_route_id(path),
                path=path,
                product=Product.PAYREGISTER if separate else Product.CORE,
                domain=_domain(path),
                component=component,
                title=title,
                route_class=route_class,
                security_requirement_id="access.me" if protected else "public",
                feature_flag_id=(
                    FeatureFlagId.PAYREGISTER
                    if separate
                    else FeatureFlagId.WEBSOCKET_LAB
                    if development
                    else FeatureFlagId.CORE
                ),
                nav_group=_domain(path) if path in _NAV_PATHS else None,
                nav_order=index,
                breadcrumb_parent=(_route_id(parent_path) if parent_path in public_paths else None),
                nav_visible=path in _NAV_PATHS,
                mobile_eligible=path in {"/", "/access", "/trace", "/status"},
                availability_policy=(
                    AvailabilityPolicy.LIFECYCLE_UNAVAILABLE
                    if path in {"/status", "/websocket-lab"}
                    else AvailabilityPolicy.RENDER
                ),
                http_operations=(
                    ("get_me_api_v1_access_me_get",)
                    if path == "/access/security-posture"
                    else {
                        "/": (
                            "health_api_v1_health_get",
                            "providers_api_v1_health_providers_get",
                            "storage_status_api_v1_storage_status_get",
                        ),
                        "/operations": (
                            "health_api_v1_health_get",
                            "providers_api_v1_health_providers_get",
                            "storage_status_api_v1_storage_status_get",
                        ),
                        "/operations/health": ("health_api_v1_health_get",),
                        "/operations/providers": ("providers_api_v1_health_providers_get",),
                        "/operations/storage": ("storage_status_api_v1_storage_status_get",),
                        "/operations/incidents": (
                            "get_me_api_v1_access_me_get",
                            "operations_list_incidents",
                        ),
                        "/operations/jobs": (
                            "get_me_api_v1_access_me_get",
                            "jobs_api_v1_operations_jobs_get",
                        ),
                        "/operations/slo": ("get_me_api_v1_access_me_get", "operations_list_slo"),
                    }.get(path, ())
                ),
                ws_families=("events.v1",) if development else (),
                future_prompt=16
                if path.startswith(("/access", "/wallet-auth"))
                else 22
                if separate
                else 9
                if path in {"/operations/incidents", "/operations/jobs", "/operations/slo"}
                else 8,
            )
        )
    return records


_EXTRA = (
    ("console.home", "/console", "console_page", "Bastion Console", "Console"),
    (
        "console.command_center",
        "/console/command-center",
        "console_page",
        "Command Center",
        "Console",
    ),
    ("console.trace", "/console/trace", "console_trace_page", "Trace Console", "Trace"),
    (
        "console.evidence",
        "/console/evidence",
        "console_evidence_page",
        "Evidence Console",
        "Evidence",
    ),
    (
        "console.provider_health",
        "/console/provider-health",
        "console_provider_health_page",
        "Provider Health Console",
        "Operations",
    ),
    (
        "console.policy",
        "/console/policy",
        "console_policy_page",
        "Policy Engine Console",
        "Console",
    ),
    ("console.audit", "/console/audit", "console_audit_page", "Audit Log Console", "Console"),
    (
        "console.market_intelligence",
        "/console/market-intelligence",
        "console_market_intelligence_page",
        "Market Intelligence",
        "Market",
    ),
    (
        "console.time_machine",
        "/console/time-machine",
        "console_time_machine_page",
        "Console Time Machine",
        "Market",
    ),
    (
        "console.sovereign_grid",
        "/console/sovereign-grid",
        "console_sovereign_grid_page",
        "Sovereign Grid",
        "Console",
    ),
    (
        "console.api_explorer",
        "/console/api-explorer",
        "console_api_explorer_page",
        "API Explorer",
        "Console",
    ),
    ("market.home", "/market", "market_page", "Market Intelligence", "Market"),
    (
        "market.time_machine",
        "/market/time-machine",
        "market_time_machine_page",
        "Market Time Machine",
        "Market",
    ),
    (
        "market.replay",
        "/market/time-machine/[event_id]",
        "market_time_machine_page",
        "Historical Replay",
        "Market",
    ),
    ("market.timeline", "/market/timeline", "market_timeline_page", "Market Timeline", "Market"),
    (
        "market.similarity",
        "/market/similarity",
        "market_similarity_page",
        "Historical Similarity",
        "Market",
    ),
    ("market.signals", "/market/signals", "market_signals_page", "Market Signals", "Market"),
    ("market.evidence", "/market/evidence", "market_evidence_page", "Market Evidence", "Market"),
    (
        "market.narratives",
        "/market/narratives",
        "market_narratives_page",
        "Market Narratives",
        "Market",
    ),
    ("market.sources", "/market/sources", "market_sources_page", "Market Sources", "Market"),
    ("trace.report", "/trace/[report_id]", "trace_report_page", "Trace Report", "Trace"),
    (
        "trace.history",
        "/trace/[report_id]/history/[snapshot_id]",
        "trace_history_page",
        "Historical Trace Topology",
        "Trace",
    ),
    (
        "trace.proof_packet",
        "/trace/[report_id]/proof-packet",
        "trace_proof_packet_page",
        "Trace Proof Packet",
        "Evidence",
    ),
    (
        "trace.historical_proof_packet",
        "/trace/[report_id]/history/[snapshot_id]/proof-packet",
        "trace_proof_packet_page",
        "Historical Trace Proof Packet",
        "Evidence",
    ),
    (
        "development.design_system",
        "/design-system",
        "design_system_preview",
        "Design System Preview",
        "Development",
    ),
)


ROUTES: tuple[RouteRecord, ...] = tuple(_public_records()) + tuple(
    RouteRecord(
        id=id_,
        path=path,
        product=Product.CORE,
        domain=domain,
        component=component,
        title=title,
        route_class=RouteClass.PROTECTED
        if id_ in {
            "market.similarity",
            "trace.proof_packet",
            "trace.historical_proof_packet",
        }
        else RouteClass.DEVELOPMENT_ONLY
        if id_.startswith("development")
        else RouteClass.OPERATOR_ONLY
        if id_.startswith("console")
        else RouteClass.ACCESS_AWARE,
        security_requirement_id="access.me"
        if id_
        in {
            "market.similarity",
            "trace.proof_packet",
            "trace.historical_proof_packet",
        }
        else "operator"
        if id_.startswith("console")
        else "public",
        feature_flag_id=FeatureFlagId.DESIGN_SYSTEM
        if id_.startswith("development")
        else FeatureFlagId.CONSOLE
        if id_.startswith("console")
        else FeatureFlagId.CORE,
        nav_group=domain if path in {"/console", "/market"} else None,
        nav_order=i,
        breadcrumb_parent="trace"
        if id_.startswith("trace.")
        else "console.home"
        if id_.startswith("console.") and id_ != "console.home"
        else "market.home"
        if id_.startswith("market.") and id_ != "market.home"
        else None,
        nav_visible=path
        in {
            "/console",
            "/market",
            "/market/signals",
            "/market/timeline",
            "/market/similarity",
            "/market/time-machine",
            "/market/narratives",
            "/market/sources",
        },
        mobile_eligible=False,
        http_operations=(
            ("market_current_overview",)
            if id_ == "market.home"
            else ("top_signals_api_v1_signals_top_get",)
            if id_ == "market.signals"
            else ("market_history_timeline",)
            if id_ == "market.timeline"
            else ("market_similarity_report",)
            if id_ == "market.similarity"
            else ("market_history_replay_event", "market_history_attributions")
            if id_ == "market.time_machine"
            else ("market_history_replay_event",)
            if id_ == "market.replay"
            else ("market_history_narratives",)
            if id_ == "market.narratives"
            else ("market_history_sources",)
            if id_ == "market.sources"
            else (
                "get_trace_graph_history_api_v1_trace_report__report_id__graph_history_get",
                "get_exact_trace_graph_snapshot",
                "get_current_trace_disagreement",
            )
            if id_ == "trace.report"
            else ("get_exact_trace_graph_snapshot", "get_historical_trace_disagreement")
            if id_ == "trace.history"
            else (
                "get_current_trace_proof_packet",
                "get_trace_evidence_lineage",
                "replay_trace_evidence",
                "verify_trace_evidence_identity",
                "export_trace_evidence",
            )
            if id_ == "trace.proof_packet"
            else (
                "get_historical_trace_proof_packet",
                "get_trace_evidence_lineage",
                "replay_trace_evidence",
                "verify_trace_evidence_identity",
                "export_trace_evidence",
            )
            if id_ == "trace.historical_proof_packet"
            else ()
        ),
        future_prompt=12 if id_.startswith("trace") else 19 if id_.startswith("console") else 9,
    )
    for i, (id_, path, component, title, domain) in enumerate(_EXTRA)
)
ROUTE_BY_ID = {route.id: route for route in ROUTES}
ALIASES: tuple[RouteAlias, ...] = (
    RouteAlias("/products", "platform", AliasStatus.DEPRECATED_ALIAS),
    RouteAlias("/self-host", "operations", AliasStatus.DEPRECATED_ALIAS),
    RouteAlias("/console/wow", "console.command_center", AliasStatus.DEPRECATED_ALIAS),
)

KNOWN_SECURITY_REQUIREMENTS = frozenset({"public", "access.me", "operator"})
KNOWN_WS_FAMILIES = frozenset({"events.v1"})


def validate_routes(*, component_names: set[str] | None = None) -> None:
    ids = [route.id for route in ROUTES]
    paths = [route.path for route in ROUTES]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate active route ID")
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate active canonical path")
    for route in ROUTES:
        if not route.path.startswith("/") or "//" in route.path:
            raise ValueError(f"invalid route pattern: {route.id}")
        params = re.findall(r"\[([^]]+)\]", route.path)
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", p) for p in params):
            raise ValueError(f"invalid dynamic parameter: {route.id}")
        if route.breadcrumb_parent and route.breadcrumb_parent not in ROUTE_BY_ID:
            raise ValueError(f"unknown breadcrumb parent: {route.id}")
        if route.product is Product.PAYREGISTER and not route.id.startswith("register."):
            raise ValueError(f"PayRegister boundary violation: {route.id}")
        if component_names is not None and route.component not in component_names:
            raise ValueError(f"unknown component {route.component}: {route.id}")
    alias_paths: set[str] = set()
    for alias in ALIASES:
        if alias.path in paths or alias.path in alias_paths:
            raise ValueError(f"alias collision: {alias.path}")
        if alias.canonical_route_id not in ROUTE_BY_ID:
            raise ValueError(f"unknown alias target: {alias.path}")
        if not alias.path.startswith("/") or alias.path.startswith("//") or "://" in alias.path:
            raise ValueError(f"unsafe alias: {alias.path}")
        alias_paths.add(alias.path)


def validate_dependencies() -> None:
    """Fail active topology when any canonical dependency identity is unknown."""
    from bastion_ui.transport.generated_http import OWNERSHIP

    for route in ROUTES:
        unknown_http = set(route.http_operations) - set(OWNERSHIP)
        unknown_ws = set(route.ws_families) - KNOWN_WS_FAMILIES
        if unknown_http:
            raise ValueError(f"unknown HTTP dependency for {route.id}: {sorted(unknown_http)}")
        if unknown_ws:
            raise ValueError(f"unknown WS dependency for {route.id}: {sorted(unknown_ws)}")
        if route.security_requirement_id not in KNOWN_SECURITY_REQUIREMENTS:
            raise ValueError(f"unknown security dependency for {route.id}")
        if route.feature_flag_id not in FLAGS:
            raise ValueError(f"unknown flag dependency for {route.id}")
        if route.product not in Product:
            raise ValueError(f"unknown product dependency for {route.id}")


def redirect_for_alias(path: str) -> str:
    """Resolve only registered internal aliases; arbitrary redirect targets are impossible."""
    alias = next((item for item in ALIASES if item.path == path), None)
    if alias is None:
        raise ValueError("unknown or unsafe redirect alias")
    return path_for(alias.canonical_route_id)


def resolve_path(
    path: str, flags: dict[FeatureFlagId, RolloutState]
) -> tuple[RouteOutcome, str | None]:
    """Resolve direct URLs without conflating disabled, alias and unknown states."""
    alias = next((item for item in ALIASES if item.path == path), None)
    if alias:
        target = alias.canonical_route_id
        return (
            RouteOutcome.REDIRECT if route_enabled(target, flags) else RouteOutcome.DISABLED,
            target,
        )
    route_id = next((route.id for route in ROUTES if route.path == path), None)
    if route_id is None:
        for route in ROUTES:
            pattern = re.escape(route.path)
            pattern = re.sub(r"\\\[[^]]+\\\]", r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", pattern)
            if re.fullmatch(pattern, path):
                route_id = route.id
                break
    if route_id is None:
        return RouteOutcome.NOT_FOUND, None
    return (
        RouteOutcome.ENABLED if route_enabled(route_id, flags) else RouteOutcome.DISABLED,
        route_id,
    )


def path_for(route_id: str, **parameters: str) -> str:
    try:
        path = ROUTE_BY_ID[route_id].path
    except KeyError as exc:
        raise KeyError(f"unknown route ID: {route_id}") from exc
    required = re.findall(r"\[([^]]+)\]", path)
    if set(parameters) != set(required):
        raise ValueError(f"route {route_id} requires parameters {required}")
    for name in required:
        value = parameters[name]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
            raise ValueError(f"unsafe route parameter: {name}")
        path = path.replace(f"[{name}]", quote(value, safe=""))
    return path


def dynamic_route_parts(route_id: str, parameter: str) -> tuple[str, str]:
    """Return registry-owned path parts for composition with a Reflex string Var."""
    path = ROUTE_BY_ID[route_id].path
    marker = f"[{parameter}]"
    if path.count(marker) != 1:
        raise ValueError(f"route {route_id} has no unique parameter {parameter}")
    before, after = path.split(marker)
    return before, after


def breadcrumbs(route_id: str) -> tuple[RouteRecord, ...]:
    trail: list[RouteRecord] = []
    current = ROUTE_BY_ID[route_id]
    seen: set[str] = set()
    while current.id not in seen:
        seen.add(current.id)
        trail.append(current)
        if current.breadcrumb_parent is None:
            break
        current = ROUTE_BY_ID[current.breadcrumb_parent]
    return tuple(reversed(trail))


def route_enabled(route_id: str, flags: dict[FeatureFlagId, RolloutState]) -> bool:
    return flags[ROUTE_BY_ID[route_id].feature_flag_id] is not RolloutState.OFF


def hardcoded_href_consumers(source_root: Path) -> tuple[str, ...]:
    """Find literal internal hrefs while excluding anchors, APIs, assets and tests."""
    findings: list[str] = []
    for source in sorted(source_root.rglob("*.py")):
        if "tests" in source.parts:
            continue
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or node.arg != "href":
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                href = value.value
                if href.startswith("/") and not href.startswith(("/api/", "//")):
                    findings.append(f"{source}:{node.lineno}:{href}")
    return tuple(findings)
