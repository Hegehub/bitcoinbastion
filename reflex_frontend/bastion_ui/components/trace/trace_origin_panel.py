from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_origin_panel() -> rx.Component:
    return card(
        rx.text("Observed origin signals appear here when available."),
        rx.text("Interpretation remains evidence-limited and confidence-limited."),
        title="Origin signals",
    )
