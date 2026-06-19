from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_utxo_hygiene_panel() -> rx.Component:
    return card(
        rx.text(
            "UTXO hygiene indicators, dust exposure, and reuse indicators appear when available."
        ),
        rx.text("This panel is operational context, not financial advice."),
        title="UTXO hygiene",
    )
