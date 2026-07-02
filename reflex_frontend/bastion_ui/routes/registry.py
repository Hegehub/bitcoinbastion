from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import reflex as rx

from bastion_ui.routes.check import check_page
from bastion_ui.routes.console import console_page
from bastion_ui.routes.console_api_explorer import console_api_explorer_page
from bastion_ui.routes.console_audit import console_audit_page
from bastion_ui.routes.console_evidence import console_evidence_page
from bastion_ui.routes.console_market_intelligence import console_market_intelligence_page
from bastion_ui.routes.console_policy import console_policy_page
from bastion_ui.routes.console_provider_health import console_provider_health_page
from bastion_ui.routes.console_sovereign_grid import console_sovereign_grid_page
from bastion_ui.routes.console_time_machine import console_time_machine_page
from bastion_ui.routes.console_trace import console_trace_page
from bastion_ui.routes.console_wow import console_wow_page
from bastion_ui.routes.design_system import design_system_preview
from bastion_ui.routes.developers import developers_page
from bastion_ui.routes.docs import docs_page
from bastion_ui.routes.evidence import evidence_page
from bastion_ui.routes.home import home_page
from bastion_ui.routes.manifesto import manifesto_page
from bastion_ui.routes.market import market_page
from bastion_ui.routes.market_evidence import market_evidence_page
from bastion_ui.routes.market_narratives import market_narratives_page
from bastion_ui.routes.market_signals import market_signals_page
from bastion_ui.routes.market_sources import market_sources_page
from bastion_ui.routes.market_time_machine import market_time_machine_page
from bastion_ui.routes.market_timeline import market_timeline_page
from bastion_ui.routes.operations import operations_page
from bastion_ui.routes.platform import platform_page
from bastion_ui.routes.proof_packet import trace_proof_packet_page
from bastion_ui.routes.roadmap import roadmap_page
from bastion_ui.routes.security import security_page
from bastion_ui.routes.status import status_page
from bastion_ui.routes.trace import trace_page
from bastion_ui.routes.trace_report import trace_report_page


@dataclass(frozen=True)
class RouteSpec:
    """Reflex route declaration kept outside the app bootstrap."""

    route: str
    title: str
    page: Callable[[], rx.Component]
    owner: str = "reflex"
    status: str = "implemented"


PUBLIC_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec("/", "Bitcoin Bastion", home_page),
    RouteSpec("/platform", "Platform", platform_page),
    RouteSpec("/developers", "Developers", developers_page),
    RouteSpec("/operations", "Operations", operations_page),
    RouteSpec("/manifesto", "Manifesto", manifesto_page),
    RouteSpec("/evidence", "Evidence", evidence_page),
    RouteSpec("/status", "Status", status_page),
    RouteSpec("/roadmap", "Roadmap", roadmap_page),
    RouteSpec("/security", "Security", security_page),
    RouteSpec("/docs", "Docs", docs_page),
    RouteSpec("/check", "Check Bitcoin Address", check_page),
    RouteSpec("/trace", "Bastion Trace", trace_page),
)

TRACE_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec("/trace/[report_id]", "Trace Report", trace_report_page),
    RouteSpec("/trace/[report_id]/proof-packet", "Trace Proof Packet", trace_proof_packet_page),
)

CONSOLE_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec("/console", "Bastion Console", console_page),
    RouteSpec("/console/command-center", "Command Center", console_page),
    RouteSpec("/console/wow", "Bastion Wow Layer", console_wow_page),
    RouteSpec("/console/trace", "Trace Console", console_trace_page),
    RouteSpec("/console/evidence", "Evidence Console", console_evidence_page),
    RouteSpec("/console/provider-health", "Provider Health Console", console_provider_health_page),
    RouteSpec("/console/market-intelligence", "Market Intelligence", console_market_intelligence_page),
    RouteSpec("/console/time-machine", "Console Time Machine", console_time_machine_page),
    RouteSpec("/console/sovereign-grid", "Sovereign Grid", console_sovereign_grid_page),
    RouteSpec("/console/policy", "Policy Engine Console", console_policy_page),
    RouteSpec("/console/audit", "Audit Log Console", console_audit_page),
    RouteSpec("/console/api-explorer", "API Explorer", console_api_explorer_page),
)

MARKET_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec("/market", "Market Intelligence", market_page),
    RouteSpec("/market/time-machine", "Market Time Machine", market_time_machine_page),
    RouteSpec("/market/timeline", "Market Timeline", market_timeline_page),
    RouteSpec("/market/signals", "Market Signals", market_signals_page),
    RouteSpec("/market/evidence", "Market Evidence", market_evidence_page),
    RouteSpec("/market/narratives", "Market Narratives", market_narratives_page),
    RouteSpec("/market/sources", "Market Sources", market_sources_page),
)

DEVELOPMENT_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    RouteSpec("/design-system", "Design System Preview", design_system_preview),
)

ALL_ROUTE_SPECS: tuple[RouteSpec, ...] = (
    PUBLIC_ROUTE_SPECS
    + TRACE_ROUTE_SPECS
    + CONSOLE_ROUTE_SPECS
    + MARKET_ROUTE_SPECS
    + DEVELOPMENT_ROUTE_SPECS
)

PUBLIC_ROUTES: tuple[str, ...] = tuple(spec.route for spec in PUBLIC_ROUTE_SPECS + TRACE_ROUTE_SPECS)
CONSOLE_ROUTES: tuple[str, ...] = tuple(spec.route for spec in CONSOLE_ROUTE_SPECS)
MARKET_ROUTES: dict[str, dict[str, str]] = {
    spec.route: {"owner": spec.owner, "status": spec.status} for spec in MARKET_ROUTE_SPECS
}
DEVELOPMENT_ROUTES: tuple[str, ...] = tuple(spec.route for spec in DEVELOPMENT_ROUTE_SPECS)

STALE_ROUTES: frozenset[str] = frozenset({"/products", "/self-host"})
ALL_REFLEX_ROUTES: tuple[str, ...] = tuple(spec.route for spec in ALL_ROUTE_SPECS)


def register_routes(app: rx.App) -> None:
    """Register every Reflex page from the domain route registry."""

    for spec in ALL_ROUTE_SPECS:
        app.add_page(spec.page, route=spec.route, title=spec.title)


__all__ = [
    "ALL_REFLEX_ROUTES",
    "ALL_ROUTE_SPECS",
    "CONSOLE_ROUTES",
    "CONSOLE_ROUTE_SPECS",
    "DEVELOPMENT_ROUTES",
    "DEVELOPMENT_ROUTE_SPECS",
    "MARKET_ROUTES",
    "MARKET_ROUTE_SPECS",
    "PUBLIC_ROUTES",
    "PUBLIC_ROUTE_SPECS",
    "RouteSpec",
    "STALE_ROUTES",
    "TRACE_ROUTE_SPECS",
    "register_routes",
]
