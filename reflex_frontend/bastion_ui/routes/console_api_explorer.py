from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.api_explorer_panel import api_explorer_panel
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_api_explorer_page() -> rx.Component:
    return dashboard_shell(
        "API Explorer",
        rx.vstack(
            console_page_header("API Explorer", "API Explorer is documentation-oriented. It does not execute risky actions. Endpoints may require authentication, rate limits, or deployment-specific configuration."),
            console_status_strip(),
            api_explorer_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
