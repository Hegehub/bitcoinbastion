from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NavStatus = Literal["active", "preview", "coming_soon", "legacy", "hidden"]

TRACE_SAFETY_NOTE = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. "
    "Public Bitcoin addresses only."
)
EVIDENCE_SAFETY_NOTE = (
    "Evidence packets explain source material and system reasoning. They are not custody, "
    "legal verification, or transaction approval."
)
POLICY_SAFETY_NOTE = (
    "Treasury and policy workflows are review-first and must not execute risky actions "
    "automatically."
)


@dataclass(frozen=True)
class NavItem:
    label: str
    route: str
    section: str
    status: NavStatus = "active"
    description: str | None = None
    requires_input: bool = False
    safety_note: str | None = None


@dataclass(frozen=True)
class CommandAction:
    id: str
    title: str
    route: str
    category: str
    description: str
    status: NavStatus = "active"
    requires_input: bool = False
    safety_note: str | None = None


PUBLIC_NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem(
        label="Platform",
        route="/platform",
        section="public",
        status="preview",
        description="Platform overview.",
    ),
    NavItem(
        label="Trace",
        route="/trace",
        section="public",
        status="preview",
        description="Trace entry point.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    NavItem(
        label="Evidence",
        route="/evidence",
        section="public",
        status="preview",
        description="Evidence overview.",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    NavItem("Status", "/status", "public", "preview", "Platform status."),
    NavItem("Developers", "/developers", "public", "preview", "Developer resources."),
    NavItem("Operations", "/operations", "public", "preview", "Operator guidance."),
    NavItem("Docs", "/docs", "public", "preview", "Documentation."),
    NavItem("Security", "/security", "public", "preview", "Security model."),
    NavItem("Roadmap", "/roadmap", "public", "preview", "Migration roadmap."),
)

FOOTER_NAV_ITEMS: tuple[NavItem, ...] = PUBLIC_NAV_ITEMS

CONSOLE_NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("Dashboard", "/console", "console", "preview", "Console overview."),
    NavItem(
        label="Trace",
        route="/console/trace",
        section="console",
        status="preview",
        description="Trace operations.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    NavItem(
        label="Evidence",
        route="/console/evidence",
        section="console",
        status="preview",
        description="Evidence review.",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    NavItem(
        "Provider Health",
        "/console/provider-health",
        "console",
        "preview",
        "Provider status.",
    ),
    NavItem(
        "Market Intelligence",
        "/console/market-intelligence",
        "console",
        "preview",
        "Market intelligence console.",
    ),
    NavItem(
        "Time Machine",
        "/console/time-machine",
        "console",
        "preview",
        "Market Time Machine console.",
    ),
    NavItem(
        "Sovereign Grid",
        "/console/sovereign-grid",
        "console",
        "preview",
        "Sovereign Grid console.",
    ),
    NavItem(
        label="Policy Engine",
        route="/console/policy",
        section="console",
        status="preview",
        description="Policy review.",
        safety_note=POLICY_SAFETY_NOTE,
    ),
    NavItem("Audit Log", "/console/audit", "console", "preview", "Audit events."),
    NavItem(
        "Deployment Status",
        "/console/deployment",
        "console",
        "coming_soon",
        "Deployment status.",
    ),
    NavItem("API Explorer", "/console/api-explorer", "console", "preview", "API explorer."),
    NavItem("Wow Layer", "/console/wow", "console", "preview", "Operator visual layer."),
)

