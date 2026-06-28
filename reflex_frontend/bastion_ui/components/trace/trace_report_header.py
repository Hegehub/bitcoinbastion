from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_report_header() -> rx.Component:
    return card(
        rx.text("Report id: ", TraceReportState.trace_report_id),
        rx.text("Status: ", TraceReportState.report_status_label),
        rx.text("Generated: ", TraceReportState.generated_at_label),
        rx.hstack(
            badge("Advisory-only", "info"),
            badge("No custody", "success"),
            badge("Confidence", "warning"),
            rx.text(TraceReportState.confidence_label),
            wrap="wrap",
        ),
        title="Trace report",
        variant="evidence",
    )
