from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_lite_result_card(summary: dict[str, Any] | None = None) -> rx.Component:
    return card(
        rx.text("Report ID: available when returned by the backend."),
        rx.text("Advisory summary: unavailable until backend data is returned."),
        rx.text("Confidence: unavailable until backend data is returned."),
        rx.text("Limitations: Trace output is advisory-only and may be incomplete."),
        rx.link("Open Trace reports", href="/trace"),
        title="Trace Lite Result",
    )
