from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_counterparty_panel() -> rx.Component:
    return card(
        rx.text(
            "Counterparty relationship hints are evidence-limited and do not identify "
            "real-world people by themselves."
        ),
        rx.text(
            "Backend fields are rendered only when available; "
            "otherwise manual review is recommended."
        ),
        rx.cond(TraceReportState.has_degraded_data, rx.text("This panel may be incomplete.")),
        title="Counterparty lens",
    )
