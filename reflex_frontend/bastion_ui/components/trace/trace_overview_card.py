from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_overview_card() -> rx.Component:
    return card(
        rx.text("Address/entity: Not available until backend report data loads."),
        rx.text("Advisory band: Not available."),
        rx.text("Confidence: Not available."),
        rx.text("Source count: Not available."),
        title="Overview",
        subtitle="Missing fields stay explicit; the UI does not invent values.",
    )