COMMAND_PALETTE_ACTIONS: tuple[CommandAction, ...] = (
    CommandAction(
        "open-platform",
        "Open Platform",
        "/platform",
        "Navigation",
        "Open platform overview.",
        "preview",
    ),
    CommandAction(
        "open-trace",
        "Open Trace",
        "/trace",
        "Trace",
        "Open Trace workflow.",
        "preview",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        "check-address",
        "Check Bitcoin Address",
        "/check",
        "Trace",
        "Check a public Bitcoin address.",
        "preview",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        id="open-trace-report",
        title="Open Trace Report",
        route="/trace/{report_id}",
        category="Trace",
        description="Open a Trace report by id.",
        status="preview",
        requires_input=True,
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        id="open-proof-packet",
        title="Open Proof Packet",
        route="/trace/{report_id}/proof-packet",
        category="Trace",
        description="Open a Proof Packet by report id.",
        status="preview",
        requires_input=True,
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    CommandAction(
        "open-evidence",
        "Open Evidence",
        "/evidence",
        "Evidence",
        "Open evidence overview.",
        "preview",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    CommandAction("open-status", "Open Status", "/status", "Navigation", "Open status.", "preview"),
    CommandAction(
        "open-console",
        "Open Console",
        "/console",
        "Console",
        "Open console.",
        "preview",
    ),
    CommandAction(
        "open-market-intelligence",
        "Open Market Intelligence",
        "/console/market-intelligence",
        "Market",
        "Open Market Intelligence console.",
        "preview",
    ),
    CommandAction(
        "open-market-time-machine",
        "Open Market Time Machine",
        "/market/time-machine",
        "Market",
        "Open Market Time Machine.",
        "preview",
    ),
    CommandAction(
        "open-market-timeline",
        "Open Market Timeline",
        "/market/timeline",
        "Market",
        "Open Market Timeline.",
        "preview",
    ),
    CommandAction(
        "open-market-signals",
        "Open Market Signals",
        "/market/signals",
        "Market",
        "Open Market Signals.",
        "preview",
    ),
    CommandAction(
        "open-market-evidence",
        "Open Market Evidence",
        "/market/evidence",
        "Market",
        "Open Market Evidence.",
        "preview",
    ),
    CommandAction(
        "open-market-narratives",
        "Open Market Narratives",
        "/market/narratives",
        "Market",
        "Open Market Narratives.",
        "preview",
    ),
    CommandAction(
        "open-market-sources",
        "Open Market Sources",
        "/market/sources",
        "Market",
        "Open Market Sources.",
        "preview",
    ),
    CommandAction(
        "open-time-machine",
        "Open Time Machine",
        "/console/time-machine",
        "Market",
        "Open Time Machine console.",
        "preview",
    ),
    CommandAction(
        "open-sovereign-grid",
        "Open Sovereign Grid",
        "/console/sovereign-grid",
        "Console",
        "Open Sovereign Grid console.",
        "preview",
    ),
    CommandAction(
        "open-policy",
        "Open Policy Engine",
        "/console/policy",
        "Console",
        "Open Policy Engine.",
        "preview",
        safety_note=POLICY_SAFETY_NOTE,
    ),
    CommandAction(
        "open-audit",
        "Open Audit Log",
        "/console/audit",
        "Console",
        "Open Audit Log.",
        "preview",
    ),
    CommandAction(
        "open-api",
        "Open API Explorer",
        "/console/api-explorer",
        "Developer",
        "Open API Explorer.",
        "preview",
    ),
    CommandAction(
        "open-wow",
        "Open Wow Layer",
        "/console/wow",
        "Console",
        "Open operator visual layer.",
        "preview",
    ),
    CommandAction(
        "open-operations",
        "Open Operations",
        "/operations",
        "Operations",
        "Open operations page.",
        "preview",
    ),
    CommandAction(
        "open-developers",
        "Open Developers",
        "/developers",
        "Developer",
        "Open developer page.",
        "preview",
    ),
    CommandAction("open-docs", "Open Docs", "/docs", "Developer", "Open documentation.", "preview"),
    CommandAction(
        "open-security",
        "Open Security",
        "/security",
        "Security",
        "Open security page.",
        "preview",
    ),
    CommandAction(
        "open-roadmap",
        "Open Roadmap",
        "/roadmap",
        "Navigation",
        "Open roadmap.",
        "preview",
    ),
)


def filter_command_actions(query: str) -> tuple[CommandAction, ...]:
    normalized = query.strip().lower()
    if not normalized:
        return COMMAND_PALETTE_ACTIONS
    return tuple(
        action
        for action in COMMAND_PALETTE_ACTIONS
        if normalized in action.title.lower() or normalized in action.route.lower()
    )


VALID_NAV_STATUSES: set[str] = {"active", "preview", "coming_soon", "legacy", "hidden"}
STALE_CANONICAL_ROUTES: set[str] = {"/products", "/self-host"}
