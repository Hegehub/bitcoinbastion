from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_state import TraceState


def trace_lite_result_card() -> rx.Component:
    return card(
        rx.text("Address: ", TraceState.normalized_address),
        rx.hstack(
            badge("Advisory status", "info"),
            rx.text(TraceState.risk_band),
            badge("Confidence", "warning"),
            rx.text(TraceState.confidence_label),
            wrap="wrap",
        ),
        rx.text("Providers: ", TraceState.provider_count_label),
        rx.text("Sources: ", TraceState.source_count_label),
        rx.cond(
            TraceState.degraded,
            rx.text("Degraded data: some providers may be unavailable."),
        ),
        rx.text(TraceState.summary),
        rx.text(TraceState.limitations_label),
        rx.text(TraceState.warnings_label),
        rx.cond(
            TraceState.trace_lite_report_id != "",
            rx.text("Full report route coming in next migration step."),
        ),
        title="Trace Lite result",
        variant="evidence",
    )
