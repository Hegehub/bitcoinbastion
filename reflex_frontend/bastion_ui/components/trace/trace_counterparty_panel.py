from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_counterparty_panel() -> rx.Component:
    return card(
        rx.text(
            "Counterparty lens data and relationship hints appear when backend "
            "evidence supports them."
        ),
        rx.text("Real-world identity should not be inferred without explicit evidence."),
        title="Counterparty lens",
    )
