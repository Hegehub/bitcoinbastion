from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def time_machine_timeline() -> rx.Component:
    return card(
        rx.text("Structured timeline renders backend events when available."),
        rx.text(
            "Timestamp, event type, title, severity, source, and evidence links "
            "are normalized."
        ),
        rx.text("Empty backend responses show an explicit unavailable state."),
        title="Timeline of market events",
        variant="console",
    )
