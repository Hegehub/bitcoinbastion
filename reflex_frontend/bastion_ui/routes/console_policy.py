from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.policy_engine_panel import policy_engine_panel
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_policy_page() -> rx.Component:
    return dashboard_shell(
        "Policy Engine",
        rx.vstack(
            console_page_header("Policy Engine", "Policy Engine output is advisory until reviewed by an operator. Risky actions require explicit human confirmation."),
            console_status_strip(),
            policy_engine_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
