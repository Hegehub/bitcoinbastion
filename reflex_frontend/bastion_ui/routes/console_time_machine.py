from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_page_header import console_page_header
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.time_machine_panel import time_machine_panel
from bastion_ui.components.console.operator_notice import operator_notice
from bastion_ui.components.ui.card import safety_card


def console_time_machine_page() -> rx.Component:
    return dashboard_shell(
        "Time Machine",
        rx.vstack(
            console_page_header("Time Machine", "Historical similarity does not guarantee future market behavior. Past market reactions are contextual evidence only. Correlation is not causation. Existing /market routes are not replaced."),
            console_status_strip(),
            time_machine_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
