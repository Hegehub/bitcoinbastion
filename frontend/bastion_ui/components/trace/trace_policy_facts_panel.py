from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_policy_facts_panel() -> rx.Component:
    return card(
        rx.text(
            "Policy facts, warnings, failures, and manual-review requirements do not create "
            "legal or payment approval."
        ),
        rx.text(
            "Backend fields are rendered only when available; "
            "otherwise manual review is recommended."
        ),
        rx.cond(TraceReportState.has_degraded_data, rx.text("This panel may be incomplete.")),
        title="Policy facts",
    )
