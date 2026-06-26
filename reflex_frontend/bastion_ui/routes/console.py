from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.module_tile import module_tile
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card


def console_page() -> rx.Component:
    return dashboard_shell(
        rx.vstack(
            rx.heading("Bastion Console", size="7"),
            rx.text(
                "Safe operator shell for Bitcoin Bastion status, module navigation, "
                "degraded states, and advisory review."
            ),
            responsive_grid(
                module_tile(
                    "Trace",
                    "Advisory Bitcoin address intelligence, evidence, privacy, origin, "
                    "and policy facts.",
                    "/console/trace",
                    "partial",
                    True,
                ),
                module_tile(
                    "Evidence",
                    "Evidence review surfaces, packets, limitations, and provider disagreement.",
                    "/console/evidence",
                    "partial",
                    True,
                ),
                module_tile(
                    "Provider Health",
                    "Provider availability, stale data, fallback state, and source limitations.",
                    "/console/provider-health",
                    "unknown",
                    True,
                ),
                module_tile(
                    "Policy Engine",
                    "Review-first policy facts and manual approval boundaries.",
                    "/console/policy",
                    "placeholder",
                    True,
                ),
                module_tile(
                    "Audit Log",
                    "Audit event review placeholder with no execution behavior.",
                    "/console/audit",
                    "placeholder",
                    True,
                ),
                module_tile(
                    "Market Intelligence",
                    "Operator overview for market intelligence and degraded data.",
                    "/console/market-intelligence",
                    "partial",
                    True,
                ),
                module_tile(
                    "Time Machine",
                    "Market reconstruction console module with degraded Time Machine visibility.",
                    "/console/time-machine",
                    "partial",
                    True,
                ),
                module_tile(
                    "Sovereign Grid",
                    "Frontend readiness and sovereignty posture console module.",
                    "/console/sovereign-grid",
                    "partial",
                    True,
                ),
                module_tile(
                    "API Explorer",
                    "Safe API capability inspection and read-only examples.",
                    "/console/api-explorer",
                    "partial",
                    True,
                ),
            ),
            card(
                rx.text("Console shell exists; module internals are implemented progressively."),
                rx.text("Risky actions are not executed by this console shell."),
                rx.text("Unknown, degraded, stale, and fallback states are shown explicitly."),
                title="Migration status",
                variant="console",
            ),
            card(
                rx.text(
                    "Prompt 14/22 adds Trace, Evidence, Provider Health, Policy, "
                    "and Audit internals."
                ),
                rx.text(
                    "Prompt 15/22 adds advanced Market, Time Machine, Sovereign "
                    "Grid, and API Explorer modules."
                ),
                title="Next modules",
                variant="console",
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )
