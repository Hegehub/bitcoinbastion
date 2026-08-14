from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_overview_card() -> rx.Component:
    return card(
        rx.text("Report id: ", TraceReportState.trace_report_id),
        rx.text("Analyzed subject: ", TraceReportState.subject_label),
        rx.text("Network: ", TraceReportState.chain_label),
        rx.text("Summary: ", TraceReportState.summary_label),
        rx.text("Advisory band: ", TraceReportState.advisory_band_label),
        rx.text("Confidence: ", TraceReportState.confidence_label),
        rx.text("Score: ", TraceReportState.trace_score_label),
        rx.text("Last updated: ", TraceReportState.generated_at_label),
        title="Overview",
    )
