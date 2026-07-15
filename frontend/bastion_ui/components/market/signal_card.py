from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def signal_card() -> rx.Component:
    return card(
        rx.text("Signal status: unavailable until backend data is returned."),
        rx.text(
            "Confidence, evidence, timestamp, and operator review status are shown "
            "when present."
        ),
        title="Operator signal",
        subtitle="No trading instruction is provided.",
        variant="console",
    )
