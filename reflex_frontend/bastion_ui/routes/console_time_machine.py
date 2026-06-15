from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.time_machine_timeline import time_machine_timeline
from bastion_ui.components.wow.historical_similarity_lens import historical_similarity_lens
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
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
            time_machine_timeline(),
            historical_similarity_lens(),
            evidence_chain_viewer(),
            time_machine_panel(),
            safety_card(rx.text("Read-only preview. Operator review required. Evidence-based. Advisory-only. No custody. No private key or seed phrase handling. Degraded, fallback, stale, and unavailable states must remain visible."), title="Limitations"),
            operator_notice(),
            spacing="4",
            width="100%",
        ),
    )
