from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState


def trace_confidence_panel() -> rx.Component:
    return card(
        rx.text("Backend confidence: ", TraceReportState.confidence_label),
        rx.text("Source quality: ", TraceReportState.source_quality_label),
        rx.text("Freshness: ", TraceReportState.freshness_label),
        rx.text("Confidence is not certainty and is not a legal conclusion."),
        rx.text(
            "Confidence depends on available providers, source quality, and evidence freshness."
        ),
        rx.text("Provider disagreement, stale data, or limited evidence can reduce confidence."),
        title="Confidence and uncertainty",
        variant="safety",
    )
