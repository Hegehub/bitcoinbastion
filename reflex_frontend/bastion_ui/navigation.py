from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NavStatus = Literal["active", "preview", "coming_soon", "legacy", "hidden"]
VALID_NAV_STATUSES: tuple[NavStatus, ...] = (
    "active",
    "preview",
    "coming_soon",
    "legacy",
    "hidden",
)

TRACE_SAFETY_NOTE = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. "
    "Public Bitcoin addresses only."
)
EVIDENCE_SAFETY_NOTE = (
    "Evidence packets explain source material and system reasoning. They are not custody, "
    "legal verification, or transaction approval."
)
TREASURY_POLICY_SAFETY_NOTE = (
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
    status: NavStatus = "preview"
    requires_input: bool = False
    safety_note: str | None = None


PUBLIC_NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("Platform", "/platform", "public", "preview", "Product platform overview."),
    NavItem(
        "Trace",
        "/trace",
        "public",
        "preview",
        "Address and report workflows.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    NavItem(
        "Evidence",
        "/evidence",
        "public",
        "preview",
        "Evidence and proof packet entry point.",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    NavItem(
        "Status", "/status", "public", "preview", "Service status and degraded-state visibility."
    ),
    NavItem("Developers", "/developers", "public", "preview", "API and integration resources."),
    NavItem(
        "Operations", "/operations", "public", "preview", "Operator and self-hosting guidance."
    ),
    NavItem("Docs", "/docs", "public", "preview", "Documentation hub."),
    NavItem("Security", "/security", "public", "preview", "Security posture and no-custody rules."),
    NavItem("Roadmap", "/roadmap", "public", "preview", "Roadmap and cutover milestones."),
)

FOOTER_NAV_ITEMS: tuple[NavItem, ...] = PUBLIC_NAV_ITEMS

MOBILE_NAV_ITEMS: tuple[NavItem, ...] = (
    *PUBLIC_NAV_ITEMS,
    NavItem(
        "Check Bitcoin Address",
        "/check",
        "public",
        "preview",
        "Address check entry point.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    NavItem("Console", "/console", "console", "preview", "Operator console shell."),
)

CONSOLE_NAV_ITEMS: tuple[NavItem, ...] = (
    NavItem("Dashboard", "/console", "console", "preview", "Console overview shell."),
    NavItem(
        "Trace",
        "/console/trace",
        "console",
        "preview",
        "Trace console workspace.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    NavItem(
        "Evidence",
        "/console/evidence",
        "console",
        "preview",
        "Evidence review workspace.",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    NavItem(
        "Provider Health",
        "/console/provider-health",
        "console",
        "coming_soon",
        "Provider health matrix.",
    ),
    NavItem(
        "Market Intelligence",
        "/console/market-intelligence",
        "console",
        "preview",
        "Market intelligence console shell.",
    ),
    NavItem(
        "Time Machine", "/console/time-machine", "console", "preview", "Time Machine console shell."
    ),
    NavItem(
        "Sovereign Grid",
        "/console/sovereign-grid",
        "console",
        "preview",
        "Sovereign infrastructure overview.",
    ),
    NavItem(
        "Policy Engine",
        "/console/policy",
        "console",
        "preview",
        "Review-first policy workspace.",
        safety_note=TREASURY_POLICY_SAFETY_NOTE,
    ),
    NavItem("Audit Log", "/console/audit", "console", "preview", "Operator audit log."),
    NavItem(
        "Deployment Status",
        "/console/deployment",
        "console",
        "coming_soon",
        "Deployment and release status.",
    ),
    NavItem("API Explorer", "/console/api", "console", "coming_soon", "API exploration workspace."),
)

COMMAND_PALETTE_ACTIONS: tuple[CommandAction, ...] = (
    CommandAction(
        "open-platform", "Open Platform", "/platform", "Navigation", "Open platform overview."
    ),
    CommandAction(
        "open-trace",
        "Open Trace",
        "/trace",
        "Trace",
        "Open Trace entry point.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        "check-address",
        "Check Bitcoin Address",
        "/check",
        "Trace",
        "Open public-address check flow.",
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        "open-trace-report",
        "Open Trace Report",
        "/trace/{report_id}",
        "Trace",
        "Requires a report identifier before navigation.",
        requires_input=True,
        safety_note=TRACE_SAFETY_NOTE,
    ),
    CommandAction(
        "open-proof-packet",
        "Open Proof Packet",
        "/trace/{report_id}/proof-packet",
        "Evidence",
        "Requires a report identifier before navigation.",
        requires_input=True,
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    CommandAction(
        "open-evidence",
        "Open Evidence",
        "/evidence",
        "Evidence",
        "Open evidence index.",
        safety_note=EVIDENCE_SAFETY_NOTE,
    ),
    CommandAction("open-status", "Open Status", "/status", "Navigation", "Open service status."),
    CommandAction("open-console", "Open Console", "/console", "Console", "Open console shell."),
    CommandAction(
        "open-market-intelligence",
        "Open Market Intelligence",
        "/console/market-intelligence",
        "Market",
        "Open market intelligence shell.",
    ),
    CommandAction(
        "open-time-machine",
        "Open Time Machine",
        "/console/time-machine",
        "Market",
        "Open Time Machine shell.",
    ),
    CommandAction(
        "open-sovereign-grid",
        "Open Sovereign Grid",
        "/console/sovereign-grid",
        "Console",
        "Open sovereign grid shell.",
    ),
    CommandAction(
        "open-policy",
        "Open Policy Engine",
        "/console/policy",
        "Console",
        "Open review-first policy shell.",
        safety_note=TREASURY_POLICY_SAFETY_NOTE,
    ),
    CommandAction(
        "open-audit", "Open Audit Log", "/console/audit", "Console", "Open audit log shell."
    ),
    CommandAction(
        "open-api", "Open API Explorer", "/console/api", "Developer", "Open API explorer shell."
    ),
    CommandAction(
        "open-operations",
        "Open Operations",
        "/operations",
        "Operations",
        "Open operations guidance.",
    ),
    CommandAction(
        "open-developers",
        "Open Developers",
        "/developers",
        "Developer",
        "Open developer resources.",
    ),
    CommandAction("open-docs", "Open Docs", "/docs", "Developer", "Open documentation."),
    CommandAction(
        "open-security", "Open Security", "/security", "Security", "Open security posture."
    ),
    CommandAction(
        "open-roadmap", "Open Roadmap", "/roadmap", "Navigation", "Open migration roadmap."
    ),
)


def search_command_actions(query: str) -> tuple[CommandAction, ...]:
    normalized = query.casefold().strip()
    if not normalized:
        return COMMAND_PALETTE_ACTIONS
    return tuple(
        action
        for action in COMMAND_PALETTE_ACTIONS
        if normalized in action.title.casefold() or normalized in action.route.casefold()
    )
