from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_state import TraceState


def _result_value(key: str, fallback: str = "Unavailable") -> Any:
    return TraceState.result.get(key, fallback)


def trace_lite_result_card() -> rx.Component:
    return card(
        rx.vstack(
            rx.text("Address: " + TraceState.normalized_address),
            badge("Advisory risk: " + _result_value("risk_band", "unknown"), "info"),
            rx.text("Confidence: " + _result_value("confidence", "unavailable")),
            rx.text("Providers: " + _result_value("provider_count", "unavailable")),
            rx.text("Sources: " + _result_value("source_count", "unavailable")),
            rx.cond(
                TraceState.degraded,
                rx.text("Degraded data: manual review recommended.", color="orange"),
                rx.fragment(),
            ),
            rx.text(_result_value("summary", "Advisory result available.")),
            rx.text(
                "Limitations: " + _result_value("limitations_text", "Manual review recommended.")
            ),
            rx.cond(
                TraceState.latest_report_id != "",
                rx.link("Open full Trace report", href="/trace/" + TraceState.latest_report_id),
                rx.text("Full report link appears when report_id is provided."),
            ),
            align="start",
            spacing="3",
        ),
        title="Trace Lite advisory result",
        variant="evidence",
    )
