from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_confidence_panel() -> rx.Component:
    return card(
        rx.text("Confidence is not certainty and is not a legal conclusion."),
        rx.text(
            "Confidence depends on available providers, source quality, and evidence freshness."
        ),
        rx.text("Provider disagreement, stale data, or limited evidence can reduce confidence."),
        title="Confidence and uncertainty",
        variant="safety",
    )
