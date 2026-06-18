from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def limitations_card() -> rx.Component:
    return card(
        rx.text("Limited evidence and provider disagreement must remain visible."),
        rx.text("Manual review recommended."),
        title="Limitations",
        variant="safety",
    )
