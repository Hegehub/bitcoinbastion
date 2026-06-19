from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_source_disagreement_panel() -> rx.Component:
    return card(
        rx.text(
            "Provider disagreement, missing provider data, and stale source warnings appear here."
        ),
        rx.text("Disagreement must be considered before any operational decision."),
        title="Source disagreement",
    )
