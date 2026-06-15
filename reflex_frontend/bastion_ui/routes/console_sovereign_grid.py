from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.sovereign_grid_map import sovereign_grid_map
from bastion_ui.components.wow.node_pulse import node_pulse
from bastion_ui.components.wow.sovereignty_score_panel import sovereignty_score_panel
from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.sovereign_grid_panel import sovereign_grid_panel
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_sovereign_grid_page() -> rx.Component:
    return dashboard_shell(
        "Sovereign Grid",
        rx.vstack(
            console_page_header("Sovereign Grid", "Sovereign Grid is an operator visibility layer. It does not mutate infrastructure. It does not execute deployment actions."),
            console_status_strip(),
            sovereign_grid_map(),
            node_pulse(),
            sovereignty_score_panel(),
            sovereign_grid_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
