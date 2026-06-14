from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.market_intelligence_panel import market_intelligence_panel
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_market_intelligence_page() -> rx.Component:
    return dashboard_shell(
        "Market Intelligence",
        rx.vstack(
            console_page_header("Market Intelligence", "Market Intelligence is evidence-based and informational only. It does not provide financial advice. It does not guarantee future market behavior."),
            console_status_strip(),
            market_intelligence_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
