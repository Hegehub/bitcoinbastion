from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_evidence_summary() -> rx.Component:
    return card(
        rx.text(TraceReportState.evidence_label),
        rx.text("Evidence may be incomplete, source-dependent, stale, or unavailable."),
        rx.link(
            "Open proof packet", href="/trace/" + TraceReportState.trace_report_id + "/proof-packet"
        ),
        title="Evidence summary",
        variant="evidence",
    )
