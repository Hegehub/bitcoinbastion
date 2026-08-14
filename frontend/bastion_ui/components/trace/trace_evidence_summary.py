from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_evidence_summary() -> rx.Component:
    return card(
        rx.text(TraceReportState.evidence_label),
        rx.text("Evidence may be incomplete, source-dependent, stale, or unavailable."),
        rx.text("Evidence references are pointers only; they do not imply verification."),
        title="Evidence summary",
        variant="evidence",
    )
